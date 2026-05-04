<template>
  <div class="upload-framework upload-framework-container">
    <!-- Policy Creation Header -->
    <div class="policy-creation-header">
      <div class="policy-intro">
        <div class="policy-intro-header">
          <button 
            v-if="currentStep > 1 && !isProcessing" 
            @click="goBack" 
            class="back-icon-btn" 
            aria-label="Back"
          >
            <i class="fas fa-arrow-left"></i>
          </button>
          <h2>Upload Framework</h2>
        </div>
        <p>Upload framework documents to the system for policy creation and compliance management.</p>
      </div>
    </div>

    <!-- Step Indicator -->
    <div class="step-indicator">
      <div class="step-item" :class="{ active: currentStep === 1, completed: currentStep > 1 }">
        <div class="step-number icon-container">
          <i class="fas fa-upload icon-md"></i>
        </div>
        <div class="step-label">Upload Document</div>
      </div>
      <div class="step-divider"></div>
      <div class="step-item" :class="{ active: currentStep === 2, completed: currentStep > 2 }">
        <div class="step-number icon-container">
          <i class="fas fa-cog icon-md" :class="{ 'fa-spin': currentStep === 2 && isProcessing }"></i>
        </div>
        <div class="step-label">Processing</div>
      </div>
      <div class="step-divider"></div>
      <div class="step-item" :class="{ active: currentStep === 3, completed: currentStep > 3 }">
        <div class="step-number icon-container">
          <i class="fas fa-list icon-md"></i>
        </div>
        <div class="step-label">Content Selection</div>
      </div>
      <div class="step-divider"></div>
      <div class="step-item" :class="{ active: currentStep === 4, completed: currentStep > 4 }">
        <div class="step-number icon-container">
          <i class="fas fa-shield-alt icon-md"></i>
        </div>
        <div class="step-label">Generate Compliances</div>
      </div>
      <div class="step-divider"></div>
      <div class="step-item" :class="{ active: currentStep === 5, completed: currentStep > 5 }">
        <div class="step-number icon-container">
          <i class="fas fa-eye icon-md"></i>
        </div>
        <div class="step-label">Overview</div>
      </div>
      <div class="step-divider"></div>
      <div class="step-item" :class="{ active: currentStep === 6, completed: currentStep > 6 }">
        <div class="step-number icon-container">
          <i class="fas fa-edit icon-md"></i>
        </div>
        <div class="step-label">Edit Policy Details</div>
      </div>
    </div>

    <div class="header">
      <div class="header-content">
        <div class="header-text">
          <h1>Upload Framework</h1>
          <p>Upload framework documents to the system</p>
        </div>
        <div class="header-actions">
          <!-- Stop Processing Button -->
          <button 
            v-if="isProcessing" 
            @click="stopProcessing" 
            class="stop-processing-btn"
            title="Stop Processing"
          >
            <i class="fas fa-stop"></i>
            Stop
          </button>
        </div>
      </div>
    </div>

    <div class="upload-section">
      <!-- Step 1: Upload header with clear cache -->
      <div v-if="currentStep === 1" class="upload-card-header">
        <h2>Upload Framework Document</h2>
        <button
          type="button"
          class="btn-clear-cache"
          @click="clearCache"
          title="Clear saved processing state"
          aria-label="Clear cache"
        >
          <i class="fas fa-broom"></i>
        </button>
      </div>
      <!-- Step 1: Upload Area -->
      <div v-if="currentStep === 1" class="upload-area" :class="{ 'drag-over': isDragOver }" 
           @drop="handleDrop" 
           @dragover.prevent="isDragOver = true" 
           @dragleave="isDragOver = false"
           @click="triggerFileInput">
        <div class="upload-content">
          <h3>Drag & Drop your framework file here</h3>
          <p>or click to browse files</p>
          <div class="supported-formats">
            <small>Supported formats: PDF, DOC, DOCX, TXT, XLS, XLSX</small>
          </div>
        </div>
        <input 
          ref="fileInput" 
          type="file" 
          @change="handleFileSelect" 
          accept=".pdf,.doc,.docx,.txt,.xls,.xlsx"
          style="display: none"
        />
      </div>



      <!-- File Preview (Step 1) -->
      <div v-if="selectedFile && currentStep === 1" class="file-preview">
        <div class="file-info">
          <div class="file-icon-container">
            <i class="fas fa-file file-icon"></i>
          </div>
          <div class="file-details">
            <h4>{{ selectedFile.name }}</h4>
            <p>{{ formatFileSize(selectedFile.size) }}</p>
          </div>
          <button @click="removeFile" class="remove-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="upload-actions">
          <button 
            @click="uploadFile" 
            :disabled="!selectedFile || isUploading"
            class="btn-upload-document"
          >
            <i class="fas fa-upload"></i>
            {{ isUploading ? 'Uploading...' : 'Upload Framework' }}
          </button>
        </div>
      </div>

      <!-- OR Divider -->
      <div v-if="currentStep === 1" class="or-divider">
        <div class="divider-line"></div>
        <span class="divider-text">OR</span>
        <div class="divider-line"></div>
      </div>

      <!-- Load Default Data Section -->
      <div v-if="currentStep === 1" class="default-data-section">
        <div class="default-data-content">
          <h3>Load Default RBI Framework Data</h3>
          <p>Use pre-loaded RBI Master Direction - NBFC framework data from TEMP_MEDIA_ROOT folder for quick testing</p>
          <button 
            @click="loadDefaultData" 
            :disabled="isLoadingDefault"
            class="btn btn-load-default"
          >
            <i class="fas fa-download"></i>
            {{ isLoadingDefault ? 'Loading RBI Data...' : 'Load RBI Data' }}
          </button>
        </div>
      </div>

      <!-- Step 2: Enhanced Processing Progress Section -->
      <div v-if="currentStep === 2" class="processing-section">
        <div class="processing-header">
          <div class="processing-animation-container">
            <div class="document-processing-visual">
              <div class="document-icon">
                <i class="fas fa-file-pdf"></i>
              </div>
              <div class="processing-waves">
                <div class="wave wave-1"></div>
                <div class="wave wave-2"></div>
                <div class="wave wave-3"></div>
              </div>
              <div class="extraction-particles">
                <div class="particle" v-for="n in 6" :key="n"></div>
              </div>
            </div>
          </div>
          <h3>Processing Framework Document</h3>
          
          <!-- Enhanced Processing Details -->
          <div class="processing-details-enhanced">
            <p class="main-status">{{ processingStatus.message || 'Extracting document sections...' }}</p>
            
            <div class="document-info">
              <i class="fas fa-file-alt"></i>
              <span>Analyzing: {{ uploadedFileName }}</span>
            </div>
            
            <!-- Enhanced Current Section Being Processed -->
            <div v-if="processingStatus.currentSection" class="current-section">
              <div class="section-indicator">
                <i class="fas fa-cog fa-spin"></i>
                <span>Processing: {{ processingStatus.currentSection }}</span>
              </div>
            </div>
            
            <!-- Enhanced Processing Stages -->
            <div class="processing-stages">
              <div class="stage" :class="{ active: processingStatus.progress >= 15 }">
                <div class="stage-dot"></div>
                <span>Document Analysis</span>
              </div>
              <div class="stage" :class="{ active: processingStatus.progress >= 30 }">
                <div class="stage-dot"></div>
                <span>Text Extraction</span>
              </div>
              <div class="stage" :class="{ active: processingStatus.progress >= 45 }">
                <div class="stage-dot"></div>
                <span>Structure Processing</span>
              </div>
              <div class="stage" :class="{ active: processingStatus.progress >= 60 }">
                <div class="stage-dot"></div>
                <span>Content Organization</span>
              </div>
              <div class="stage" :class="{ active: processingStatus.progress >= 75 }">
                <div class="stage-dot"></div>
                <span>Policy Identification</span>
              </div>
              <div class="stage" :class="{ active: processingStatus.progress >= 90 }">
                <div class="stage-dot"></div>
                <span>Final Processing</span>
              </div>
            </div>
            
            <!-- Enhanced Processing Activity Indicator -->
            <div class="processing-activity">
              <div class="activity-dots">
                <div class="dot" v-for="n in 3" :key="n"></div>
              </div>
              <span>Processing framework sections</span>
            </div>
            
            <!-- Time Information -->
            <div v-if="processingStatus.elapsedTime" class="time-info">
              <div class="time-display">
                <i class="fas fa-clock"></i>
                <span>Elapsed Time: {{ formatTime(processingStatus.elapsedTime) }}</span>
              </div>
              <div class="time-estimate">
                <i class="fas fa-hourglass-half"></i>
                <span>Estimated Completion: {{ getEstimatedCompletion(processingStatus.progress, processingStatus.elapsedTime) }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Enhanced Progress Container -->
        <div class="progress-container">
          <div class="progress-header">
            <div class="progress-label">Extraction Progress</div>
            <div class="progress-percentage">{{ processingStatus.progress || 0 }}%</div>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: processingStatus.progress + '%' }"></div>
            <div class="progress-glow"></div>
          </div>
          <div class="progress-stats">
            <div class="stat-item">
              <i class="fas fa-file-pdf"></i>
              <span>File: {{ uploadedFileName }}</span>
            </div>
            <div class="stat-item">
              <i class="fas fa-clock"></i>
              <span>Started: {{ processingStartTime }}</span>
            </div>
            <div v-if="processingStatus.elapsedTime" class="stat-item">
              <i class="fas fa-stopwatch"></i>
              <span>Duration: {{ formatTime(processingStatus.elapsedTime) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 3: Content Selection -->
      <div v-if="currentStep === 3" class="content-viewer-section">
        <div class="content-viewer-header">
          <h3>Framework Content Viewer</h3>
          <div class="content-viewer-actions">
            <button @click="selectAllSections" class="btn btn-select-all">Select All</button>
            <button @click="deselectAllSections" class="btn btn-deselect-all">Deselect All</button>
            <button @click="saveSelectedSections" class="btn btn-submit">Save Selection</button>
            <button @click="saveSelectedSections" class="btn btn-continue">
              <i class="fas fa-arrow-right"></i>
              Continue
            </button>
          </div>
        </div>
        
        <div class="content-viewer-body">
          <div class="content-instructions">
            <p><i class="fas fa-info-circle"></i> <strong>Selection Guide:</strong> 
              • Select entire sections to include all policies and subpolicies
              • Select individual policies to include all their subpolicies  
              • Select specific subpolicies for granular control
              • Click the red PDF icon to view PDFs inline
            </p>
            <p><i class="fas fa-arrow-right"></i> <strong>Continue:</strong> Click "Continue" to save your selections to checked_section.json and proceed to the next step.</p>
          </div>
          <div class="search-bar">
            <i class="fas fa-search search-bar__icon"></i>
            <input type="text" v-model="searchQuery" placeholder="Search sections..." class="search-bar__input" />
          </div>
          
          <!-- Additional Dropdown for View Options -->
          <div class="view-options-wrapper">
            <div class="dropdown-field">
              <label class="dropdown-external-label">View Mode:</label>
              <CustomDropdown
                v-model="viewMode"
                :options="viewModeOptions"
                :showLabel="false"
                :showSearchBar="false"
                placeholder="Select View Mode"
                @change="onViewModeChange"
              />
            </div>
            <div class="dropdown-field">
              <label class="dropdown-external-label">Filter by Type:</label>
              <CustomDropdown
                v-model="filterType"
                :options="filterTypeOptions"
                :showLabel="false"
                :showSearchBar="false"
                placeholder="Select Filter Type"
                @change="onFilterTypeChange"
              />
            </div>
          </div>
          
          <div class="section-list">
            <div v-for="(section, index) in filteredSections" :key="index" class="section-item">
              <div class="section-header" @click="toggleSection(section.id)">
                <div class="section-checkbox">
                  <input type="checkbox" v-model="section.selected" @change="updateSelection(section)" />
                  <span class="section-title">{{ section.title }}</span>
                  <span class="subsection-count">({{ section.total_policies || section.subsections.length }} policies, {{ section.total_subpolicies || 0 }} subpolicies)</span>
                  <span v-if="!section.expanded" class="expand-hint">Click to expand and view PDF controls</span>
                </div>
                <i class="fas" :class="section.expanded ? 'fa-chevron-down' : 'fa-chevron-right'"></i>
              </div>
              <div v-if="section.expanded" class="section-content">
                <div v-for="(subsection, subIndex) in section.subsections" :key="subIndex" class="subsection-item">
                  <div class="subsection-header" @click="toggleSubsection(subsection.id)">
                    <div class="subsection-checkbox">
                      <input type="checkbox" v-model="subsection.selected" @change="updateSubsectionSelection(section)" @click.stop />
                      <span class="subsection-title">{{ subsection.title }}</span>
                      <span v-if="subsection.id" class="control-id">({{ subsection.id }})</span>
                      <span v-if="subsection.subpolicies && subsection.subpolicies.length > 0" class="subpolicy-count">({{ subsection.subpolicies.length }} subpolicies)</span>
                    </div>
                    <div class="subsection-actions">
                      <button 
                        v-if="subsection.ai_analysis"
                        @click.stop="subsection.showAiAnalysis = !subsection.showAiAnalysis"
                        class="ai-analysis-toggle-btn"
                        :title="subsection.showAiAnalysis ? 'Hide AI analysis' : 'Show why AI extracted this policy'"
                      >
                        <i class="fas fa-microscope"></i>
                        <span>AI</span>
                      </button>
                      <button 
                        v-if="subsection.control_id"
                        @click="togglePDFView(section.folder, subsection.control_id, subIndex)" 
                        class="pdf-view-btn"
                        :class="{ 'active': subsection.showPDF }"
                        :title="`${subsection.showPDF ? 'Hide' : 'Show'} PDF for ${subsection.title} (${subsection.control_id})`"
                        @click.stop
                      >
                        <i :class="subsection.showPDF ? 'fas fa-eye-slash' : 'fas fa-file-pdf'"></i>
                        <span v-if="subsection.showPDF" class="pdf-status">Active</span>
                      </button>
                      <i v-if="subsection.subpolicies && subsection.subpolicies.length > 0" class="fas subsection-arrow" :class="subsection.expanded ? 'fa-chevron-down' : 'fa-chevron-right'"></i>
                    </div>
                  </div>
                  <!-- Policy-level AI analysis (expandable) -->
                  <div v-if="subsection.showAiAnalysis && subsection.ai_analysis" class="upload-ai-analysis-block policy-ai-analysis">
                    <div class="upload-ai-analysis-header"><i class="fas fa-robot"></i> How & why this policy was selected</div>
                    <div v-if="subsection.ai_analysis.extraction_rationale" class="upload-ai-analysis-row">
                      <span class="upload-ai-analysis-label">Why selected:</span>
                      <p class="upload-ai-analysis-text">{{ subsection.ai_analysis.extraction_rationale }}</p>
                    </div>
                    <div v-if="subsection.ai_analysis.source_excerpt" class="upload-ai-analysis-row">
                      <span class="upload-ai-analysis-label">How selected / source:</span>
                      <p class="upload-ai-analysis-excerpt">{{ subsection.ai_analysis.source_excerpt }}</p>
                    </div>
                  </div>
                  
                  <!-- Subpolicies (nested under policies) - Always visible when expanded -->
                  <div v-if="subsection.expanded && subsection.subpolicies && subsection.subpolicies.length > 0" class="subpolicy-content">
                    <div v-for="(subpolicy, subpolicyIndex) in subsection.subpolicies" :key="subpolicyIndex" class="subpolicy-item">
                      <div class="subpolicy-header">
                        <div class="subpolicy-checkbox">
                          <input type="checkbox" v-model="subpolicy.selected" @change="updateSubpolicySelection(section, subsection)" />
                          <span class="subpolicy-title">{{ subpolicy.title }}</span>
                          <span v-if="subpolicy.id" class="subpolicy-id">({{ subpolicy.id }})</span>
                          <span v-if="subpolicy.control" class="subpolicy-control-hint">Has Control</span>
                        </div>
                        <div class="subpolicy-actions">
                          <button 
                            v-if="subpolicy.ai_analysis"
                            @click.stop="subpolicy.showAiAnalysis = !subpolicy.showAiAnalysis"
                            class="ai-analysis-toggle-btn small"
                            :title="subpolicy.showAiAnalysis ? 'Hide AI justification' : 'Show AI justification for this subpolicy'"
                          >
                            <i class="fas fa-microscope"></i>
                            <span>AI</span>
                          </button>
                          <button 
                            v-if="subpolicy.control_id"
                            @click="togglePDFView(section.folder, subpolicy.control_id, subIndex)" 
                            class="pdf-view-btn small"
                            :class="{ 'active': subpolicy.showPDF }"
                            :title="`${subpolicy.showPDF ? 'Hide' : 'Show'} PDF for ${subpolicy.title} (${subpolicy.control_id})`"
                          >
                            <i :class="subpolicy.showPDF ? 'fas fa-eye-slash' : 'fas fa-file-pdf'"></i>
                          </button>
                          <button 
                            @click="toggleSubpolicyDetails(subpolicy)" 
                            class="details-btn small"
                            :title="`${subpolicy.showDetails ? 'Hide' : 'Show'} details for ${subpolicy.title}`"
                          >
                            <i :class="subpolicy.showDetails ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
                          </button>
                        </div>
                      </div>
                      <!-- Subpolicy AI justification: how & why selected -->
                      <div v-if="(subpolicy.showAiAnalysis || subpolicy.showDetails) && subpolicy.ai_analysis" class="upload-ai-analysis-block subpolicy-ai-analysis">
                        <div class="upload-ai-analysis-header"><i class="fas fa-robot"></i> How & why this subpolicy was selected</div>
                        <div v-if="subpolicy.ai_analysis.extraction_rationale" class="upload-ai-analysis-row">
                          <span class="upload-ai-analysis-label">Why selected:</span>
                          <p class="upload-ai-analysis-text">{{ subpolicy.ai_analysis.extraction_rationale }}</p>
                        </div>
                        <div v-if="subpolicy.ai_analysis.source_excerpt" class="upload-ai-analysis-row">
                          <span class="upload-ai-analysis-label">How selected / source:</span>
                          <p class="upload-ai-analysis-excerpt">{{ subpolicy.ai_analysis.source_excerpt }}</p>
                        </div>
                      </div>
                      <!-- Subpolicy Details - Always visible when showDetails is true -->
                      <div v-if="subpolicy.showDetails" class="subpolicy-details">
                        <div v-if="subpolicy.description" class="subpolicy-description">
                          <strong>Description:</strong> {{ subpolicy.description }}
                        </div>
                        <div v-if="subpolicy.control" class="subpolicy-control">
                          <strong>Control:</strong> {{ subpolicy.control }}
                        </div>
                        <div v-if="subpolicy.content" class="subpolicy-content-text">
                          <strong>Content:</strong> {{ subpolicy.content }}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-if="subsection.content" class="subsection-content">
                    {{ subsection.content }}
                  </div>
                  <!-- Inline PDF Viewer -->
                  <div v-if="subsection.showPDF" class="pdf-viewer-container" :key="`pdf-${section.folder}-${subsection.control_id}`">
                    <div class="pdf-viewer-header">
                      <span class="pdf-title">{{ subsection.title }} - PDF Document</span>
                      <button @click="closePDFView(section.folder, subsection.control_id)" class="close-pdf-btn">
                        <i class="fas fa-times"></i>
                      </button>
                    </div>
                    <div class="pdf-viewer-body">
                      <div v-if="subsection.pdfError" class="pdf-error">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>PDF file not found. Trying alternative paths...</p>
                        <button @click="retryPDFLoad(section.folder, subsection.control_id)" class="retry-btn">
                          <i class="fas fa-refresh"></i>
                          Retry
                        </button>
                      </div>
                      <iframe 
                        v-else
                        :src="getPDFUrl(section.folder, subsection.control_id)" 
                        :key="`iframe-${section.folder}-${subsection.control_id}`"
                        class="pdf-iframe"
                        frameborder="0"
                        @load="onPDFLoad(section.folder, subsection.control_id)"
                        @error="onPDFError(section.folder, subsection.control_id)"
                      ></iframe>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 4: Generate Compliances -->
      <div v-if="currentStep === 4" class="extraction-section">
        <div class="extraction-header">
          <div class="ai-extraction-container">
            <div class="ai-brain-visual">
              <div class="brain-core">
                <i class="fas fa-shield-alt"></i>
              </div>
              <div class="neural-network">
                <div class="neuron" v-for="n in 8" :key="n"></div>
              </div>
              <div class="data-flow">
                <div class="data-bit" v-for="n in 12" :key="n"></div>
              </div>
            </div>
          </div>
          <h3>AI Compliance Generation</h3>
          <div class="ai-processing-details">
            <p class="main-status">{{ complianceGenerationMessage }}</p>
            <div class="ai-stages">
              <div class="ai-stage" :class="{ active: complianceGenerationProgress >= 25 }">
                <div class="ai-stage-icon">
                  <i class="fas fa-file-alt"></i>
                </div>
                <span>Reading Subpolicies</span>
              </div>
              <div class="ai-stage" :class="{ active: complianceGenerationProgress >= 50 }">
                <div class="ai-stage-icon">
                  <i class="fas fa-robot"></i>
                </div>
                <span>AI Analysis</span>
              </div>
              <div class="ai-stage" :class="{ active: complianceGenerationProgress >= 75 }">
                <div class="ai-stage-icon">
                  <i class="fas fa-shield-alt"></i>
                </div>
                <span>Generating Compliances</span>
              </div>
              <div class="ai-stage" :class="{ active: complianceGenerationProgress >= 100 }">
                <div class="ai-stage-icon">
                  <i class="fas fa-check-circle"></i>
                </div>
                <span>Complete</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: complianceGenerationProgress + '%' }"></div>
          </div>
          <div class="progress-text">{{ complianceGenerationProgress || 0 }}%</div>
        </div>
        
        <div class="extraction-details">
          <div class="detail-item">
            <i class="fas fa-file-alt"></i>
            <span>Processing subpolicies from checked_section.json...</span>
          </div>
          <div class="detail-item">
            <i class="fas fa-robot"></i>
            <span>AI is generating compliance records for each subpolicy...</span>
          </div>
          <div v-if="complianceStats.total_subpolicies > 0" class="detail-item">
            <i class="fas fa-chart-line"></i>
            <span>Processed {{ complianceStats.processed_subpolicies }} of {{ complianceStats.total_subpolicies }} subpolicies</span>
          </div>
          <div v-if="complianceStats.total_compliances > 0" class="detail-item">
            <i class="fas fa-check-double"></i>
            <span>Generated {{ complianceStats.total_compliances }} compliance records so far</span>
          </div>
        </div>
        
        <!-- Retry button for errors -->
        <div v-if="complianceGenerationMessage.includes('Error')" class="retry-container">
          <button @click="generateCompliancesForCheckedSections" class="retry-btn">
            <i class="fas fa-redo"></i>
            Retry Generation
          </button>
        </div>
      </div>

      <!-- Step 5: Overview -->
      <div v-if="currentStep === 5" class="policy-review-section overview-section">
        <div class="review-header">
          <div class="review-icon-container">
            <div class="success-circle">
              <i class="fas fa-check-double"></i>
            </div>
          </div>
          <h3>Compliance Generation Complete!</h3>
          <p>Overview of generated compliances for all selected subpolicies.</p>
        </div>
        
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-card-icon">
              <i class="fas fa-sitemap"></i>
            </div>
            <div class="kpi-card-body">
              <span class="kpi-card-value">{{ overviewStats.total_sections || 0 }}</span>
              <span class="kpi-card-title">Sections Selected</span>
            </div>
          </div>
          <div class="kpi-card">
            <div class="kpi-card-icon">
              <i class="fas fa-file-alt"></i>
            </div>
            <div class="kpi-card-body">
              <span class="kpi-card-value">{{ overviewStats.total_policies || 0 }}</span>
              <span class="kpi-card-title">Policies Selected</span>
            </div>
          </div>
          <div class="kpi-card">
            <div class="kpi-card-icon">
              <i class="fas fa-list-alt"></i>
            </div>
            <div class="kpi-card-body">
              <span class="kpi-card-value">{{ overviewStats.total_subpolicies || 0 }}</span>
              <span class="kpi-card-title">Subpolicies Processed</span>
            </div>
          </div>
          <div class="kpi-card">
            <div class="kpi-card-icon kpi-icon-approved">
              <i class="fas fa-shield-alt"></i>
            </div>
            <div class="kpi-card-body">
              <span class="kpi-card-value">{{ overviewStats.total_compliances || 0 }}</span>
              <span class="kpi-card-title">Compliances Generated</span>
            </div>
          </div>
        </div>
        
        <div class="overview-details">
          <div class="detail-card">
            <h4><i class="fas fa-info-circle"></i> Summary</h4>
            <p>Successfully generated {{ overviewStats.total_compliances || 0 }} compliance records from {{ overviewStats.total_subpolicies || 0 }} subpolicies across {{ overviewStats.total_policies || 0 }} policies in {{ overviewStats.total_sections || 0 }} sections.</p>
            <p class="timestamp"><i class="fas fa-clock"></i> Generated at: {{ overviewStats.timestamp || 'N/A' }}</p>
          </div>
        </div>
        
        <div class="review-actions">
          <button @click="goToStep(6)" class="btn-edit-review">
            <i class="fas fa-edit"></i>
            Edit Policy Details
          </button>
        </div>
      </div>

      <!-- Step 6: Edit Policy Details & Save to Database -->
      <div v-if="currentStep === 6" class="policy-details-section">
        <div class="details-header">
          <h3>📝 Edit Framework, Policies, Subpolicies & Compliances</h3>
          <p>Review and edit all extracted data before saving to the database</p>
        </div>
        
        <!-- Loading State -->
        <div v-if="!checkedSectionsData" class="policy-mod-sk" aria-busy="true" aria-label="Loading extracted data">
          <div class="policy-mod-sk__hero"></div>
          <div class="policy-mod-sk__table">
            <div v-for="n in 10" :key="'uf-sk-' + n" class="policy-mod-sk__row"></div>
          </div>
        </div>
        
        <!-- Main Content - Vertical Layout -->
        <div v-else class="vertical-edit-container">
          
          <!-- 1. Framework Section (form.css) -->
          <div class="global-form-box">
            <h3 class="global-form-section-title">Framework Details</h3>
            <div class="global-form-section">
              <div class="global-form-row">
                <div class="global-form-group">
                  <label class="global-form-label">Framework Name <span class="global-form-label-required">*</span></label>
                  <input v-model="frameworkForm.FrameworkName" type="text" class="global-form-input" required />
                </div>
                <div class="global-form-group">
                  <label class="global-form-label">Version</label>
                  <input v-model="frameworkForm.CurrentVersion" type="text" class="global-form-input" />
                </div>
              </div>
              <div class="global-form-row">
                <div class="global-form-group global-form-group-full-width">
                  <label class="global-form-label">Description</label>
                  <textarea v-model="frameworkForm.FrameworkDescription" rows="3" class="global-form-textarea"></textarea>
                </div>
              </div>
              <div class="global-form-row">
                <div class="global-form-group">
                  <label class="global-form-label">Category</label>
                  <input v-model="frameworkForm.Category" type="text" class="global-form-input" />
                </div>
                <div class="global-form-group">
                  <label class="global-form-label">Identifier</label>
                  <input v-model="frameworkForm.Identifier" type="text" class="global-form-input" />
                </div>
              </div>
              <div class="global-form-row">
                <div class="global-form-group">
                  <label class="global-form-label">Status</label>
                  <select v-model="frameworkForm.Status" class="global-form-select">
                    <option value="Under Review">Under Review</option>
                    <option value="Approved">Approved</option>
                    <option value="Rejected">Rejected</option>
                  </select>
                </div>
                <div class="global-form-group">
                  <label class="global-form-label">Reviewer</label>
                  <input v-model="frameworkForm.Reviewer" type="text" class="global-form-input" />
                </div>
              </div>
            </div>
          </div>

          <!-- 2. Sections, Policies, Subpolicies, Compliances -->
          <div v-for="(section, sectionIndex) in checkedSectionsData.sections" 
               :key="`section-${sectionIndex}`">
            
            <!-- Section Header -->
            <div class="section-divider-vertical">
              <h3><i class="fas fa-folder-open"></i> Section: {{ section.section_title }}</h3>
              </div>
            
            <!-- Policies in this Section -->
            <div v-for="(policy, policyIndex) in section.policies" 
                 :key="`policy-${sectionIndex}-${policyIndex}`">
              
              <!-- Policy Level -->
              <div class="level-section policy-level">
                <div class="level-header">
                  <h4><i class="fas fa-file-alt"></i> Policy: {{ policy.policy_title }}</h4>
                  <span class="v-badge">{{ policy.policy_id }}</span>
                  <button 
                    v-if="policy.ai_analysis" 
                    @click="policy.showAiAnalysis = !policy.showAiAnalysis" 
                    class="ai-analysis-toggle-btn step6"
                    :title="policy.showAiAnalysis ? 'Hide AI analysis' : 'Show why AI extracted this policy'"
                  >
                    <i class="fas fa-microscope"></i> AI
                  </button>
                </div>
                <!-- Policy AI analysis (Step 6) -->
                <div v-if="policy.showAiAnalysis && policy.ai_analysis" class="upload-ai-analysis-block policy-ai-analysis">
                  <div class="upload-ai-analysis-header"><i class="fas fa-robot"></i> How & why this policy was selected</div>
                  <div v-if="policy.ai_analysis.extraction_rationale" class="upload-ai-analysis-row">
                    <span class="upload-ai-analysis-label">Why selected:</span>
                    <p class="upload-ai-analysis-text">{{ policy.ai_analysis.extraction_rationale }}</p>
                  </div>
                  <div v-if="policy.ai_analysis.source_excerpt" class="upload-ai-analysis-row">
                    <span class="upload-ai-analysis-label">How selected / source:</span>
                    <p class="upload-ai-analysis-excerpt">{{ policy.ai_analysis.source_excerpt }}</p>
                  </div>
                </div>
                <div class="global-form-section">
                  <div class="global-form-row">
                    <div class="global-form-group">
                      <label class="global-form-label">Policy Title <span class="global-form-label-required">*</span></label>
                      <input v-model="policy.policy_title" type="text" class="global-form-input" required />
                    </div>
                    <div class="global-form-group">
                      <label class="global-form-label">Policy Type</label>
                      <input v-model="policy.policy_type" type="text" class="global-form-input" />
                    </div>
                  </div>
                  <div class="global-form-row">
                    <div class="global-form-group global-form-group-full-width">
                      <label class="global-form-label">Description</label>
                      <textarea v-model="policy.policy_description" rows="3" class="global-form-textarea"></textarea>
                    </div>
                  </div>
                  <div class="global-form-row">
                    <div class="global-form-group">
                      <label class="global-form-label">Category</label>
                      <input v-model="policy.policy_category" type="text" class="global-form-input" />
                    </div>
                    <div class="global-form-group">
                      <label class="global-form-label">Subcategory</label>
                      <input v-model="policy.policy_subcategory" type="text" class="global-form-input" />
                    </div>
                  </div>
                  <div class="global-form-row">
                    <div class="global-form-group global-form-group-full-width">
                      <label class="global-form-label">Scope</label>
                      <textarea v-model="policy.scope" rows="2" class="global-form-textarea"></textarea>
                    </div>
                  </div>
                  <div class="global-form-row">
                    <div class="global-form-group global-form-group-full-width">
                      <label class="global-form-label">Objective</label>
                      <textarea v-model="policy.objective" rows="2" class="global-form-textarea"></textarea>
                    </div>
                  </div>
                </div>
            </div>

              <!-- Subpolicies for this Policy -->
              <div v-for="(subpolicy, subpolicyIndex) in policy.subpolicies" 
                   :key="`subpolicy-${sectionIndex}-${policyIndex}-${subpolicyIndex}`">
                
                <!-- Subpolicy Level -->
                <div class="level-section subpolicy-level">
                  <div class="level-header">
                    <h5><i class="fas fa-file-contract"></i> Subpolicy: {{ subpolicy.subpolicy_title }}</h5>
                    <span class="v-badge v-badge-small">{{ subpolicy.subpolicy_id }}</span>
                    <button 
                      v-if="subpolicy.ai_analysis" 
                      @click="subpolicy.showAiAnalysis = !subpolicy.showAiAnalysis" 
                      class="ai-analysis-toggle-btn step6 small"
                      :title="subpolicy.showAiAnalysis ? 'Hide AI analysis' : 'Show why AI extracted this subpolicy'"
                    >
                      <i class="fas fa-microscope"></i> AI
                    </button>
                  </div>
                  <!-- Subpolicy AI analysis (Step 6) -->
                  <div v-if="subpolicy.showAiAnalysis && subpolicy.ai_analysis" class="upload-ai-analysis-block subpolicy-ai-analysis">
                    <div class="upload-ai-analysis-header"><i class="fas fa-robot"></i> How & why this subpolicy was selected</div>
                    <div v-if="subpolicy.ai_analysis.extraction_rationale" class="upload-ai-analysis-row">
                      <span class="upload-ai-analysis-label">Why selected:</span>
                      <p class="upload-ai-analysis-text">{{ subpolicy.ai_analysis.extraction_rationale }}</p>
                    </div>
                    <div v-if="subpolicy.ai_analysis.source_excerpt" class="upload-ai-analysis-row">
                      <span class="upload-ai-analysis-label">How selected / source:</span>
                      <p class="upload-ai-analysis-excerpt">{{ subpolicy.ai_analysis.source_excerpt }}</p>
                    </div>
                  </div>
                  <div class="global-form-section">
                    <div class="global-form-row">
                      <div class="global-form-group">
                        <label class="global-form-label">Subpolicy Title <span class="global-form-label-required">*</span></label>
                        <input v-model="subpolicy.subpolicy_title" type="text" class="global-form-input" required />
                      </div>
                      <div class="global-form-group">
                        <label class="global-form-label">Description</label>
                        <textarea v-model="subpolicy.subpolicy_description" rows="2" class="global-form-textarea"></textarea>
                      </div>
                    </div>
                    <div class="global-form-row">
                      <div class="global-form-group global-form-group-full-width">
                        <label class="global-form-label">Control</label>
                        <textarea v-model="subpolicy.control" rows="3" class="global-form-textarea"></textarea>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Compliances for this Subpolicy -->
                <div v-for="(compliance, complianceIndex) in getCompliancesForSubpolicy(subpolicy.subpolicy_id)" 
                     :key="`compliance-${sectionIndex}-${policyIndex}-${subpolicyIndex}-${complianceIndex}`">
                  
                  <!-- Compliance Level -->
                  <div class="level-section compliance-level">
                    <div class="level-header">
                      <h6><i class="fas fa-shield-alt"></i> Compliance {{ complianceIndex + 1 }}</h6>
                      <span class="v-badge v-criticality-badge" :class="'v-' + compliance.Criticality?.toLowerCase()">
                        {{ compliance.Criticality }}
                    </span>
                  </div>
                    <div class="global-form-section">
                      <div class="global-form-row">
                        <div class="global-form-group">
                          <label class="global-form-label">Compliance Title <span class="global-form-label-required">*</span></label>
                          <input v-model="compliance.ComplianceTitle" type="text" class="global-form-input" required />
                        </div>
                        <div class="global-form-group">
                          <label class="global-form-label">Type</label>
                          <select v-model="compliance.ComplianceType" class="global-form-select">
                            <option value="Regulatory">Regulatory</option>
                            <option value="Internal">Internal</option>
                            <option value="Industry Standard">Industry Standard</option>
                            <option value="Legal">Legal</option>
                            <option value="Operational">Operational</option>
                          </select>
                        </div>
                      </div>
                      <div class="global-form-row">
                        <div class="global-form-group global-form-group-full-width">
                          <label class="global-form-label">Description</label>
                          <textarea v-model="compliance.ComplianceItemDescription" rows="3" class="global-form-textarea"></textarea>
                        </div>
                      </div>
                      <div class="global-form-row">
                        <div class="global-form-group">
                          <label class="global-form-label">Criticality</label>
                          <select v-model="compliance.Criticality" class="global-form-select">
                            <option value="Low">Low</option>
                            <option value="Medium">Medium</option>
                            <option value="High">High</option>
                            <option value="Critical">Critical</option>
                          </select>
                        </div>
                        <div class="global-form-group">
                          <label class="global-form-label">Mandatory/Optional</label>
                          <select v-model="compliance.MandatoryOptional" class="global-form-select">
                            <option value="Mandatory">Mandatory</option>
                            <option value="Optional">Optional</option>
                          </select>
                        </div>
                      </div>
                      <div class="global-form-row">
                        <div class="global-form-group">
                          <label class="global-form-label">Maturity Level</label>
                          <select v-model="compliance.MaturityLevel" class="global-form-select">
                            <option value="Initial">Initial</option>
                            <option value="Developing">Developing</option>
                            <option value="Defined">Defined</option>
                            <option value="Managed">Managed</option>
                            <option value="Optimizing">Optimizing</option>
                          </select>
                        </div>
                        <div class="global-form-group">
                          <label class="global-form-label">Risk Category</label>
                          <input v-model="compliance.RiskCategory" type="text" class="global-form-input" />
                        </div>
                      </div>
                      <div class="global-form-row">
                        <div class="global-form-group global-form-group-full-width">
                          <label class="global-form-label">Possible Damage</label>
                          <textarea v-model="compliance.PossibleDamage" rows="2" class="global-form-textarea"></textarea>
                        </div>
                      </div>
                    </div>
                  </div>
          
                </div>
                
                <!-- No Compliances Message -->
                <div v-if="getCompliancesForSubpolicy(subpolicy.subpolicy_id).length === 0" class="no-compliances-vertical">
                  <p><i class="fas fa-info-circle"></i> No compliances generated for this subpolicy</p>
                </div>
                
              </div>
            </div>
          </div>
          
          <!-- Save Button (uses .btn-submit from main.css) -->
          <div class="save-actions">
            <button @click="saveToDatabase" class="btn-submit" :disabled="isSavingToDatabase">
              <i :class="isSavingToDatabase ? 'fas fa-spinner fa-spin' : 'fas fa-database'"></i>
              {{ isSavingToDatabase ? 'Saving to Database...' : 'Save to Database' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Upload Status Messages -->
      <div v-if="uploadStatus && currentStep === 1" class="status-message" :class="uploadStatus.type">
        <i :class="uploadStatus.type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
        {{ uploadStatus.message }}
      </div>
      
      <!-- Congratulations Modal -->
      <div v-if="showCongratulationsModal" class="congratulations-modal">
        <div class="congratulations-container">
          <div class="congratulations-header">
            <div class="congratulations-icon-container">
              <i class="fas fa-check-circle"></i>
            </div>
            <h2>Congratulations!</h2>
            <p class="congratulations-message">Your framework has been successfully added to the system.</p>
          </div>
          <div class="congratulations-content">
            <p>You have completed all the steps to add a new framework to your GRC system.</p>
            <p>Your framework is now ready to be used for compliance management.</p>
          </div>
          <div class="congratulations-actions">
            <button @click="goToPolicyDashboard" class="ok-btn">
              <i class="fas fa-check"></i>
              Go to Policy Dashboard
            </button>
          </div>
        </div>
      </div>
      
      <!-- Global Success Notification -->
      <div v-if="uploadStatus && uploadStatus.type === 'success' && currentStep > 1" class="global-notification success">
        <div class="notification-content">
          <i class="fas fa-check-circle"></i>
          <div class="notification-message">
            {{ uploadStatus.message }}
          </div>
          <button @click="uploadStatus = null" class="notification-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
      
      <!-- Content Viewer Modal -->
      <div v-if="showContentViewer" class="content-viewer-modal">
        <div class="content-viewer-container">
          <div class="content-viewer-header">
            <h3>Framework Content Viewer</h3>
            <button @click="closeContentViewer" class="close-btn">
              <i class="fas fa-times"></i>
            </button>
          </div>
          
          <div class="content-viewer-body">
            <div class="search-bar">
              <i class="fas fa-search search-bar__icon"></i>
              <input type="text" v-model="searchQuery" placeholder="Search sections..." class="search-bar__input" />
            </div>
            
            <div class="section-list">
              <div v-for="(section, index) in filteredSections" :key="index" class="section-item">
                <div class="section-header" @click="toggleSection(section.id)">
                  <div class="section-checkbox">
                    <input type="checkbox" v-model="section.selected" @change="updateSelection(section)" />
                    <span>{{ section.title }}</span>
                  </div>
                  <i class="fas" :class="section.expanded ? 'fa-chevron-down' : 'fa-chevron-right'"></i>
                </div>
                <div v-if="section.expanded" class="section-content">
                  <div v-for="(subsection, subIndex) in section.subsections" :key="subIndex" class="subsection-item">
                    <div class="subsection-header">
                      <div class="subsection-checkbox">
                        <input type="checkbox" v-model="subsection.selected" @change="updateSubsectionSelection(section)" />
                        <span class="subsection-title">{{ subsection.title }}</span>
                        <span v-if="subsection.control_id" class="control-id">({{ subsection.control_id }})</span>
                      </div>
                      <div class="subsection-actions">
                        <button 
                          @click="togglePDFView(section.folder, subsection.control_id, subIndex)" 
                          class="pdf-view-btn"
                          :class="{ 'active': subsection.showPDF }"
                          :title="`${subsection.showPDF ? 'Hide' : 'Show'} PDF for ${subsection.title}`"
                        >
                          <i :class="subsection.showPDF ? 'fas fa-eye-slash' : 'fas fa-file-pdf'"></i>
                        </button>
                      </div>
                    </div>
                    <div v-if="subsection.content" class="subsection-content">
                      {{ subsection.content }}
                    </div>
                    <!-- Inline PDF Viewer -->
                    <div v-if="subsection.showPDF" class="pdf-viewer-container">
                      <div class="pdf-viewer-header">
                        <span class="pdf-title">{{ subsection.title }} - PDF Document</span>
                        <button @click="closePDFView(subIndex)" class="close-pdf-btn">
                          <i class="fas fa-times"></i>
                        </button>
                      </div>
                      <div class="pdf-viewer-body">
                        <iframe 
                          :src="getPDFUrl(section.folder, subsection.control_id)" 
                          class="pdf-iframe"
                          frameborder="0"
                        ></iframe>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="content-viewer-footer">
            <button @click="selectAllSections" class="btn btn-select-all">Select All</button>
            <button @click="deselectAllSections" class="btn btn-deselect-all">Deselect All</button>
            <button @click="saveSelectedSections" class="btn btn-submit">Save Selection</button>
          </div>
        </div>
      </div>

      <!-- Policy Extractor View -->
      <div v-if="showPolicyExtractor" class="policy-extractor-modal">
        <div class="policy-extractor-container">
          <div class="policy-extractor-header">
            <h3>Extracted Policies</h3>
            <div class="policy-actions">
              <button @click="saveAllPolicies" class="save-all-btn">
                <i class="fas fa-save"></i>
                Save All
              </button>
              <button @click="closePolicyExtractor" class="close-btn">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
          
          <div class="policy-extractor-body">
            <div class="policy-table-container">
              <table class="policy-table" v-if="policies.length > 0">
                <thead>
                  <tr>
                    <th>Section</th>
                    <th>Control ID</th>
                    <th>Policy Name</th>
                    <th>Control</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <template v-for="(policy, index) in policies" :key="index">
                    <tr :class="{ 'expanded-row': expandedRows[index] }">
                      <td>{{ policy.section_name || 'N/A' }}</td>
                      <td>{{ policy.Sub_policy_id || 'N/A' }}</td>
                      <td>{{ policy.sub_policy_name || 'N/A' }}</td>
                      <td class="control-cell">
                        {{ policy.control ? (policy.control.length > 100 ? policy.control.substring(0, 100) + '...' : policy.control) : 'N/A' }}
                      </td>
                      <td class="actions-cell">
                        <button @click="toggleExpandRow(index)" class="view-btn">
                          <i :class="expandedRows[index] ? 'fas fa-chevron-up' : 'fas fa-eye'"></i>
                          {{ expandedRows[index] ? 'Hide' : 'View' }}
                        </button>
                        <button @click="editPolicy(policy, index)" class="edit-btn">
                          <i class="fas fa-edit"></i>
                          Edit
                        </button>
                      </td>
                    </tr>
                    <tr v-if="expandedRows[index]" class="detail-row">
                      <td colspan="5">
                        <div class="policy-details-container">
                          <div class="policy-details-section">
                            <h4>Control ID</h4>
                            <div class="detail-content">{{ policy.Sub_policy_id || 'N/A' }}</div>
                          </div>
                          
                          <div class="policy-details-section">
                            <h4>Policy Name</h4>
                            <div class="detail-content">{{ policy.sub_policy_name || 'N/A' }}</div>
                          </div>
                          
                          <div class="policy-details-section">
                            <h4>Control</h4>
                            <div class="detail-content control-content">
                              <div v-if="getFormattedControl(policy.control).length > 0">
                                <ul>
                                  <li v-for="(point, idx) in getFormattedControl(policy.control)" :key="idx">
                                    {{ point }}
                                  </li>
                                </ul>
                              </div>
                              <div v-else>{{ policy.control || 'N/A' }}</div>
                            </div>
                          </div>
                          
                          <div class="policy-details-section">
                            <h4>Related Controls</h4>
                            <div class="detail-content">{{ policy.related_controls || 'N/A' }}</div>
                          </div>
                          
                          <div class="policy-details-section">
                            <h4>Control Enhancements</h4>
                            <div class="detail-content">{{ policy.control_enhancements || 'N/A' }}</div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  </template>
                </tbody>
              </table>
              <div v-else class="no-policies-message">
                <p>No policies found. Please try processing the document again.</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Policy Edit Modal -->
      <div v-if="showPolicyDetail" class="policy-edit-modal">
        <div class="policy-edit-container">
          <div class="policy-edit-header">
            <h3>Edit Policy</h3>
            <div class="policy-edit-actions">
              <button @click="savePolicy" class="save-btn">
                <i class="fas fa-save"></i>
                Save
              </button>
              <button @click="closePolicyDetail" class="close-btn">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
          
          <div class="policy-edit-body">
            <div class="policy-field">
              <label>Section</label>
              <input type="text" v-model="currentPolicy.section_name" />
            </div>
            
            <div class="policy-field">
              <label>Control ID</label>
              <input type="text" v-model="currentPolicy.Sub_policy_id" />
            </div>
            
            <div class="policy-field">
              <label>Policy Name</label>
              <input type="text" v-model="currentPolicy.sub_policy_name" />
            </div>
            
            <div class="policy-field">
              <label>Control</label>
              <textarea v-model="currentPolicy.control" rows="8"></textarea>
            </div>
            
            <div class="policy-field">
              <label>Related Controls</label>
              <input type="text" v-model="currentPolicy.related_controls" />
            </div>
            
            <div class="policy-field">
              <label>Control Enhancements</label>
              <textarea v-model="currentPolicy.control_enhancements" rows="5"></textarea>
            </div>
            </div>
          </div>
        </div>
      </div>
    </div>

</template>

<script>
import { ref, computed, onUnmounted, watch, onMounted, getCurrentInstance } from 'vue'
import { useRouter } from 'vue-router'
import apiService from '@/services/apiService.js'
import eventBus, { LOGOUT_EVENT } from '../../utils/eventBus.js'
import { API_ENDPOINTS, API_BASE_URL } from '@/config/api.js'
import { compressFile, shouldCompressFile } from '@/utils/fileCompression.js'
import CustomDropdown from '../CustomDropdown.vue'
// AI Centralized Module Optimizations
import moduleAiAnalysisService from '@/services/moduleAiAnalysisService'
import policyFrameworkCacheService from '@/services/policyFrameworkCacheService'

export default {
  name: 'UploadFramework',
  components: {
    CustomDropdown
  },
  setup() {
    const router = useRouter()
    
    // Use router to prevent ESLint warning
    const navigateTo = (path) => {
      router.push(path)
    }
    
    // Basic reactive data
    const selectedFile = ref(null)
          const isDragOver = ref(false)
      const isUploading = ref(false)
      const isLoadingDefault = ref(false)
      const currentFrameworkKey = ref('dgca_framework') // Hardcoded to DGCA

    const isProcessing = ref(false)
    const processingComplete = ref(false)
    const uploadStatus = ref(null)
    const fileInput = ref(null)
    const processingStatus = ref({ progress: 0, message: '' })
    const taskId = ref(null)
    const uploadedFileName = ref('')
    const processingStartTime = ref('')
    let progressInterval = null
    let statusInterval = null
    
    // Step management
    const currentStep = ref(1)
    const stepHistory = ref([1])
    
    // Content viewer related
    const showContentViewer = ref(false)
    const sections = ref([])
    const searchQuery = ref('')
    
    // New view mode and filter options
    const viewMode = ref('collapsed')
    const filterType = ref('all')
    
    // Dropdown options
    const viewModeOptions = ref([
      { label: 'Collapsed View', value: 'collapsed' },
      { label: 'Expanded View', value: 'expanded' },
      { label: 'Sub-policies Only', value: 'subpolicies-only' },
      { label: 'All Expanded', value: 'all-expanded' }
    ])
    
    const filterTypeOptions = ref([
      { label: 'All Types', value: 'all' },
      { label: 'Policies Only', value: 'policies' },
      { label: 'Sub-policies Only', value: 'subpolicies' },
      { label: 'Controls Only', value: 'controls' }
    ])
    
    // Policy extraction progress
    const policyExtractionComplete = ref(false)
    const policyExtractionInProgress = ref(false)
    const policyExtractionMessage = ref('')
    const policyExtractionProgress = ref(0)
    
    // Compliance generation state
    const complianceGenerationMessage = ref('')
    const complianceGenerationProgress = ref(0)
    const complianceStats = ref({
      total_subpolicies: 0,
      processed_subpolicies: 0,
      total_compliances: 0
    })
    
    // Overview stats
    const overviewStats = ref({
      total_sections: 0,
      total_policies: 0,
      total_subpolicies: 0,
      total_compliances: 0,
      timestamp: ''
    })
    
    // Step 6 - Edit Form Data
    const checkedSectionsData = ref(null)
    const frameworkForm = ref({
      FrameworkName: '',
      FrameworkDescription: '',
      CurrentVersion: '1.0',
      Category: '',
      Identifier: '',
      Status: 'Under Review',
      ActiveInactive: 'Active',
      Reviewer: '',
      InternalExternal: 'Internal',
      EffectiveDate: null,
      StartDate: null,
      EndDate: null,
      CreatedByName: 'Admin'
    })
    const isSavingToDatabase = ref(false)

    // Policy extractor related
    const showPolicyExtractor = ref(false)
    const policies = ref([])
    const extractedPoliciesCount = ref(0)
    const selectedSectionsCount = ref(0)
    
    // Policy detail view related
    const showPolicyDetail = ref(false)
    const currentPolicy = ref({})
    const currentPolicyIndex = ref(null)
    const isEditing = ref(false)
    
    // For expandable rows
    const expandedRows = ref({})
    
    // Policy details for Step 6
    const policyDetails = ref({
      title: '',
      description: '',
      category: '',
      effectiveDate: '',
      startDate: '',
      endDate: ''
    })
    
    // Dynamic forms data
    const policyFormData = ref({})
    // SECURITY: prevent prototype pollution via externally-controlled object keys.
    const unsafeObjectKeys = new Set(['__proto__', 'prototype', 'constructor'])
    const sanitizeObjectKey = (key) => {
      const k = String(key ?? '').trim()
      if (!k) return '_empty_key'
      if (unsafeObjectKeys.has(k) || k.startsWith('__')) {
        return `safe_${k.replace(/[^\w.-]/g, '_')}`
      }
      return k
    }
    
    // Compliance data
    const complianceData = ref({})
    
    // Congratulations modal
    const showCongratulationsModal = ref(false)

    // Persistent state management
    const PERSISTENT_STATE_KEY = 'upload_framework_processing_state'
    const STATE_RESTORED_FLAG = 'upload_framework_state_restored'
    
    // Save processing state to sessionStorage
    const saveProcessingState = () => {
      // Save state even if not actively processing (for steps after processing completes)
      
      const state = {
        isProcessing: isProcessing.value,
        currentStep: currentStep.value,
        taskId: taskId.value,
        processingStatus: processingStatus.value,
        uploadedFileName: uploadedFileName.value,
        processingStartTime: processingStartTime.value,
        sections: sections.value,
        complianceGenerationProgress: complianceGenerationProgress.value,
        complianceGenerationMessage: complianceGenerationMessage.value,
        overviewStats: overviewStats.value,
        checkedSectionsData: checkedSectionsData.value,
        frameworkForm: frameworkForm.value,
        timestamp: Date.now()
      }
      
      try {
        sessionStorage.setItem(PERSISTENT_STATE_KEY, JSON.stringify(state))
        console.log('💾 Processing state saved:', state)
      } catch (error) {
        console.error('❌ Failed to save processing state:', error)
      }
    }
    
    // Load processing state from sessionStorage
    const loadProcessingState = () => {
      try {
        const savedState = sessionStorage.getItem(PERSISTENT_STATE_KEY)
        if (!savedState) {
          console.log('❌ No saved state found')
          return false
        }
        
        const state = JSON.parse(savedState)
        
        // Check if state is not too old (24 hours max)
        const maxAge = 24 * 60 * 60 * 1000 // 24 hours in milliseconds
        if (Date.now() - state.timestamp > maxAge) {
          console.log('❌ Saved state is too old, clearing')
          sessionStorage.removeItem(PERSISTENT_STATE_KEY)
          return false
        }
        
        // Restore state
        isProcessing.value = state.isProcessing || false
        currentStep.value = state.currentStep || 1
        taskId.value = state.taskId || null
        processingStatus.value = state.processingStatus || { progress: 0, message: '' }
        uploadedFileName.value = state.uploadedFileName || ''
        processingStartTime.value = state.processingStartTime || ''
        sections.value = state.sections || []
        complianceGenerationProgress.value = state.complianceGenerationProgress || 0
        complianceGenerationMessage.value = state.complianceGenerationMessage || ''
        overviewStats.value = state.overviewStats || {
          total_sections: 0,
          total_policies: 0,
          total_subpolicies: 0,
          total_compliances: 0,
          timestamp: ''
        }
        checkedSectionsData.value = state.checkedSectionsData || null
        frameworkForm.value = state.frameworkForm || {
          FrameworkName: '',
          FrameworkDescription: '',
          CurrentVersion: '1.0',
          Category: '',
          Identifier: '',
          Status: 'Under Review',
          ActiveInactive: 'Active',
          Reviewer: '',
          InternalExternal: 'Internal',
          EffectiveDate: null,
          StartDate: null,
          EndDate: null,
          CreatedByName: 'Admin'
        }
        
        console.log('✅ Processing state restored:', state)
        return true
      } catch (error) {
        console.error('❌ Failed to load processing state:', error)
        sessionStorage.removeItem(PERSISTENT_STATE_KEY)
        return false
      }
    }
    
    // Clear processing state from sessionStorage
    const clearProcessingState = () => {
      try {
        sessionStorage.removeItem(PERSISTENT_STATE_KEY)
        sessionStorage.removeItem(STATE_RESTORED_FLAG)
        console.log('🗑️ Processing state cleared')
      } catch (error) {
        console.error('❌ Failed to clear processing state:', error)
      }
    }
    
    // Stop processing function
    const stopProcessing = () => {
      console.log('🛑 Stopping processing...')
      
      // Clear intervals
      if (progressInterval) {
        clearInterval(progressInterval)
        progressInterval = null
      }
      if (statusInterval) {
        clearInterval(statusInterval)
        statusInterval = null
      }
      
      // Reset processing state
      isProcessing.value = false
      processingComplete.value = false
      processingStatus.value = { progress: 0, message: 'Processing stopped by user' }
      
      // Clear persistent state
      clearProcessingState()
      
      // Reset to step 1
      currentStep.value = 1
      
      // Show notification
      uploadStatus.value = {
        type: 'info',
        message: 'Processing stopped by user'
      }
      
      setTimeout(() => {
        uploadStatus.value = null
      }, 3000)
    }
    
    // Resume processing if needed
    const resumeProcessingIfNeeded = () => {
      if (isProcessing.value && taskId.value) {
        console.log('🔄 Resuming processing with task ID:', taskId.value)
        startProgressTracking(taskId.value)
      } else if (currentStep.value === 4 && complianceGenerationProgress.value > 0 && complianceGenerationProgress.value < 100) {
        console.log('🔄 Resuming compliance generation from', complianceGenerationProgress.value + '%')
        // If we're on step 4 and compliance generation was in progress, continue from where we left off
        // The backend should handle the continuation
        generateCompliancesForCheckedSections()
      } else if (currentStep.value === 6 && !checkedSectionsData.value) {
        console.log('🔄 Resuming step 6 - loading checked sections data')
        // If we're on step 6 but data is not loaded, load it
        loadCheckedSectionsData()
      }
    }

    // Natural sorting function for proper numerical ordering
    const naturalSort = (a, b) => {
      const aParts = a.match(/(\d+|\D+)/g) || []
      const bParts = b.match(/(\d+|\D+)/g) || []
      
      for (let i = 0; i < Math.min(aParts.length, bParts.length); i++) {
        const aPart = aParts[i]
        const bPart = bParts[i]
        
        if (/\d/.test(aPart) && /\d/.test(bPart)) {
          const aNum = parseInt(aPart, 10)
          const bNum = parseInt(bPart, 10)
          if (aNum !== bNum) return aNum - bNum
        } else {
          if (aPart !== bPart) return aPart.localeCompare(bPart)
        }
      }
      
      return aParts.length - bParts.length
    }

    // Computed properties
    const filteredSections = computed(() => {
      let filtered = sections.value
      
      // Apply search filter
      if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
        filtered = sections.value
        .filter(section => 
          section.title.toLowerCase().includes(query) ||
            section.subsections.some(sub => 
              sub.title.toLowerCase().includes(query) ||
              (sub.subpolicies && sub.subpolicies.some(sp => 
                sp.title.toLowerCase().includes(query) ||
                (sp.description && sp.description.toLowerCase().includes(query))
              ))
            )
        )
        .map(section => ({
          ...section,
          subsections: section.subsections
              .filter(sub => 
                sub.title.toLowerCase().includes(query) ||
                (sub.subpolicies && sub.subpolicies.some(sp => 
                  sp.title.toLowerCase().includes(query) ||
                  (sp.description && sp.description.toLowerCase().includes(query))
                ))
              )
              .map(sub => ({
                ...sub,
                subpolicies: sub.subpolicies ? sub.subpolicies.filter(sp => 
                  sp.title.toLowerCase().includes(query) ||
                  (sp.description && sp.description.toLowerCase().includes(query))
                ) : []
              }))
          }))
      }
      
      // Apply type filter
      if (filterType.value !== 'all') {
        filtered = filtered.map(section => ({
          ...section,
          subsections: section.subsections.filter(sub => {
            switch (filterType.value) {
              case 'policies':
                return sub.subpolicies && sub.subpolicies.length === 0
              case 'subpolicies':
                return sub.subpolicies && sub.subpolicies.length > 0
              case 'controls':
                return sub.control_id || (sub.subpolicies && sub.subpolicies.some(sp => sp.control_id))
              default:
                return true
            }
          })
        })).filter(section => section.subsections.length > 0)
      }
      
      // Sort sections and subsections naturally
      return filtered.map(section => ({
        ...section,
        subsections: [...section.subsections].sort((a, b) => naturalSort(a.title, b.title))
      })).sort((a, b) => naturalSort(a.title, b.title))
    })

    const uniqueSectionNames = computed(() => {
      if (!policies.value || policies.value.length === 0) return []
      const sections = [...new Set(
        policies.value
          .map(p => sanitizeObjectKey(p.policy_name))
          .filter(name => name)
      )]
      return sections.sort()
    })

    // Computed properties for filtered arrays to avoid v-for with v-if
    const validPolicies = computed(() => {
      if (!policies.value || policies.value.length === 0) return []
      return policies.value.filter(policy => policy && policy.policy_name)
    })

    const getValidSubPolicies = (policy) => {
      if (!policy || !policy.sub_policies || !Array.isArray(policy.sub_policies)) return []
      return policy.sub_policies.filter(subPolicy => subPolicy && subPolicy.id)
    }

    const getValidRelatedControls = (subPolicy) => {
      if (!subPolicy || !subPolicy.related_controls || !Array.isArray(subPolicy.related_controls)) return []
      return subPolicy.related_controls.filter(control => control)
    }

    const getValidSubSections = (subPolicy) => {
      if (!subPolicy || !subPolicy.sub_sections || typeof subPolicy.sub_sections !== 'object') return []
      return Object.entries(subPolicy.sub_sections).filter(([, sectionData]) => sectionData)
    }

    // Ensure form data is always properly initialized
    const ensureFormData = (policyName) => {
      const safePolicyName = sanitizeObjectKey(policyName)
      if (!policyFormData.value[safePolicyName]) {
        policyFormData.value[safePolicyName] = {
          documentUrl: '',
          identifier: '',
          createdBy: '',
          reviewer: '',
          policyName: policyName,
          department: '',
          scope: '',
          applicability: '',
          objective: '',
          coverageRate: 0
        }
      }
      return policyFormData.value[safePolicyName]
    }

    const ensureSubPolicyFormData = (policyName, subPolicyId) => {
      const safePolicyName = sanitizeObjectKey(policyName)
      const safeSubPolicyId = sanitizeObjectKey(subPolicyId)
      const key = `${safePolicyName}_${safeSubPolicyId}`
      if (!policyFormData.value[key]) {
        policyFormData.value[key] = {
          documentUrl: '',
          identifier: subPolicyId,
          createdBy: '',
          reviewer: '',
          policyName: subPolicyId,
          department: '',
          scope: '',
          applicability: '',
          objective: '',
          coverageRate: 0,
          complianceInfo: {}
        }
      }
      return policyFormData.value[key]
    }

    const ensureComplianceInfo = (policyName, subPolicyId, sectionKey) => {
      const formData = ensureSubPolicyFormData(policyName, subPolicyId)
      const safeSectionKey = sanitizeObjectKey(sectionKey)
      if (!formData.complianceInfo[safeSectionKey]) {
        formData.complianceInfo[safeSectionKey] = {
          section: sectionKey,
          text: '',
          order: 0
        }
      }
      return formData.complianceInfo[safeSectionKey]
    }



    // File handling methods
    const triggerFileInput = () => {
      fileInput.value.click()
    }

    const handleFileSelect = (event) => {
      const file = event.target.files[0]
      if (file) {
        selectedFile.value = file
        uploadStatus.value = null
      }
    }

    const handleDrop = (event) => {
      event.preventDefault()
      isDragOver.value = false
      const file = event.dataTransfer.files[0]
      if (file) {
        selectedFile.value = file
        uploadStatus.value = null
      }
    }

    const removeFile = () => {
      selectedFile.value = null
      uploadStatus.value = null
      fileInput.value.value = ''
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    // Enhanced time formatting function
    const formatTime = (seconds) => {
      if (seconds < 60) {
        return `${seconds}s`
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60)
        const remainingSeconds = seconds % 60
        return `${minutes}m ${remainingSeconds}s`
      } else {
        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        const remainingSeconds = seconds % 60
        return `${hours}h ${minutes}m ${remainingSeconds}s`
      }
    }

    // Estimated completion time calculation
    const getEstimatedCompletion = (progress, elapsedTime) => {
      if (progress <= 0 || elapsedTime <= 0) return 'Calculating...'
      
      const totalEstimatedTime = (elapsedTime / progress) * 100
      const remainingTime = totalEstimatedTime - elapsedTime
      
      if (remainingTime <= 0) return 'Completing...'
      
      return formatTime(Math.floor(remainingTime))
    }

    // Upload and processing methods
    const uploadFile = async () => {
      if (!selectedFile.value) return

      isUploading.value = true
      uploadStatus.value = null

      try {
        // OPTIMIZATION: Check cache first for identical document
        const cached = policyFrameworkCacheService.getCachedDocumentResult(selectedFile.value)
        if (cached) {
          console.log('🎯 Using cached document result for', selectedFile.value.name)
          const cachedResponse = cached.data?.data || cached.data
          uploadedFileName.value = cachedResponse?.filename || cached.fileName || selectedFile.value.name
          processingStartTime.value = new Date().toLocaleTimeString()
          
          if ((cachedResponse?.processing || cached.data?.processing) && cached.taskId) {
            isProcessing.value = true
            taskId.value = cached.taskId
            goToStep(2)
            startProgressTracking(cached.taskId)
            saveProcessingState()
          } else {
            uploadStatus.value = {
              type: 'success',
              message: `File "${uploadedFileName.value}" loaded from cache!`
            }
          }
          return
        }

        let fileToUpload = selectedFile.value
        let compressionMetadata = null

        // Compress file if beneficial
        if (shouldCompressFile(selectedFile.value)) {
          try {
            uploadStatus.value = 'Compressing document...'
            const result = await compressFile(selectedFile.value)
            fileToUpload = result.compressedFile
            compressionMetadata = {
              original_size: result.originalSize,
              compressed_size: result.compressedSize,
              ratio: result.compressionRatio
            }
            console.log(`✅ Compression complete: ${result.compressionRatio}% reduction`)
          } catch (error) {
            console.warn('⚠️ Compression failed, uploading original file:', error)
            // Continue with original file if compression fails
          }
        }

        const formData = new FormData()
        formData.append('file', fileToUpload)
        
        // Include compression metadata if available
        if (compressionMetadata) {
          formData.append('compression_metadata', JSON.stringify(compressionMetadata))
        }
        
        // Add user ID to the request
        const userId = localStorage.getItem('user_id') || 'default'
        formData.append('userid', userId)

        // OPTIMIZATION: Use cached upload with deduplication
        uploadStatus.value = 'Uploading document...'
        const result = await policyFrameworkCacheService.uploadDocument(formData, selectedFile.value)
        const payload = result && result.data && typeof result.data === 'object' ? result.data : null
        const taskIdFromResponse = (result && result.taskId) || (payload && (payload.task_id ?? (payload.data && payload.data.task_id)))
        const isProcessingResponse = payload && (payload.processing === true || (payload.data && payload.data.processing === true))
        const filename = (payload && (payload.filename || (payload.data && payload.data.filename))) || selectedFile.value.name

        uploadedFileName.value = filename
        processingStartTime.value = new Date().toLocaleTimeString()

        if (isProcessingResponse && taskIdFromResponse) {
          isProcessing.value = true
          taskId.value = taskIdFromResponse
          goToStep(2)
          startProgressTracking(taskIdFromResponse)
          saveProcessingState()
        } else if (!isProcessingResponse) {
          uploadStatus.value = {
            type: 'success',
            message: `File "${uploadedFileName.value}" uploaded successfully!`
          }
          setTimeout(() => {
            removeFile()
            uploadStatus.value = null
          }, 3000)
        } else {
          uploadStatus.value = {
            type: 'error',
            message: 'Upload succeeded but task ID was missing. Please clear cache and try again.'
          }
        }

      } catch (error) {
        console.error('❌ Upload failed:', error)
        uploadStatus.value = {
          type: 'error',
          message: error.response?.data?.error || error.message || 'Upload failed. Please try again.'
        }
      } finally {
        isUploading.value = false
      }
    }

    // Progress tracking
    const startProgressTracking = (id, onComplete = null) => {
      isProcessing.value = true
      processingComplete.value = false
      const startTime = Date.now()
      let lastProgress = 0
      let idlePolls = 0
      
      const calculateProgress = () => {
        const elapsedTime = (Date.now() - startTime) / 1000
        const estimatedTotalTime = 120 // 2 minutes
        return Math.min((elapsedTime / estimatedTotalTime) * 100, 99)
      }
      
      const getStatusMessage = (progress) => {
        if (progress < 25) return 'Uploading and analyzing document...'
        if (progress < 50) return 'Extracting sections and subsections...'
        if (progress < 75) return 'Processing content and metadata...'
        if (progress < 100) return 'Finalizing framework structure...'
        return 'Processing complete!'
      }
      
      const getCurrentSection = (progress) => {
        const sections = ['Upload', 'Analysis', 'Extraction', 'Processing', 'Finalization']
        const sectionIndex = Math.floor((progress / 100) * sections.length)
        return sections[Math.min(sectionIndex, sections.length - 1)]
      }
      
      // Poll less frequently to avoid spamming backend (5s) and stop if idle for too long
      progressInterval = setInterval(async () => {
        try {
          // Check if user is still authenticated (rely on flags, not tokens, for cookie-first auth)
          const isAuthenticated = (sessionStorage.getItem('isAuthenticated') || localStorage.getItem('isAuthenticated')) === 'true' || 
                                 (sessionStorage.getItem('is_logged_in') || localStorage.getItem('is_logged_in')) === 'true'
          
          if (!isAuthenticated) {
            console.log('User not authenticated (session flags missing) - stopping progress polling')
            clearInterval(progressInterval)
            return
          }
          
          const data = await apiService.get(API_ENDPOINTS.FRAMEWORK_PROCESSING_STATUS(id))
          
          if (data.progress !== undefined) {
            // Use backend progress if available
            processingStatus.value = {
              ...data,
              message: getStatusMessage(data.progress),
              currentSection: getCurrentSection(data.progress)
            }

            // Track idle polls (no progress change)
            if (data.progress === lastProgress) {
              idlePolls += 1
            } else {
              idlePolls = 0
              lastProgress = data.progress
            }
          } else {
            // Use time-based progress calculation
            const calculatedProgress = calculateProgress()
            const elapsedTime = (Date.now() - startTime) / 1000
            processingStatus.value = {
              progress: calculatedProgress,
              message: getStatusMessage(calculatedProgress),
              currentSection: getCurrentSection(calculatedProgress),
              elapsedTime: Math.floor(elapsedTime)
            }
          }
          
          // Auto-stop if we've polled many times with no change and progress is high
          if (processingStatus.value.progress >= 95 && idlePolls >= 6) {
            console.log('⏱️ Stopping polling after prolonged idle high progress state')
            clearInterval(progressInterval)
            isProcessing.value = false
          }

          if (processingStatus.value.progress >= 100) {
            clearInterval(progressInterval)
            isProcessing.value = false
            processingComplete.value = true
            const result = data?.result
            const isSuccess = result && result.status === 'success'
            const hasNoResult = !result || (!result.status && processingStatus.value.progress >= 100)
            
            if (!isSuccess && result && result.status === 'failed') {
              uploadStatus.value = {
                type: 'error',
                message: result.error || 'Document processing failed. Please try again or use a different file.'
              }
            }
            if (onComplete) {
              onComplete()
            } else if (isSuccess || hasNoResult) {
              // Advance to step 3 if explicitly successful OR if progress is complete but no result status set
              console.log(`🎯 Advancing to step 3: isSuccess=${isSuccess}, hasNoResult=${hasNoResult}, progress=${processingStatus.value.progress}`)
              goToStep(3)
              fetchExtractedContent()
            }
          } else {
            // Save state periodically during processing
            saveProcessingState()
          }
        } catch (error) {
          console.error('Error fetching progress:', error)
          
          // If we get a 401 error, stop polling
          if (error.response && error.response.status === 401) {
            console.log('Unauthorized - stopping progress polling')
            clearInterval(progressInterval)
            return
          }
          
          // Fallback to time-based progress
          const calculatedProgress = calculateProgress()
          const elapsedTime = (Date.now() - startTime) / 1000
          processingStatus.value = {
            progress: calculatedProgress,
            message: getStatusMessage(calculatedProgress),
            currentSection: getCurrentSection(calculatedProgress),
            elapsedTime: Math.floor(elapsedTime)
          }
          
          if (calculatedProgress >= 99) {
            clearInterval(progressInterval)
            isProcessing.value = false
            processingComplete.value = true
            // Time-based fallback: do not auto-advance to step 3; backend progress is source of truth
            if (onComplete) onComplete()
          }
          
          if (error.response?.status === 404) {
            clearInterval(progressInterval)
            isProcessing.value = false
            policyFrameworkCacheService.clearTaskCache(id)
            uploadStatus.value = {
              type: 'error',
              message: 'Processing task not found or expired. Please upload again.'
            }
            currentStep.value = 1
          }
        }
      }, 1500)
    }

    // Step navigation
    const goToStep = (step) => {
      if (step !== currentStep.value) {
        stepHistory.value.push(currentStep.value)
        currentStep.value = step
        
        // Save state when step changes (always, not just when processing)
        saveProcessingState()
      }
    }

    const goBack = () => {
      currentStep.value = Math.max(1, currentStep.value - 1)
      
      // Save state when going back
      saveProcessingState()
    }

    // Content extraction and viewing
    const fetchExtractedContent = async () => {
      try {
        // Get user ID from localStorage or use the task ID as user ID
        const userid = localStorage.getItem('user_id') || '1'
        
        // OPTIMIZATION: Check cache first for sections data
        const cached = policyFrameworkCacheService.getCachedSections(userid, taskId.value)
        if (cached && cached.sections) {
          console.log('🎯 Using cached sections data for user:', userid)
          processSectionsData(cached)
          return
        }
        
        // OPTIMIZATION: Use cached sections fetching with deduplication
        const response = await policyFrameworkCacheService.getSections(userid, taskId.value)
        
        console.log('[DEBUG] API Response:', response)
        
        if (response && response.sections) {
          processSectionsData(response)
        } else {
          sections.value = []
        }
      } catch (error) {
        console.error('❌ Error fetching extracted content:', error)
        sections.value = []
      }
    }
    
    // Helper function to process sections data (extracted for reuse)
    const processSectionsData = (data) => {
      sections.value = data.sections.map((section, index) => {
        // Map policies to subsections (for frontend compatibility)
        const subsections = (section.policies || []).map(policy => {
          // Map subpolicies from the policy
          const subpolicies = (policy.subpolicies || []).map(subpolicy => ({
            id: subpolicy.subpolicy_id,
            title: subpolicy.subpolicy_title || subpolicy.subpolicy_id,
            description: subpolicy.subpolicy_description,
            content: subpolicy.subpolicy_text,
            control: subpolicy.control,
            ai_analysis: subpolicy.ai_analysis || null,
            selected: false,
            expanded: false,
            showPDF: false
          }))
          
          return {
            id: policy.policy_id,
            title: policy.policy_title || policy.policy_id,
            description: policy.policy_description,
            content: policy.policy_text,
            scope: policy.scope,
            objective: policy.objective,
            policy_type: policy.policy_type,
            policy_category: policy.policy_category,
            policy_subcategory: policy.policy_subcategory,
            ai_analysis: policy.ai_analysis || null,
            subpolicies: subpolicies,
            selected: false,
            expanded: false,
            showPDF: false
          }
        })
        
        // Count total subpolicies
        const total_subpolicies = subsections.reduce((sum, sub) => 
          sum + (sub.subpolicies ? sub.subpolicies.length : 0), 0)
        
        return {
          id: index,
          title: section.title,
          folder: section.folder_path || '',
          level: section.level,
          selected: false,
          expanded: false,
          subsections: subsections,
          total_policies: subsections.length,
          total_subpolicies: total_subpolicies,
          content: section.content || ''
        }
      })
      
      console.log('[SUCCESS] Loaded sections with policies and subpolicies:', sections.value)
      
      // OPTIMIZATION: Preload compliance AI analysis (silent if disabled)
      moduleAiAnalysisService.fetchModuleAnalysis('compliance', null).catch(() => {})
      
      // Save state after content is loaded
      saveProcessingState()
    }

          const viewExtractedContent = () => {
        // Fetch content and go to step 3 (inline content, not modal)
        fetchExtractedContent()
        goToStep(3)
      }

      // Load default data function
      const loadDefaultData = async () => {
        // OPTIMIZATION: Load precomputed data with caching and enhanced performance
        isLoadingDefault.value = true
        uploadStatus.value = null

        // Clear any previous processing state so we don't resume old tasks
        if (progressInterval) {
          clearInterval(progressInterval)
          progressInterval = null
        }
        if (statusInterval) {
          clearInterval(statusInterval)
          statusInterval = null
        }
        isProcessing.value = false
        processingComplete.value = false
        processingStatus.value = { progress: 0, message: '' }
        taskId.value = null
        processingStartTime.value = ''
        saveProcessingState()

        try {
          const framework = 'rbi_framework'
          
          // OPTIMIZATION: Check cache first for default data
          const cached = policyFrameworkCacheService.getCachedDefaultData(framework)
          if (cached) {
            console.log('🎯 Using cached default data for framework:', framework)
            processDefaultDataResponse(cached)
            return
          }

          uploadStatus.value = 'Loading framework data from cache or server...'
          
          // OPTIMIZATION: Use cached default data loading with deduplication
          const response = await policyFrameworkCacheService.loadDefaultData(framework)
          
          processDefaultDataResponse(response)

        } catch (error) {
          console.error('❌ Error loading default data:', error)
          uploadStatus.value = {
            type: 'error',
            message: error.response?.data?.error || error.message || 'Failed to load default data. Please try again.'
          }
        } finally {
          isLoadingDefault.value = false
        }
      }
      
      // Helper function to process default data response (extracted for reuse)
      const processDefaultDataResponse = (data) => {
        if (data.success) {
          console.log('📊 Full API Response:', data)
          console.log('📊 Sections received:', data.sections)
          
          // Set the sections data directly from the response using same mapping as fetchExtractedContent
          sections.value = data.sections.map((section, index) => {
            console.log(`Section ${index}: ${section.title} has ${section.policies?.length || 0} policies`)
            
            // Map policies to subsections (for frontend compatibility)
            const subsections = (section.policies || []).map(policy => {
              // Map subpolicies from the policy
              const subpolicies = (policy.subpolicies || []).map(subpolicy => ({
                id: subpolicy.subpolicy_id,
                title: subpolicy.subpolicy_title || subpolicy.subpolicy_id,
                description: subpolicy.subpolicy_description,
                content: subpolicy.subpolicy_text,
                control: subpolicy.control,
                ai_analysis: subpolicy.ai_analysis || null,
                selected: false,
                expanded: false,
                showPDF: false
              }))
              
              return {
                id: policy.policy_id,
                title: policy.policy_title || policy.policy_id,
                description: policy.policy_description,
                content: policy.policy_text,
                scope: policy.scope,
                objective: policy.objective,
                policy_type: policy.policy_type,
                policy_category: policy.policy_category,
                policy_subcategory: policy.policy_subcategory,
                ai_analysis: policy.ai_analysis || null,
                subpolicies: subpolicies,
                selected: false,
                expanded: false,
                showPDF: false
              }
            })
            
            // Count total subpolicies
            const total_subpolicies = subsections.reduce((sum, sub) => 
              sum + (sub.subpolicies ? sub.subpolicies.length : 0), 0)
            
            return {
              id: index,
              title: section.title,
              folder: section.folder_path || section.folder || '',
              level: section.level,
              selected: false,
              expanded: false, // Collapse sections by default
              subsections: subsections,
              total_policies: subsections.length,
              total_subpolicies: total_subpolicies,
              content: section.content || ''
            }
          })
          
          console.log('📊 Mapped sections:', sections.value)
          console.log('📊 Section count:', sections.value.length)
          console.log('📊 Total policies:', sections.value.reduce((sum, s) => sum + s.total_policies, 0))
          console.log('📊 Total subpolicies:', sections.value.reduce((sum, s) => sum + s.total_subpolicies, 0))
          
          // Set task ID for future reference
          taskId.value = data.task_id
          currentFrameworkKey.value = data.framework_key || 'dgca_framework'
          
          // Set uploaded file name to indicate it's default DGCA data from TEMP_MEDIA_ROOT
          uploadedFileName.value = 'DGCA Framework (Default from TEMP_MEDIA_ROOT)'
          
          // OPTIMIZATION: Preload module AI analysis for policy (silent if disabled)
          moduleAiAnalysisService.fetchModuleAnalysis('policy', null).catch(() => {})
          
          // Go directly to step 3 (content selection) – no processing step
          goToStep(3)
          
          // Save state after loading default data
          saveProcessingState()
          
          uploadStatus.value = {
            type: 'success',
            message: `Default DGCA framework data loaded successfully! Found ${data.total_sections} sections.`
          }

          setTimeout(() => {
            uploadStatus.value = null
          }, 3000)
        } else {
          throw new Error(data.error || 'Invalid response from server')
        }
      }
    
    const closeContentViewer = () => {
      showContentViewer.value = false
    }

    // Get PDF URL for inline viewing
    const getPDFUrl = (sectionFolder, controlId) => {
      if (!sectionFolder || !controlId) {
        console.error('Missing section folder or control ID')
        return ''
      }

      // Get the current user ID - try multiple sources
      let currentUserId = '1' // default
      
      if (taskId.value) {
        // Try to extract user ID from task ID
        if (taskId.value.startsWith('default_')) {
          currentUserId = '1' // For default data, use user 1
        } else {
          const parts = taskId.value.split('_')
          if (parts.length > 1) {
            currentUserId = parts[0]
          }
        }
      }
      
      // Check if this is default data from TEMP_MEDIA_ROOT
      if (taskId.value && taskId.value.startsWith('default_')) {
        // Use the default data PDF endpoint with DGCA framework
        const framework = currentFrameworkKey.value || 'dgca_framework'
        const pdfPath = API_ENDPOINTS.AI_DEFAULT_PDF(sectionFolder, controlId, framework)
        console.log('Using default data PDF endpoint:', pdfPath)
        
        // Add timestamp to prevent caching issues
        const timestamp = Date.now()
        const separator = pdfPath.includes('?') ? '&' : '?'
        return `${pdfPath}${separator}t=${timestamp}`
      } else {
        // Use the regular checked sections PDF endpoint
        const pdfPath = API_ENDPOINTS.CHECKED_SECTIONS_PDF(currentUserId, sectionFolder, controlId) + `?task_id=${taskId.value || ''}`
        console.log('Using backend PDF endpoint:', pdfPath)
        
        // Add timestamp to prevent caching issues
        const timestamp = Date.now()
        return `${pdfPath}&t=${timestamp}`
      }
    }

    // Test if PDF file exists
    const testPDFExists = async (sectionFolder, controlId) => {
      const pdfUrl = getPDFUrl(sectionFolder, controlId)
      console.log('Testing PDF existence for:', pdfUrl)
      
      try {
        const response = await fetch(pdfUrl, { method: 'HEAD' })
        if (response.ok) {
          console.log('✅ PDF file exists:', pdfUrl)
        } else {
          console.error('❌ PDF file not found:', pdfUrl, 'Status:', response.status)
          // Try alternative paths
          await tryAlternativePaths(sectionFolder, controlId)
        }
      } catch (error) {
        console.error('❌ Error checking PDF:', error)
        // Try alternative paths
        await tryAlternativePaths(sectionFolder, controlId)
      }
    }

    // Try alternative PDF paths
    const tryAlternativePaths = async (sectionFolder, controlId) => {
      // Check if this is default data from TEMP_MEDIA_ROOT
      const isDefaultData = taskId.value && taskId.value.startsWith('default_')
      const framework = currentFrameworkKey.value || 'dgca_framework'
      
      // Build list of alternative paths based on data source
      let alternativePaths = []
      
      if (isDefaultData) {
        // For default data from TEMP_MEDIA_ROOT
        alternativePaths = [
          API_ENDPOINTS.AI_DEFAULT_PDF(sectionFolder, controlId, framework),
          `${API_BASE_URL}/api/ai-upload/default-pdf/${sectionFolder}/${controlId}/?framework=${framework}`
        ]
      } else {
        // For regular uploaded data
        alternativePaths = [
          // Use only the backend endpoint - media paths require authentication
          API_ENDPOINTS.CHECKED_SECTIONS_PDF('1', sectionFolder, controlId) + `?task_id=${taskId.value || ''}`,
          API_ENDPOINTS.CHECKED_SECTIONS_PDF('1', sectionFolder, controlId) + `?task_id=default_task`,
          API_ENDPOINTS.CHECKED_SECTIONS_PDF('1', sectionFolder, controlId),
          // Fallback to current API base URL
          `${API_BASE_URL}/api/checked-sections/pdf/1/${sectionFolder}/${controlId}/?task_id=${taskId.value || ''}`,
          `${API_BASE_URL}/api/checked-sections/pdf/1/${sectionFolder}/${controlId}/?task_id=default_task`
        ]
      }
      
      console.log('Trying alternative paths for:', { sectionFolder, controlId, isDefaultData, framework })
      
      for (const path of alternativePaths) {
        try {
          const response = await fetch(path, { method: 'HEAD' })
          if (response.ok) {
            console.log('✅ Found PDF at alternative path:', path)
            return path
          }
        } catch (error) {
          console.log('❌ Alternative path failed:', path, error)
        }
      }
      
      console.error('❌ No PDF found in any alternative paths')
    }

    // Handle PDF load success
    const onPDFLoad = (sectionFolder, controlId) => {
      console.log('✅ PDF loaded successfully:', { sectionFolder, controlId })
      
      // Find and update the subsection
      const section = sections.value.find(s => s.folder === sectionFolder)
      if (section && section.subsections) {
        const subsection = section.subsections.find(sub => sub.control_id === controlId)
        if (subsection) {
          subsection.pdfError = false
          console.log('PDF error cleared for:', subsection.title)
        }
      }
    }

    // Handle PDF load error
    const onPDFError = (sectionFolder, controlId) => {
      console.error('❌ PDF failed to load:', { sectionFolder, controlId })
      
      // Find and update the subsection
      const section = sections.value.find(s => s.folder === sectionFolder)
      if (section && section.subsections) {
        const subsection = section.subsections.find(sub => sub.control_id === controlId)
        if (subsection) {
          subsection.pdfError = true
          console.log('PDF error set for:', subsection.title)
        }
      }
    }

          // Retry PDF load
      const retryPDFLoad = async (sectionFolder, controlId) => {
        console.log('Retrying PDF load for:', { sectionFolder, controlId })
        
        // Find and update the subsection
        const section = sections.value.find(s => s.folder === sectionFolder)
        if (section && section.subsections) {
          const subsection = section.subsections.find(sub => sub.control_id === controlId)
          if (subsection) {
            subsection.pdfError = false
            
            // Try to find the correct PDF path
            const correctPath = await tryAlternativePaths(sectionFolder, controlId)
            if (correctPath) {
              // Update the PDF URL with the correct path
              subsection.pdfUrl = correctPath
              console.log('Updated PDF URL to:', correctPath)
            }
          }
        }
      }

      // Get checked sections information
      const getCheckedSectionsInfo = async (userId) => {
        try {
          const data = await apiService.get(`${API_ENDPOINTS.CHECKED_SECTIONS_GET(userId)}?task_id=${taskId.value}`)
          
          if (data && data.success) {
            console.log('Checked sections info:', data.data)
            return data.data
          } else {
            console.error('Failed to get checked sections info:', data.error)
            return null
          }
        } catch (error) {
          console.error('Error getting checked sections info:', error)
          return null
        }
      }

      // Delete checked sections
      const deleteCheckedSections = async (userId) => {
        try {
          const data = await apiService.delete(`${API_ENDPOINTS.CHECKED_SECTIONS_DELETE(userId)}?task_id=${taskId.value}`)
          
          if (data && data.success) {
            console.log('Successfully deleted checked sections')
            return true
          } else {
            console.error('Failed to delete checked sections:', data.error)
            return false
          }
        } catch (error) {
          console.error('Error deleting checked sections:', error)
          return false
        }
    }

    // Toggle PDF view for specific control
    const togglePDFView = (sectionFolder, controlId, subIndex) => {
      console.log('togglePDFView called:', { sectionFolder, controlId, subIndex })
      
      if (!sectionFolder || !controlId) {
        console.error('Missing section folder or control ID')
        return
      }

      // Find the section by folder name
      const section = sections.value.find(s => s.folder === sectionFolder)
      
      if (!section) {
        console.error(`Section with folder ${sectionFolder} not found`)
        return
      }
      
      if (!section.subsections) {
        console.error(`No subsections found in section ${sectionFolder}`)
        return
      }
      
      // Find the specific subsection by control ID to ensure we get the exact one
      const subsection = section.subsections.find(sub => sub.control_id === controlId)
      
      if (!subsection) {
        console.error(`Subsection with control_id ${controlId} not found in section ${sectionFolder}`)
        return
      }
        
        // Ensure showPDF property exists
        if (typeof subsection.showPDF === 'undefined') {
          subsection.showPDF = false
        }
        
      // Toggle the PDF view for this specific subsection
        subsection.showPDF = !subsection.showPDF
      console.log(`Toggled PDF view for ${subsection.title} (${controlId}): ${subsection.showPDF}`)
        
      // Close all other PDFs to ensure only one is open at a time
      if (subsection.showPDF) {
        sections.value.forEach(s => {
          if (s.subsections) {
            s.subsections.forEach(sub => {
              if (sub.control_id !== controlId) {
                sub.showPDF = false
              }
            })
          }
        })
        
        // Test if PDF file exists
        testPDFExists(sectionFolder, controlId)
      }
    }

    // Close PDF view for specific control
    const closePDFView = (sectionFolder, controlId) => {
      console.log('closePDFView called:', { sectionFolder, controlId })
      
      if (!sectionFolder || !controlId) {
        console.error('Missing section folder or control ID')
        return
      }

      // Find the section by folder name
      const section = sections.value.find(s => s.folder === sectionFolder)
      
      if (section && section.subsections) {
        // Find the subsection by control ID
        const subsection = section.subsections.find(sub => sub.control_id === controlId)
        
        if (subsection) {
          subsection.showPDF = false
          console.log(`Closed PDF view for ${subsection.title}`)
      } else {
          console.error(`Subsection with control_id ${controlId} not found in section ${sectionFolder}`)
        }
      } else {
        console.error(`Section with folder ${sectionFolder} not found`)
      }
    }
    
    const toggleSection = (sectionId) => {
      const section = sections.value.find(s => s.id === sectionId)
      if (section) {
        section.expanded = !section.expanded
      }
    }
    
    const toggleSubsection = (subsectionId) => {
      // Find the subsection across all sections
      for (const section of sections.value) {
        const subsection = section.subsections.find(s => s.id === subsectionId)
        if (subsection) {
          subsection.expanded = !subsection.expanded
          break
        }
      }
    }
    
    const toggleSubpolicyDetails = (subpolicy) => {
      subpolicy.showDetails = !subpolicy.showDetails
    }
    
    const onViewModeChange = () => {
      switch (viewMode.value) {
        case 'collapsed':
          // Collapse all sections
          sections.value.forEach(section => {
            section.expanded = false
            section.subsections.forEach(subsection => {
              subsection.expanded = false
              if (subsection.subpolicies) {
                subsection.subpolicies.forEach(subpolicy => {
                  subpolicy.showDetails = false
                })
              }
            })
          })
          break
        case 'expanded':
          // Expand sections but keep subsections collapsed
          sections.value.forEach(section => {
            section.expanded = true
            section.subsections.forEach(subsection => {
              subsection.expanded = false
              if (subsection.subpolicies) {
                subsection.subpolicies.forEach(subpolicy => {
                  subpolicy.showDetails = false
                })
              }
            })
          })
          break
        case 'subpolicies-only':
          // Expand sections and subsections to show subpolicies
          sections.value.forEach(section => {
            section.expanded = true
            section.subsections.forEach(subsection => {
              subsection.expanded = true
              if (subsection.subpolicies) {
                subsection.subpolicies.forEach(subpolicy => {
                  subpolicy.showDetails = true
                })
              }
            })
          })
          break
        case 'all-expanded':
          // Expand everything
          sections.value.forEach(section => {
            section.expanded = true
            section.subsections.forEach(subsection => {
              subsection.expanded = true
              if (subsection.subpolicies) {
                subsection.subpolicies.forEach(subpolicy => {
                  subpolicy.showDetails = true
                })
              }
            })
          })
          break
      }
    }
    
    const onFilterTypeChange = () => {
      // Filter logic will be handled in the computed property
      console.log('Filter type changed to:', filterType.value)
    }
    
    const updateSelection = (section) => {
      section.subsections.forEach(sub => {
        sub.selected = section.selected
        if (sub.subpolicies) {
          sub.subpolicies.forEach(subpolicy => {
            subpolicy.selected = section.selected
          })
        }
      })
    }
    
    const updateSubsectionSelection = (section) => {
      section.selected = section.subsections.every(sub => sub.selected)
    }
    
    const updateSubpolicySelection = (section, subsection) => {
      // Update subsection selection based on subpolicies
      subsection.selected = subsection.subpolicies.every(subpolicy => subpolicy.selected)
      // Update section selection based on all subsections
      section.selected = section.subsections.every(sub => sub.selected)
    }
    
    const selectAllSections = () => {
      sections.value.forEach(section => {
        section.selected = true
        section.subsections.forEach(sub => {
          sub.selected = true
          if (sub.subpolicies) {
            sub.subpolicies.forEach(subpolicy => {
              subpolicy.selected = true
            })
          }
        })
      })
    }
    
    const deselectAllSections = () => {
      sections.value.forEach(section => {
        section.selected = false
        section.subsections.forEach(sub => {
          sub.selected = false
          if (sub.subpolicies) {
            sub.subpolicies.forEach(subpolicy => {
              subpolicy.selected = false
            })
          }
        })
      })
    }
    
    const saveSelectedSections = async () => {
      try {
        // Build hierarchical structure: section -> policy -> subpolicy
        const selectedItems = []
        
        sections.value.forEach(section => {
          // Check if section has any selected items
          const hasSelectedItems = section.selected || 
            section.subsections.some(sub => sub.selected) ||
            section.subsections.some(sub => sub.subpolicies && sub.subpolicies.some(sp => sp.selected))
          
          if (hasSelectedItems) {
            const sectionData = {
              section_name: section.folder || section.title,
              section_title: section.title,
              policies: []
            }
            
            // Process policies (subsections)
            section.subsections.forEach(policy => {
              // Check if policy is selected or has selected subpolicies
              const hasSelectedSubpolicies = policy.selected || 
                (policy.subpolicies && policy.subpolicies.some(sp => sp.selected))
              
              if (hasSelectedSubpolicies) {
                const policyData = {
                  policy_id: policy.id,
                  policy_title: policy.title,
                  policy_description: policy.description || '',
                  policy_text: policy.content || '',
                  scope: policy.scope || '',
                  objective: policy.objective || '',
                  policy_type: policy.policy_type || '',
                  policy_category: policy.policy_category || '',
                  policy_subcategory: policy.policy_subcategory || '',
                  subpolicies: []
                }
                if (policy.ai_analysis) policyData.ai_analysis = policy.ai_analysis
                
                // Process subpolicies
                if (policy.subpolicies) {
                  policy.subpolicies.forEach(subpolicy => {
                    if (subpolicy.selected) {
                      const subpolicyData = {
                        subpolicy_id: subpolicy.id,
                        subpolicy_title: subpolicy.title,
                        subpolicy_description: subpolicy.description || '',
                        subpolicy_text: subpolicy.content || '',
                        control: subpolicy.control || ''
                      }
                      if (subpolicy.ai_analysis) subpolicyData.ai_analysis = subpolicy.ai_analysis
                      policyData.subpolicies.push(subpolicyData)
                    }
                  })
                }
                
                // If entire policy is selected but no specific subpolicies, include all subpolicies
                if (policy.selected && policyData.subpolicies.length === 0 && policy.subpolicies) {
                  policy.subpolicies.forEach(subpolicy => {
                    const subpolicyData = {
                      subpolicy_id: subpolicy.id,
                      subpolicy_title: subpolicy.title,
                      subpolicy_description: subpolicy.description || '',
                      subpolicy_text: subpolicy.content || '',
                      control: subpolicy.control || ''
                    }
                    if (subpolicy.ai_analysis) subpolicyData.ai_analysis = subpolicy.ai_analysis
                    policyData.subpolicies.push(subpolicyData)
                  })
                }
                
                sectionData.policies.push(policyData)
              }
            })
            
            // If entire section is selected but no specific policies, include all policies
            if (section.selected && sectionData.policies.length === 0) {
              section.subsections.forEach(policy => {
                const policyData = {
                  policy_id: policy.id,
                  policy_title: policy.title,
                  policy_description: policy.description || '',
                  policy_text: policy.content || '',
                  scope: policy.scope || '',
                  objective: policy.objective || '',
                  policy_type: policy.policy_type || '',
                  policy_category: policy.policy_category || '',
                  policy_subcategory: policy.policy_subcategory || '',
                  subpolicies: []
                }
                if (policy.ai_analysis) policyData.ai_analysis = policy.ai_analysis
                
                // Include all subpolicies for this policy
                if (policy.subpolicies) {
                  policy.subpolicies.forEach(subpolicy => {
                    const subpolicyData = {
                      subpolicy_id: subpolicy.id,
                      subpolicy_title: subpolicy.title,
                      subpolicy_description: subpolicy.description || '',
                      subpolicy_text: subpolicy.content || '',
                      control: subpolicy.control || ''
                    }
                    if (subpolicy.ai_analysis) subpolicyData.ai_analysis = subpolicy.ai_analysis
                    policyData.subpolicies.push(subpolicyData)
                  })
                }
                
                sectionData.policies.push(policyData)
              })
            }
            
            if (sectionData.policies.length > 0) {
              selectedItems.push(sectionData)
            }
          }
        })
        
        if (selectedItems.length === 0) {
          alert('No items selected. Please select at least one section, policy, or subpolicy.')
          return
        }
        
        // Count totals
        const totalSections = selectedItems.length
        const totalPolicies = selectedItems.reduce((sum, section) => sum + section.policies.length, 0)
        const totalSubpolicies = selectedItems.reduce((sum, section) => 
          sum + section.policies.reduce((pSum, policy) => pSum + policy.subpolicies.length, 0), 0)
        
        console.log('Selected items (hierarchical):', selectedItems)
        console.log(`Totals: ${totalSections} sections, ${totalPolicies} policies, ${totalSubpolicies} subpolicies`)
        
        // Prepare the request data
        const requestData = {
          task_id: taskId.value,
          selected_items: selectedItems
        }
        
        console.log('Saving selected items to checked_section.json:', requestData)
        
        // Add user_id to request data
        requestData.user_id = localStorage.getItem('user_id') || '1'
        
        // Clear compliance cache when selections change so next generate hits AI
        policyFrameworkCacheService.clearTaskCache(taskId.value)

        // Call the new backend API to save selected items
        const data = await apiService.post(API_ENDPOINTS.SAVE_CHECKED_SECTIONS_JSON, requestData)

        if (data) {
          console.log('Successfully saved selected items:', data)
          
          uploadStatus.value = {
            type: 'success',
            message: `Successfully saved ${data.total_sections} sections, ${data.total_policies} policies, and ${data.total_subpolicies} subpolicies to checked_section.json!`
          }
          
          // Close content viewer and proceed to next step
          closeContentViewer()
          goToStep(4)
          complianceGenerationMessage.value = "Initializing compliance generation..."
          complianceGenerationProgress.value = 0
          
          // Save state when starting step 4
          saveProcessingState()
          
          // Start Step 4: Generate compliances for checked sections
          await generateCompliancesForCheckedSections()
          
          setTimeout(() => {
            uploadStatus.value = null
          }, 5000)
          
        } else {
          throw new Error(data.error || 'Failed to save selected sections')
        }
        
      } catch (error) {
        console.error('Error saving selected sections:', error)
        
        uploadStatus.value = {
          type: 'error',
          message: `Error saving selected sections: ${error.response?.data?.error || error.message}`
        }
        
        // Clear error message after 8 seconds
        setTimeout(() => {
          uploadStatus.value = null
        }, 8000)
      }
    }

    // Step 4: Process PDFs in checked sections
    const generateCompliancesForCheckedSections = async () => {
      try {
        complianceGenerationMessage.value = "Checking cache and reading checked_section.json..."
        complianceGenerationProgress.value = 10

        // OPTIMIZATION: Check cache first
        const cached = policyFrameworkCacheService.getCachedCompliances(taskId.value)
        if (cached) {
          console.log('🎯 Using cached compliance results for task:', taskId.value)
          
          // Update UI with cached data
          complianceStats.value.total_subpolicies = cached.stats.total_subpolicies
          complianceStats.value.processed_subpolicies = cached.stats.total_subpolicies
          complianceStats.value.total_compliances = cached.stats.total_compliances

          complianceGenerationMessage.value = `Loaded cached compliances: ${cached.stats.total_compliances} compliances from ${cached.stats.total_subpolicies} subpolicies`
          complianceGenerationProgress.value = 100

          // Update overview stats
          overviewStats.value = {
            total_sections: cached.stats.total_sections || 0,
            total_policies: cached.stats.total_policies || 0,
            total_subpolicies: cached.stats.total_subpolicies,
            total_compliances: cached.stats.total_compliances,
            timestamp: new Date().toLocaleString()
          }

          // Save state and move to overview step
          saveProcessingState()
          goToStep(5)
          return
        }

        // Save state after initial progress
        saveProcessingState()

        complianceGenerationMessage.value = "Generating compliances with AI optimization..."
        complianceGenerationProgress.value = 25

        // OPTIMIZATION: Use cached compliance generation with deduplication
        const userId = localStorage.getItem('user_id') || '1'
        const result = await policyFrameworkCacheService.generateCompliances(taskId.value, userId)

        complianceGenerationProgress.value = 75
        complianceGenerationMessage.value = "Finalizing compliance records..."

        // Save state after 75% progress
        saveProcessingState()

        console.log('✅ Successfully generated compliances:', result)

        // Update stats from cached result
        complianceStats.value.total_subpolicies = result.stats.total_subpolicies
        complianceStats.value.processed_subpolicies = result.stats.total_subpolicies
        complianceStats.value.total_compliances = result.stats.total_compliances

        complianceGenerationMessage.value = `Successfully generated ${result.stats.total_compliances} compliances from ${result.stats.total_subpolicies} subpolicies`
        complianceGenerationProgress.value = 100

        // Update overview stats
        overviewStats.value = {
          total_sections: result.stats.total_sections || 0,
          total_policies: result.stats.total_policies || 0,
          total_subpolicies: result.stats.total_subpolicies,
          total_compliances: result.stats.total_compliances,
          timestamp: new Date().toLocaleString()
        }

        // OPTIMIZATION: Preload module AI analysis for policy (silent if disabled)
        moduleAiAnalysisService.fetchModuleAnalysis('policy', null).catch(() => {
          // Silently ignore - module may be disabled by configuration
        })

        // Save state after compliance generation completes
        saveProcessingState()

        // Move to overview step
        goToStep(5)

      } catch (error) {
        console.error('❌ Error generating compliances:', error)

        complianceGenerationMessage.value = `Error generating compliances: ${error.response?.data?.error || error.message}`
        
        // Save state even on error to preserve current progress
        saveProcessingState()

        // Show error notification
        uploadStatus.value = {
          type: 'error',
          message: `Failed to generate compliances: ${error.response?.data?.error || error.message}`
        }

        // Clear error message after 5 seconds
        setTimeout(() => {
          uploadStatus.value = null
        }, 5000)
      }
    }
    
    // Load checked sections data when Step 6 is reached
    const loadCheckedSectionsData = async () => {
      try {
        console.log('Loading checked sections data for task:', taskId.value)
        console.log('API Endpoint URL:', API_ENDPOINTS.GET_CHECKED_SECTIONS_WITH_COMPLIANCE)
        console.log('API_BASE_URL:', API_BASE_URL)
        
        // Check if endpoint is defined
        if (!API_ENDPOINTS.GET_CHECKED_SECTIONS_WITH_COMPLIANCE) {
          console.error('GET_CHECKED_SECTIONS_WITH_COMPLIANCE endpoint is undefined!')
          return
        }
        
        // Fallback URL in case of caching issues
        const apiUrl = API_ENDPOINTS.GET_CHECKED_SECTIONS_WITH_COMPLIANCE || `${API_BASE_URL}/api/get-checked-sections-with-compliance/`
        console.log('Final API URL being called:', apiUrl)
        
        const data = await apiService.get(apiUrl, { timeout: 30000 })
        
        if (data && data.success) {
          checkedSectionsData.value = data.data
          console.log('Loaded data:', checkedSectionsData.value)
          
          // Pre-populate framework form
          if (checkedSectionsData.value.metadata) {
            const metadata = checkedSectionsData.value.metadata
            const frameworkInfo = metadata.framework_info || {}
            
            // Populate framework form with framework_info data
            frameworkForm.value.FrameworkName = frameworkInfo.framework_name || metadata.task_id?.replace('_', ' ') || 'New Framework'
            frameworkForm.value.FrameworkDescription = frameworkInfo.framework_description || `Generated from ${metadata.task_id || 'upload'}`
            frameworkForm.value.CurrentVersion = frameworkInfo.current_version || '1.0'
            frameworkForm.value.Category = frameworkInfo.category || ''
            frameworkForm.value.Identifier = frameworkInfo.framework_name || ''
            frameworkForm.value.Status = 'Under Review'
            frameworkForm.value.Reviewer = ''
            
            console.log('[DEBUG] Populated framework form:', frameworkForm.value)
          }
          
          // Save state after step 6 data is loaded
          saveProcessingState()
        }
      } catch (error) {
        console.error('Error loading checked sections data:', error)
        
        // Handle specific error cases
        if (error.response?.status === 429) {
          uploadStatus.value = {
            type: 'error',
            message: 'Too many requests. Please wait a moment and try again.'
          }
        } else if (error.response?.status === 401) {
          uploadStatus.value = {
            type: 'error',
            message: 'Authentication failed. Please refresh the page and try again.'
          }
        } else if (error.response?.status === 404) {
          uploadStatus.value = {
            type: 'error',
            message: 'API endpoint not found. Please contact support.'
          }
        } else {
          uploadStatus.value = {
            type: 'error',
            message: 'Failed to load data: ' + (error.response?.data?.error || error.message)
          }
        }
      }
    }
    
    // Get compliances for a specific subpolicy
    const getCompliancesForSubpolicy = (subpolicyId) => {
      if (!checkedSectionsData.value || !checkedSectionsData.value.sections) {
        console.log(`[DEBUG] No checkedSectionsData or sections for subpolicy: ${subpolicyId}`)
        return []
      }
      
      // Search through sections, policies, and subpolicies to find compliances
      for (const section of checkedSectionsData.value.sections) {
        for (const policy of section.policies || []) {
          for (const subpolicy of policy.subpolicies || []) {
            if (subpolicy.subpolicy_id === subpolicyId) {
              const compliances = subpolicy.compliances || []
              console.log(`[DEBUG] Found ${compliances.length} compliances for subpolicy: ${subpolicyId}`)
              return compliances
            }
          }
        }
      }
      
      console.log(`[DEBUG] No compliances found for subpolicy: ${subpolicyId}`)
      return []
    }
    
    // Save all edited data to database
    const saveToDatabase = async () => {
      try {
        isSavingToDatabase.value = true
        
        const payload = {
          task_id: taskId.value,
          framework: frameworkForm.value,
          sections: checkedSectionsData.value.sections,
          user_id: localStorage.getItem('user_id') || '1'
        }
        
        console.log('Saving to database:', payload)
        
        const data = await apiService.post(API_ENDPOINTS.SAVE_EDITED_FRAMEWORK_TO_DATABASE, payload)
        
        if (data && data.success) {
          const frameworkId = data.framework_id
          const totalCompliances = data.total_compliances || 0
          const totalPolicies = data.total_policies || 0
          const totalSubpolicies = data.total_subpolicies || 0
          
          uploadStatus.value = {
            type: 'success',
            message: `✅ Successfully saved to database!\n\nFramework ID: ${frameworkId}\nPolicies: ${totalPolicies} | SubPolicies: ${totalSubpolicies} | Compliances: ${totalCompliances}\n\nRedirecting to Policies page...`
          }
          
          console.log('✅ Database save successful!')
          console.log(`Framework ID: ${frameworkId}`)
          console.log(`Total Policies: ${totalPolicies}`)
          console.log(`Total SubPolicies: ${totalSubpolicies}`)
          console.log(`Total Compliances: ${totalCompliances}`)
          
          // Wait 3 seconds to show success message, then redirect to Framework Explorer
          setTimeout(() => {
            uploadStatus.value = null
            // Redirect to Framework Explorer (optionally to the new framework's policies page)
            const path = frameworkId ? `/framework-explorer/policies/${frameworkId}` : '/framework-explorer'
            router.push(path)
          }, 3000)
        }
      } catch (error) {
        console.error('Error saving to database:', error)
        uploadStatus.value = {
          type: 'error',
          message: 'Failed to save: ' + (error.response?.data?.error || error.message)
        }
        
        // Clear error after 8 seconds
        setTimeout(() => {
          uploadStatus.value = null
        }, 8000)
      } finally {
        isSavingToDatabase.value = false
      }
    }
    
    const processCheckedSectionsPDFs = async () => {
      try {
        policyExtractionMessage.value = "Processing PDFs in checked sections..."
        policyExtractionProgress.value = 10
        
        const userId = localStorage.getItem('user_id') || '1'
        
        // Call the backend API to process PDFs
        const data = await apiService.post(API_ENDPOINTS.CHECKED_SECTIONS_PROCESS_PDFS, {
          user_id: userId,
          task_id: taskId.value
        })
        
        if (data && data.success) {
          console.log('Successfully processed PDFs:', data)
          
          const summary = data.data.summary
          policyExtractionMessage.value = `Successfully processed ${summary.successful_extractions} PDFs`
          policyExtractionProgress.value = 100
          
          // Update extracted policies count
          extractedPoliciesCount.value = summary.successful_extractions
          
          // Wait a moment to show completion, then proceed to Step 5
          setTimeout(() => {
            policyExtractionComplete.value = true
            goToStep(5)
          }, 2000)
          
        } else {
          throw new Error(data.error || 'Failed to process PDFs')
        }
        
      } catch (error) {
        console.error('Error processing PDFs:', error)
        
        policyExtractionMessage.value = `Error processing PDFs: ${error.response?.data?.error || error.message}`
        policyExtractionProgress.value = 0
        
        // Show error for 5 seconds, then allow retry
        setTimeout(() => {
          policyExtractionMessage.value = "Click 'Retry' to try again"
        }, 5000)
      }
    }

    // Policy extraction (legacy - replaced by processCheckedSectionsPDFs)
    // const pollPolicyExtractionStatus = () => { ... }

    // Legacy function - replaced by processCheckedSectionsPDFs
    // const fetchExtractedPolicies = async () => { ... }

    const viewPolicyExtractor = async () => {
      try {
        const userId = localStorage.getItem('user_id') || '1'
        
        // Use the new endpoint to get extracted policies form data
        const data = await apiService.get(`${API_ENDPOINTS.CHECKED_SECTIONS_GET_FORM_DATA}${userId}/?task_id=${taskId.value}`)
        
        if (data && data.success && data.data && data.data.policies) {
          const policiesData = data.data.policies
          
          // Transform the data for the form
          const transformedPolicies = policiesData.map(policy => ({
            policy_name: policy.policy_name,
            sub_policies: policy.sub_policies.map(subPolicy => ({
              id: subPolicy.id,
              title: subPolicy.title,
              sub_sections: subPolicy.sub_sections,
              related_controls: subPolicy.related_controls
            }))
          }))
          
          // Ensure transformedPolicies is valid
          if (!transformedPolicies || !Array.isArray(transformedPolicies)) {
            console.error('Invalid transformed policies data:', transformedPolicies)
            throw new Error('Invalid policies data received from server')
          }
          
          // Filter out any invalid policies before setting
          const validTransformedPolicies = transformedPolicies.filter(policy => 
            policy && policy.policy_name && policy.sub_policies && Array.isArray(policy.sub_policies)
          )
          
          if (validTransformedPolicies.length === 0) {
            console.warn('No valid policies found in transformed data, creating default')
            validTransformedPolicies.push({
              policy_name: 'Default Policy',
              sub_policies: [{
                id: 'default',
                title: 'Default Control',
                sub_sections: {
                  'main': {
                    'text': 'No policy data available',
                    'order': 1
                  }
                },
                related_controls: []
              }]
            })
          }
          
          policies.value = validTransformedPolicies
          extractedPoliciesCount.value = data.data.total_policies || policies.value.length
          
          // Populate the form with the extracted data
          populatePolicyForm(validTransformedPolicies)
          
          goToStep(6)
        } else {
          throw new Error(data.error || 'No policies found')
        }
      } catch (error) {
        console.error('Error loading extracted policies:', error)
        uploadStatus.value = {
          type: 'error',
          message: 'Failed to load extracted policies. Please try again.'
        }
      }
    }
    
    const populatePolicyForm = (policiesData) => {
      try {
        // Clear existing form data
        policyFormData.value = {}
        
        console.log('Populating form with policies data:', policiesData)
        
        // Populate form with extracted data
        policiesData.forEach((policy, index) => {
          // Add null checks for policy structure
          if (!policy) {
            console.warn(`Skipping null policy at index ${index}`)
            return
          }
          
          if (!policy.policy_name) {
            console.warn(`Skipping policy with missing policy_name at index ${index}:`, policy)
            // Create a fallback policy name
            policy.policy_name = `Policy_${index + 1}`
          }

          const safePolicyName = sanitizeObjectKey(policy.policy_name)
          // Initialize main policy form data
          policyFormData.value[safePolicyName] = {
            documentUrl: '',
            identifier: '',
            createdBy: '',
            reviewer: '',
            policyName: policy.policy_name,
            department: '',
            scope: '',
            applicability: '',
            objective: '',
            coverageRate: 0
          }
          
          // Initialize sub-policy form data with null checks
          if (policy.sub_policies && Array.isArray(policy.sub_policies)) {
            policy.sub_policies.forEach((subPolicy, subIndex) => {
              if (!subPolicy) {
                console.warn(`Skipping null sub-policy at index ${subIndex} for policy ${policy.policy_name}`)
                return
              }
              
              if (!subPolicy.id) {
                console.warn(`Skipping sub-policy with missing id at index ${subIndex} for policy ${policy.policy_name}:`, subPolicy)
                // Create a fallback ID
                subPolicy.id = `sub_${subIndex + 1}`
              }
              
              const safeSubPolicyId = sanitizeObjectKey(subPolicy.id)
              const sectionKey = `${safePolicyName}_${safeSubPolicyId}`
              
              // Create form data for this sub-policy
              policyFormData.value[sectionKey] = {
                documentUrl: '',
                identifier: subPolicy.id,
                createdBy: '',
                reviewer: '',
                policyName: subPolicy.title || subPolicy.id,
                department: '',
                scope: '',
                applicability: '',
                objective: '',
                coverageRate: 0,
                // Add sub-sections as compliance information
                complianceInfo: {}
              }
              
              // Initialize compliance info for each sub-section with null checks
              if (subPolicy.sub_sections && typeof subPolicy.sub_sections === 'object') {
                Object.keys(subPolicy.sub_sections).forEach(key => {
                  const sectionData = subPolicy.sub_sections[key]
                  if (sectionData) {
                    // Ensure the complianceInfo object exists
                    if (!policyFormData.value[sectionKey].complianceInfo) {
                      policyFormData.value[sectionKey].complianceInfo = {}
                    }
                    const safeSectionKey = sanitizeObjectKey(key)
                    policyFormData.value[sectionKey].complianceInfo[safeSectionKey] = {
                      section: key,
                      text: sectionData.text || '',
                      order: sectionData.order || 0
                    }
                  }
                })
              }
              
              // Add related controls
              policyFormData.value[sectionKey].relatedControls = subPolicy.related_controls || []
            })
          }
        })
        
        console.log('Form populated with extracted policy data:', policyFormData.value)
        
      } catch (error) {
        console.error('Error populating policy form:', error)
      }
    }

    const closePolicyExtractor = () => {
      showPolicyExtractor.value = false
    }

    // Policy editing
    const editPolicy = (policy, index) => {
      currentPolicy.value = {...policy}
      currentPolicyIndex.value = index
      showPolicyDetail.value = true
    }
    
    const savePolicy = async () => {
      try {
        if (currentPolicyIndex.value !== null) {
          policies.value[currentPolicyIndex.value] = {...currentPolicy.value}
        }
        
        // For now, we'll skip this step as it's not implemented in the new backend yet
        // This will be implemented in the next steps
        console.log('Saving policy:', currentPolicy.value)
        
        // Simulate successful response
        const response = { status: 200 }
        
        if (response.status === 200) {
          showPolicyDetail.value = false
          
          uploadStatus.value = {
            type: 'success',
            message: `Policy "${currentPolicy.value.Sub_policy_id}" saved successfully!`
          }
          
          setTimeout(() => {
            uploadStatus.value = null
          }, 5000)
        }
      } catch (error) {
        console.error('Error saving policy:', error)
        uploadStatus.value = {
          type: 'error',
          message: error.response?.data?.error || 'Failed to save policy. Please try again.'
        }
      }
    }
    
    const saveAllPolicies = async () => {
      try {
        // For now, we'll skip this step as it's not implemented in the new backend yet
        // This will be implemented in the next steps
        console.log('Saving all policies:', policies.value)
        
        // Simulate successful response
        const response = { status: 200 }
        
        if (response.status === 200) {
          uploadStatus.value = {
            type: 'success',
            message: `All policies saved successfully! (${policies.value.length} policies)`
          }
          
          setTimeout(() => {
            uploadStatus.value = null
          }, 5000)
        }
      } catch (error) {
        console.error('Error saving all policies:', error)
        uploadStatus.value = {
          type: 'error',
          message: error.response?.data?.error || 'Failed to save policies. Please try again.'
        }
      }
    }

    const closePolicyDetail = () => {
      showPolicyDetail.value = false
      currentPolicy.value = {}
      currentPolicyIndex.value = null
    }

    // Table row expansion
    const toggleExpandRow = (index) => {
      expandedRows.value = {
        ...expandedRows.value,
        [index]: !expandedRows.value[index]
      }
    }
    
    const getFormattedControl = (controlText) => {
      if (!controlText) return []
      
      if (/^\s*[\d*-]+\s+/.test(controlText)) {
        return controlText.split('\n')
          .filter(line => line.trim())
          .map(line => line.trim())
      }
      
      return controlText.split(/\.\s+|\.\n/)
        .filter(sentence => sentence.trim())
        .map(sentence => sentence.trim() + (sentence.endsWith('.') ? '' : '.'))
    }

    // Form management
    const initializePolicyFormData = () => {
      const newFormData = Object.create(null)
      uniqueSectionNames.value.forEach((sectionName) => {
        const safeSection = sanitizeObjectKey(sectionName)
        if (!policyFormData.value[safeSection]) {
          newFormData[safeSection] = {
            documentUrl: '',
            identifier: '',
            createdBy: '',
            reviewer: '',
            policyName: '',
            department: '',
            scope: '',
            applicability: '',
            objective: '',
            coverageRate: 0
          }
        } else {
          newFormData[safeSection] = policyFormData.value[safeSection]
        }
      })
      policyFormData.value = newFormData
    }

    const initializeDynamicForms = () => {
      policyFormData.value = Object.create(null)

      uniqueSectionNames.value.forEach((sectionName) => {
        const safeSection = sanitizeObjectKey(sectionName)
        policyFormData.value[safeSection] = {
          documentUrl: '',
          identifier: '',
          createdBy: '',
          reviewer: '',
          policyName: '',
          department: '',
          scope: '',
          applicability: '',
          objective: '',
          coverageRate: 0
        }
      })
    }

    // Compliance management
    const getComplianceItems = (control) => {
      if (!control || control.trim() === '') return [];
      
      const letterPattern = /([a-z])[.)](\s*)/gi;
      const matches = [];
      let match;
      while ((match = letterPattern.exec(control)) !== null) {
        matches.push({
          letter: match[1].toLowerCase(),
          index: match.index,
          matchLength: match[0].length
        });
      }
      
      if (matches.length === 0) {
        if (control.trim().length < 5) return [];
        
        return [{
          id: 'compliance_1',
          letter: 'a',
          name: control.substring(0, 100) + (control.length > 100 ? '...' : ''),
          description: control,
          status: 'pending',
          assignee: '',
          dueDate: '',
          evidence: null
        }];
      }
      
      const items = matches.map((match, index) => {
        const startPos = match.index + match.matchLength;
        const endPos = index < matches.length - 1 ? matches[index + 1].index : control.length;
        const content = control.substring(startPos, endPos).trim();
        
        if (content.length < 5) return null;
        
        return {
          id: `compliance_${index + 1}`,
          letter: match.letter,
          name: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
          description: content,
          status: 'pending',
          assignee: '',
          dueDate: '',
          evidence: null
        };
      }).filter(item => item !== null);
      
      return items;
    }
    
    const initializeComplianceData = () => {
      const newComplianceData = {}
      
      policies.value.forEach(policy => {
        if (!policy.control || policy.control.trim() === '') return;
        
        const policyKey = sanitizeObjectKey(`${policy.section_name}_${policy.Sub_policy_id}`)
        const complianceItems = getComplianceItems(policy.control)
        
        if (complianceItems.length > 0) {
          newComplianceData[policyKey] = complianceItems
        }
      })
      
      complianceData.value = newComplianceData
    }
    
    const handleComplianceFileUpload = (event, policyKey, complianceIndex) => {
      const safePolicyKey = sanitizeObjectKey(policyKey)
      const file = event.target.files[0]
      if (file && complianceData.value[safePolicyKey] && complianceData.value[safePolicyKey][complianceIndex]) {
        complianceData.value[safePolicyKey][complianceIndex].evidence = file
      }
    }
    
    const addComplianceItem = (policyKey) => {
      const safePolicyKey = sanitizeObjectKey(policyKey)
      if (!complianceData.value[safePolicyKey]) {
        complianceData.value[safePolicyKey] = []
      }
      
      const newIndex = complianceData.value[safePolicyKey].length
      const newItem = {
        id: `compliance_${newIndex + 1}`,
        letter: String.fromCharCode(97 + newIndex),
        name: '',
        description: '',
        status: 'pending',
        assignee: '',
        dueDate: '',
        evidence: null
      }
      
      complianceData.value[safePolicyKey].push(newItem)
    }
    
    const removeComplianceItem = (policyKey, index) => {
      const safePolicyKey = sanitizeObjectKey(policyKey)
      if (complianceData.value[safePolicyKey] && complianceData.value[safePolicyKey].length > 1) {
        complianceData.value[safePolicyKey].splice(index, 1)
        
        complianceData.value[safePolicyKey].forEach((item, idx) => {
          item.letter = String.fromCharCode(97 + idx)
          item.id = `compliance_${idx + 1}`
        })
      }
    }

    // File upload handlers
    const handleSubPolicyFileUpload = (event, index) => {
      const file = event.target.files[0]
      if (file && policies.value[index]) {
        policies.value[index].uploaded_file = file
      }
    }

    // Save and reset methods
    const saveAllDetails = async () => {
      try {
        console.log('🔄 Starting save process...')
        console.log('🔄 Button clicked - saveAllDetails function called!')
        console.log('🔄 Current task ID:', taskId.value)
        console.log('🔄 Current policies:', policies.value)
        console.log('🔄 Current policy form data:', policyFormData.value)
        
        // Check if we have the required data
        if (!taskId.value) {
          console.error('❌ No task ID found!')
          uploadStatus.value = {
            type: 'error',
            message: 'No task ID found. Please restart the upload process.'
          }
          return
        }
        
        if (!policies.value || policies.value.length === 0) {
          console.error('❌ No policies found!')
          uploadStatus.value = {
            type: 'error',
            message: 'No policies found. Please complete the previous steps first.'
          }
          return
        }
        
        // Transform the data to match backend expectations
        const transformedSubPolicies = policies.value.map(policy => ({
          ...policy,
          section_name: policy.policy_name, // Add section_name for backend compatibility
          sub_policies: policy.sub_policies.map(subPolicy => ({
            ...subPolicy,
            Sub_policy_id: subPolicy.id, // Ensure Sub_policy_id field exists for backend
            sub_policy_name: subPolicy.title || subPolicy.id // Ensure sub_policy_name field exists
          }))
        }))
        
        // First, save the complete package to JSON/Excel files
        const completePackage = {
          task_id: taskId.value || 'default_task',
          framework_details: policyDetails.value,
          policy_forms: policyFormData.value,
          sub_policies: transformedSubPolicies,
          compliance_data: complianceData.value,
          unique_sections: uniqueSectionNames.value
        }
        
        console.log('📦 Complete package data:', completePackage)
        console.log('📦 Task ID:', taskId.value)
        console.log('📦 Framework details:', policyDetails.value)
        console.log('📦 Policy forms:', policyFormData.value)
        console.log('📦 Transformed sub policies:', transformedSubPolicies)
        console.log('📦 Compliance data:', complianceData.value)
        console.log('📦 Unique sections:', uniqueSectionNames.value)
        
        // Debug compliance data structure
        console.log('🔍 Compliance data keys:', Object.keys(complianceData.value))
        transformedSubPolicies.forEach(policy => {
          policy.sub_policies.forEach(subPolicy => {
            const expectedKey = `${policy.policy_name}_${subPolicy.id}`
            console.log(`🔍 Expected compliance key: ${expectedKey}, exists: ${expectedKey in complianceData.value}`)
          })
        })
        
        console.log('📦 Saving complete package to files...')
        console.log('📦 API endpoint for files:', API_ENDPOINTS.SAVE_COMPLETE_POLICY_PACKAGE)
        
        // Save to files first
        console.log('📦 Making API call to save files...')
        const fileResponse = await apiService.post(API_ENDPOINTS.SAVE_COMPLETE_POLICY_PACKAGE, completePackage)
        console.log('📦 File save response:', fileResponse)
        
        console.log('✅ Files saved successfully')
        
        // Now save to database
        try {
          console.log('🗄️ Saving to database...')
          console.log('🗄️ API endpoint for database:', API_ENDPOINTS.SAVE_FRAMEWORK_TO_DATABASE)
          
          console.log('🗄️ Making API call to save to database...')
          const result = await apiService.post(API_ENDPOINTS.SAVE_FRAMEWORK_TO_DATABASE, {
            task_id: taskId.value || 'default_task'
          })
          console.log('🗄️ Database save response:', result)
          
          if (result && result.framework_id) {
            console.log('✅ Database save successful:', result)
            
            uploadStatus.value = {
              type: 'success',
              message: `Framework "${policyDetails.value.title || 'Untitled'}" has been created successfully!\nFramework ID: ${result.framework_id}\nPolicies: ${result.total_policies}\nSub-policies: ${result.total_sub_policies}\nCompliance items: ${result.total_compliance_items}`
            }
            
            showCongratulationsModal.value = true
            
            // Clear persistent state only when entire process is complete
            clearProcessingState()
            
            setTimeout(() => {
              uploadStatus.value = null
            }, 10000)
          }
        } catch (dbError) {
          console.error('❌ Error saving to database:', dbError)
          uploadStatus.value = {
            type: 'warning',
            message: `Files saved successfully, but database save failed: ${dbError.message}`
          }
        }
      } catch (error) {
        console.error('❌ Error saving complete package:', error)
        uploadStatus.value = {
          type: 'error',
          message: error.message || 'Failed to save package. Please try again.'
        }
      }
    }
    
    const resetAllForms = () => {
      policyDetails.value = {
        title: '',
        description: '',
        category: '',
        effectiveDate: '',
        startDate: '',
        endDate: ''
      }
      
      policyFormData.value = {}
      initializePolicyFormData()
      
      policies.value.forEach(policy => {
        policy.scope = ''
        policy.department = ''
        policy.objective = ''
        policy.applicability = ''
        policy.coverage_rate = 0
        policy.start_date = ''
        policy.end_date = ''
        policy.uploaded_file = null
      })
    }

    const resetUpload = () => {
      selectedFile.value = null
      isProcessing.value = false
      isLoadingDefault.value = false
      processingComplete.value = false
      uploadStatus.value = null
      processingStatus.value = { progress: 0, message: '' }
      taskId.value = null
      uploadedFileName.value = ''
      processingStartTime.value = ''
      if (fileInput.value) {
        fileInput.value.value = ''
      }
      sections.value = []
      showContentViewer.value = false
      policyExtractionComplete.value = false
      policyExtractionInProgress.value = false
      policyExtractionMessage.value = ''
      policyExtractionProgress.value = 0
      showPolicyExtractor.value = false
      policies.value = []
      extractedPoliciesCount.value = 0
      
      // Clear persistent state
      clearProcessingState()
      selectedSectionsCount.value = 0
      currentStep.value = 1
      stepHistory.value = [1]
    }

    const clearCache = async () => {
      resetUpload()
      policyFrameworkCacheService.clearAllCache()
      moduleAiAnalysisService.clearCache()
      try {
        await apiService.post(API_ENDPOINTS.AI_CACHE_CLEAR)
      } catch (e) {
        console.warn('Backend AI cache clear failed (continuing):', e)
      }
      const instance = getCurrentInstance()
      if (instance?.proxy?.$notify) {
        instance.proxy.$notify({
          type: 'success',
          title: 'Cache cleared',
          text: 'Frontend and backend AI cache cleared. You can start a fresh upload.'
        })
      }
    }

    const goToPolicyDashboard = () => {
      showCongratulationsModal.value = false
      window.location.href = '/policy-dashboard'
    }

    // Watch for changes in policies to initialize form data
    watch(policies, () => {
      if (policies.value.length > 0) {
        initializePolicyFormData()
        initializeComplianceData()
      }
    }, { immediate: true })
    
    // Watch for step changes to load data
    watch(currentStep, async (newStep, oldStep) => {
      if (newStep === 6 && oldStep === 5) {
        // Load data when entering Step 6 from Step 5
        await loadCheckedSectionsData()
      }
    })
    
    // Watch for framework form changes to save state
    watch(frameworkForm, () => {
      if (currentStep.value === 6) {
        saveProcessingState()
      }
    }, { deep: true })
    
    // Watch for checked sections data changes to save state
    watch(checkedSectionsData, () => {
      if (currentStep.value === 6) {
        saveProcessingState()
      }
    }, { deep: true })

    // OPTIMIZATION: Enhanced cleanup with cache management on component unmount
    onUnmounted(() => {
      console.log('🧹 UploadFramework component unmounting - performing cleanup...')
      
      // Clear polling intervals
      if (progressInterval) {
        clearInterval(progressInterval)
      }
      if (statusInterval) {
        clearInterval(statusInterval)
      }
      
      // OPTIMIZATION: Log cache statistics before cleanup
      const cacheStats = policyFrameworkCacheService.getCacheStats()
      console.log('📊 Cache statistics before cleanup:', cacheStats)
      
      // OPTIMIZATION: Clear task-specific cache to free memory
      if (taskId.value) {
        policyFrameworkCacheService.clearTaskCache(taskId.value)
        console.log('🧹 Cleared cache for task:', taskId.value)
      }
      
      // OPTIMIZATION: Log final cache state
      const finalStats = policyFrameworkCacheService.getCacheStats()
      console.log('📊 Final cache statistics:', finalStats)
      
      console.log('✅ UploadFramework cleanup complete')
    })

    // Handle logout event
    const handleLogout = () => {
      console.log('🛑 Logout event received - stopping upload framework polling')
      if (progressInterval) {
        clearInterval(progressInterval)
        progressInterval = null
      }
      if (statusInterval) {
        clearInterval(statusInterval)
        statusInterval = null
      }
    }

    onMounted(() => {
      console.log('🔄 UploadFramework component mounted')

      // OPTIMIZATION: Log initial cache state and performance metrics
      const initialCacheStats = policyFrameworkCacheService.getCacheStats()
      const moduleStats = moduleAiAnalysisService.getCacheStats()
      console.log('📊 Initial cache statistics:', { 
        policyFramework: initialCacheStats,
        moduleAi: moduleStats 
      })

      // Listen for logout events
      eventBus.on(LOGOUT_EVENT, handleLogout)

      // Always attempt to restore state on mount
      console.log('🔄 Attempting state restoration on mount')

      // Use setTimeout to ensure DOM is ready before restoring state
      setTimeout(() => {
        const stateRestored = loadProcessingState()
        console.log('🔄 State restoration attempted:', stateRestored)

        if (stateRestored) {
          console.log('✅ Processing state restored from sessionStorage')
          console.log('🔄 Restored state:', {
            isProcessing: isProcessing.value,
            progress: processingStatus.value.progress,
            taskId: taskId.value,
            currentStep: currentStep.value
          })
          
          // Show notification that state was restored
          uploadStatus.value = {
            type: 'success',
            message: `Processing state restored! Continuing from ${processingStatus.value.progress || 0}% progress.`
          }
          
          // Clear notification after 5 seconds
          setTimeout(() => {
            uploadStatus.value = null
          }, 5000)
          
          resumeProcessingIfNeeded()
        } else {
          console.log('❌ No state to restore or state restoration failed')
        }
      }, 100) // Small delay to ensure component is fully initialized
      
      // Handle page refresh detection
      const handleBeforeUnload = () => {
        // Only clear state on actual refresh, not navigation
        if (isProcessing.value) {
          // Don't clear state on navigation - let it persist
          return
        }
      }
      
      // Listen for page refresh
      window.addEventListener('beforeunload', handleBeforeUnload)
      
      // Listen for browser navigation
      window.addEventListener('popstate', () => {
        console.log('🔄 Browser navigation detected, attempting state restoration')
        setTimeout(() => {
          loadProcessingState()
          resumeProcessingIfNeeded()
        }, 100)
      })
      
      // Clean up event listeners on unmount
      onUnmounted(() => {
        window.removeEventListener('beforeunload', handleBeforeUnload)
        window.removeEventListener('popstate', () => {})
      })
    })

    return {
      selectedFile,
              isDragOver,
      isUploading,
      isLoadingDefault,
      currentFrameworkKey,

      isProcessing,
      processingComplete,
      uploadStatus,
      fileInput,
      processingStatus,
      uploadedFileName,
      processingStartTime,
      showContentViewer,
      sections,
      searchQuery,
      filteredSections,
      policyExtractionComplete,
      policyExtractionInProgress,
      policyExtractionMessage,
      policyExtractionProgress,
      complianceGenerationMessage,
      complianceGenerationProgress,
      complianceStats,
      overviewStats,
      showPolicyExtractor,
      policies,
      extractedPoliciesCount,
      selectedSectionsCount,
      currentStep,
      triggerFileInput,
      handleFileSelect,
      handleDrop,
      removeFile,
      clearCache,
      formatFileSize,
      formatTime,
      getEstimatedCompletion,
      uploadFile,
      resetUpload,
      stopProcessing,
      saveProcessingState,
      loadProcessingState,
      clearProcessingState,
      resumeProcessingIfNeeded,
      viewExtractedContent,
      loadDefaultData,
        closeContentViewer,
        getPDFUrl,
        togglePDFView,
        closePDFView,
        toggleSection,
        toggleSubsection,
      updateSelection,
      updateSubsectionSelection,
      updateSubpolicySelection,
      selectAllSections,
      deselectAllSections,
      saveSelectedSections,
      viewPolicyExtractor,
      closePolicyExtractor,
      goBack,
      goToStep,
      showPolicyDetail,
      currentPolicy,
      currentPolicyIndex,
      isEditing,
      editPolicy,
      savePolicy,
      saveAllPolicies,
      expandedRows,
      toggleExpandRow,
      getFormattedControl,
      policyDetails,
      saveAllDetails,
      closePolicyDetail,
      handleSubPolicyFileUpload,
      resetAllForms,
      uniqueSectionNames,
      validPolicies,
      getValidSubPolicies,
      getValidRelatedControls,
      getValidSubSections,
      ensureFormData,
      ensureSubPolicyFormData,
      ensureComplianceInfo,
      policyFormData,
      initializePolicyFormData,
      initializeDynamicForms,
      complianceData,
      getComplianceItems,
      initializeComplianceData,
      handleComplianceFileUpload,
      addComplianceItem,
      removeComplianceItem,
             showCongratulationsModal,
       goToPolicyDashboard,
       handleLogout,
      navigateTo,
      testPDFExists,
      onPDFLoad,
      onPDFError,
      retryPDFLoad,
      getCheckedSectionsInfo,
      deleteCheckedSections,
      processCheckedSectionsPDFs,
      generateCompliancesForCheckedSections,
      populatePolicyForm,
      viewMode,
      filterType,
      viewModeOptions,
      filterTypeOptions,
      toggleSubpolicyDetails,
      onViewModeChange,
      onFilterTypeChange,
      checkedSectionsData,
      frameworkForm,
      isSavingToDatabase,
      loadCheckedSectionsData,
      getCompliancesForSubpolicy,
      saveToDatabase,
      // OPTIMIZATION: Cache monitoring functions for debugging and performance analysis
      getCacheStatistics: () => ({
        policyFramework: policyFrameworkCacheService.getCacheStats(),
        moduleAi: moduleAiAnalysisService.getCacheStats()
      }),
      clearAllCaches: () => {
        policyFrameworkCacheService.clearAllCache()
        moduleAiAnalysisService.clearCache()
        console.log('🧹 All caches cleared manually')
      }
    }
  }
}
</script>

<style>
@import '@/assets/css/main.css';
@import '@/assets/css/dropdown.css';
@import '@/assets/css/form.css';
</style>

<style scoped>

/* Remove left borders from all form sections/boxes */
.upload-framework .global-form-box {
  border-left: none !important;
}

/* Remove green from all form inputs – force neutral grey/white (overrides any global green) */
.upload-framework .global-form-input,
.upload-framework .global-form-textarea,
.upload-framework .global-form-select,
.upload-framework input[type="text"],
.upload-framework input[type="email"],
.upload-framework input[type="number"],
.upload-framework input[type="tel"],
.upload-framework textarea,
.upload-framework select {
  background-color: #ffffff !important;
  border: 1px solid #e5e7eb !important;
  color: #374151 !important;
}
.upload-framework .global-form-input:focus,
.upload-framework .global-form-textarea:focus,
.upload-framework .global-form-select:focus,
.upload-framework input[type="text"]:focus,
.upload-framework input[type="email"]:focus,
.upload-framework input[type="number"]:focus,
.upload-framework input[type="tel"]:focus,
.upload-framework textarea:focus,
.upload-framework select:focus {
  outline: none !important;
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
  background-color: #ffffff !important;
  color: #374151 !important;
}
.upload-framework .global-form-input::placeholder,
.upload-framework .global-form-textarea::placeholder,
.upload-framework input::placeholder,
.upload-framework textarea::placeholder {
  color: #9ca3af !important;
}

/* Policy Creation Header Styles */
.upload-framework .policy-creation-header {
  display: flex;
  flex-direction: column;
  gap: 30px;
  margin-bottom: 30px;
}

.upload-framework .policy-intro {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.upload-framework .policy-intro-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.upload-framework .policy-intro h2 {
  margin: 0;
  font-size: 28px;
  color: #000000;
}

.upload-framework .policy-intro p {
  color: #718096;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 4px;
}

.upload-framework-container {
  padding: 3rem;
  max-width: 1300px;
  margin: 0 auto;
  font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
  min-height: 100vh;
  margin-left: 230px !important;
}

/* Step Indicator */
.upload-framework .step-indicator {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  margin-bottom: 3rem;
}

.upload-framework .step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.upload-framework .step-item .step-number {
  align-self: center;
}

.upload-framework .step-number {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e2e8f0;
  color: #64748b;
  transition: all 0.3s ease;
}

.upload-framework .step-number i {
  color: inherit;
}

/* Colorblindness support for default step-number */
[data-colorblind="protanopia"] .upload-framework .step-number,
[data-colorblind="deuteranopia"] .upload-framework .step-number,
[data-colorblind="tritanopia"] .upload-framework .step-number {
  background: var(--cb-neutral-border, #e2e8f0);
  color: var(--cb-text-secondary, #64748b);
}

.upload-framework .step-number-value {
  display: inline-block;
  text-align: center;
  line-height: 1;
}

.upload-framework .step-item.active .step-number {
  background-color: #16a34a; /* green-600 - success color */
  color: white;
  transform: scale(1.1);
}

.upload-framework .step-item.active .step-number i {
  color: white;
}

/* Colorblindness support for active step-number - green */
[data-colorblind="protanopia"] .upload-framework .step-item.active .step-number,
[data-colorblind="tritanopia"] .upload-framework .step-item.active .step-number {
  background-color: var(--cb-success, #16a34a) !important; /* green for protanopia/tritanopia */
}

[data-colorblind="deuteranopia"] .upload-framework .step-item.active .step-number {
  background-color: var(--cb-success, #0f766e) !important; /* teal for deuteranopia */
}

.upload-framework .step-item.completed .step-number {
  background-color: #16a34a; /* green-600 - success color */
  color: white;
}

.upload-framework .step-item.completed .step-number i {
  color: white;
}

/* Colorblindness support for completed step-number - green */
[data-colorblind="protanopia"] .upload-framework .step-item.completed .step-number,
[data-colorblind="tritanopia"] .upload-framework .step-item.completed .step-number {
  background-color: var(--cb-success, #16a34a) !important; /* green for protanopia/tritanopia */
}

[data-colorblind="deuteranopia"] .upload-framework .step-item.completed .step-number {
  background-color: var(--cb-success, #0f766e) !important; /* teal for deuteranopia */
}

.upload-framework .step-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: #64748b;
  text-align: center;
  transition: all 0.3s ease;
}

.upload-framework .step-item.active .step-label {
  color: #1e293b;
  font-weight: 600;
}

.upload-framework .step-item.completed .step-label {
  color: #0f766e;
}

.upload-framework .step-divider {
  width: 80px;
  height: 2px;
  background: #94a3b8;
  margin: 0 1rem;
  margin-top: 23px; /* Align with center of 48px icon (24px - 1px for divider height) */
  transition: all 0.3s ease;
  align-self: flex-start;
}

.upload-framework .step-item.completed + .step-divider {
  background: #94a3b8;
}


.upload-framework .header {
  text-align: center;
  margin-bottom: 3rem;
  padding: 1rem;
  background: white;
  border-radius: 16px;
  
}

.upload-framework .header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.upload-framework .header-text {
  flex: 1;
  text-align: left;
}

.upload-framework .header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.upload-framework .stop-processing-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.upload-framework .stop-processing-btn:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.4);
}

.upload-framework .stop-processing-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}

.upload-framework .stop-processing-btn i {
  font-size: 1rem;
}

.upload-framework .header h1 {
  color: #000000;
  margin-bottom: 0.5rem;
  font-weight: 700;
  font-size: 1.5rem;
}

.upload-framework .header p {
  color: #64748b;
  font-size: 0.9rem;
  font-weight: 400;
}

.upload-section {
  background: white;
  border-radius: 20px;
  padding: -80px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Upload card header with clear cache (same pattern as Risk/Incident AI) */
.upload-framework .upload-card-header {
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  margin-bottom: 12px;
}

.upload-framework .upload-card-header h2 {
  margin: 0;
  color: var(--text-primary, #1e293b);
  font-size: 1.25rem;
  font-weight: 700;
}

.upload-framework .btn-clear-cache {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: 1px solid var(--border-color, #e2e8f0);
  color: var(--text-secondary, #64748b);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}

.upload-framework .btn-clear-cache:hover {
  color: #667eea;
  background: rgba(102, 126, 234, 0.1);
  border-color: #667eea;
}

/* Upload Area */
.upload-area {
  border: 3px dashed #cbd5e1;
  border-radius: 16px;
  padding: 2rem 2rem 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  position: relative;
  overflow: hidden;
}

.upload-area::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.upload-area:hover::before,
.upload-area.drag-over::before {
  opacity: 1;
}



.upload-content {
  position: relative;
  z-index: 1;
}



.upload-icon {
  font-size: 4rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.upload-content h3 {
  color: #1e293b;
  margin-bottom: 1rem;
  font-weight: 600;
  font-size: 1rem;
}

.upload-content p {
  color: #64748b;
  margin-bottom: 2rem;
  font-size: 0.9rem;
}

.supported-formats {
  color: #94a3b8;
  font-size: 0.9rem;
  padding: 1rem;
  background: rgba(156, 168, 184, 0.1);
  border-radius: 8px;
  display: inline-block;
}

/* OR Divider */
.or-divider {
  display: flex;
  align-items: center;
  margin: 2rem 0;
  color: #64748b;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #cbd5e1, transparent);
}

.divider-text {
  padding: 0 1.5rem;
  font-weight: 600;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Default Data Section */
.default-data-section {
  text-align: center;
  margin: 1rem 0;
  transition: all 0.3s ease;
}

.default-data-section:hover {
  transform: translateY(-2px);
}

.default-data-content {
  max-width: 500px;
  margin: 0 auto;
}

.default-data-content h3 {
  color: #1e293b;
  margin: 0;
  font-weight: 600;
  font-size: 1rem;
}

.default-data-content p {
  color: #64748b;
  margin: 0;
  font-size: 0.8rem;
  max-width: 500px;
  line-height: 1.5;
}

/* Button now uses global .btn-load-default class from main.css */

.divider-line {
  flex: 1;
  height: 2px;
  background: #e2e8f0;
}

.divider-text {
  padding: 0 1rem;
  font-size: 0.9rem;
  color: #64748b;
  font-weight: 500;
}

.default-data-section {
  text-align: center;
  margin-bottom: 2rem;
}

.default-data-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

/* File Preview */
.file-preview {
  margin: 2rem 0;
  padding: 2rem;

  transition: all 0.3s ease;
}



.file-info {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 2rem;
}



.file-icon {
  font-size: 1.5rem;
  color: rgb(49, 123, 196);
}

.file-details h4 {
  margin: 0;
  color: #1e293b;
  font-weight: 600;
  font-size: 0.9rem;
}

.file-details p {
  margin: 0.5rem 0 0 0;
  color: #64748b;
  font-size: 0.7rem;
}

.remove-btn {
  margin-left: auto;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.remove-btn:hover {
  transform: scale(1.1);
}

.upload-actions {
  text-align: center;
  margin-top: -2rem;
}

/* Upload Document button styles now use global .btn-upload-document from main.css */

/* Processing Section */
.processing-section {
  text-align: center;
  padding: 4rem 2rem;
}

.processing-header {
  margin-bottom: 3rem;
}

.processing-icon-container {
  margin-bottom: 2rem;
}

.processing-icon {
  font-size: 4rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.processing-header h3 {
  color: #1e293b;
  margin-bottom: 1rem;
  font-weight: 600;
  font-size: 2rem;
}

.processing-header p {
  color: #64748b;
  font-size: 1.2rem;
}

.progress-container {
  position: relative;
  margin-bottom: 3rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.progress-label {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e293b;
}

.progress-percentage {
  font-size: 1.5rem;
  font-weight: 700;
  color: #667eea;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.progress-bar {
  width: 100%;
  height: 16px;
  background: #f1f5f9;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
  margin-bottom: 1.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2, #4facfe);
  border-radius: 20px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  position: relative;
}

.progress-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 20px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.6), transparent);
  animation: glow-sweep 2s ease-in-out infinite;
}

@keyframes glow-sweep {
  0% { transform: translateX(-100px); }
  100% { transform: translateX(100px); }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.progress-stats {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #64748b;
  font-size: 0.9rem;
  font-weight: 500;
}

.stat-item i {
  color: #667eea;
  font-size: 1rem;
}

.processing-details {
  display: flex;
  justify-content: center;
  gap: 3rem;
  flex-wrap: wrap;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #64748b;
  font-size: 0.95rem;
}

.detail-item i {
  color: #667eea;
  font-size: 1.3rem;
}

/* Completion Section */
.completion-section {
  text-align: center;
  padding: 4rem 2rem;
}

.completion-icon-container {
  margin-bottom: 2rem;
}

.success-circle {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  color: white;
  font-size: 48px;
  box-shadow: 0 20px 40px rgba(16, 185, 129, 0.3);
  animation: successPulse 2s ease-in-out infinite;
}

@keyframes successPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.completion-header h3 {
  color: #1e293b;
  margin-bottom: 1rem;
  font-weight: 700;
  font-size: 2.2rem;
}

.completion-header p {
  color: #64748b;
  font-size: 1.2rem;
  max-width: 600px;
  margin: 0 auto 3rem;
}

.completion-actions {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.view-content-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  transition: all 0.3s ease;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.view-content-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
}

/* Extraction Section */
.extraction-section {
  text-align: center;
  padding: 4rem 2rem;
}

.extraction-header {
  margin-bottom: 3rem;
}

.extraction-icon-container {
  margin-bottom: 2rem;
}

.extraction-icon {
  font-size: 4rem;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.extraction-header h3 {
  color: #1e293b;
  margin-bottom: 1rem;
  font-weight: 600;
  font-size: 2rem;
}

.extraction-header p {
  color: #64748b;
  font-size: 1.2rem;
}

.extraction-details {
  display: flex;
  justify-content: center;
  gap: 3rem;
  flex-wrap: wrap;
}

/* Policy Review Section */
.upload-framework .policy-review-section {
  text-align: center;
  padding: 4rem 2rem;
}

.review-header {
  margin-bottom: 3rem;
}

.review-icon-container {
  margin-bottom: 2rem;
}

.review-header h3 {
  color: #1e293b;
  margin-bottom: 1rem;
  font-weight: 700;
  font-size: 2.2rem;
}

.review-header p {
  color: #64748b;
  font-size: 1.2rem;
  max-width: 600px;
  margin: 0 auto 3rem;
}

/* KPI cards (Sections, Policies, Subpolicies, Compliances) use .kpi-grid, .kpi-card, .kpi-card-icon, .kpi-card-body, .kpi-card-value, .kpi-card-title from main.css */

.overview-details {
  margin: 2rem 0;
}

.detail-card {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  padding: 2rem;
  margin: 1rem 0;
}

.detail-card h4 {
  color: #1e293b;
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.detail-card p {
  color: #64748b;
  line-height: 1.6;
  margin: 0.5rem 0;
}

.detail-card .timestamp {
  color: #94a3b8;
  font-size: 0.9rem;
  margin-top: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.review-actions {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

/* Edit Policy Details uses .btn-edit-review from main.css */

/* Enhanced Professional Layout for Step 6 */
.upload-framework .policy-details-section {
  padding: 2rem 0;
}

.details-header {
  text-align: left;
  margin-bottom: 3rem;
  padding: 0;
  background: none;
}

.details-header h3 {
  margin: 0 0 0.5rem 0;
  font-weight: 700;
  font-size: 2rem;
  color: #1e293b;
}

.details-header p {
  margin: 0;
  font-size: 1.1rem;
  color: #64748b;
}

.professional-layout {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Information Sections */
.info-section {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  transition: all 0.3s ease;
  border-left: none;
}

.info-section:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.framework-section {
  border-left: none;
}

/* Compliance Section Styles */
.compliance-section {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.compliance-section .section-title h5 {
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1.1rem;
  font-weight: 600;
}

.compliance-grid {
  display: grid;
  gap: 1rem;
}

.compliance-item {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  border: 1px solid #e5e7eb;
}

.compliance-header h6 {
  margin: 0 0 0.5rem 0;
  color: #6b7280;
  font-size: 0.9rem;
  font-weight: 600;
}

.compliance-textarea {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 0.75rem;
  font-size: 0.9rem;
  resize: vertical;
  min-height: 80px;
}

.compliance-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Related Controls Display */
.related-controls-display {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.control-tag {
  background: #667eea;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
}

.upload-framework .policy-section {
  border-left: none;
}

.sub-policy-section {
  border-left: none;
}

.section-title {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title h4 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.section-title h4 i {
  color: #667eea;
}

.section-badge {
  background: #e2e8f0;
  color: #64748b;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Form Grid Layout */
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  padding: 2rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field.full-width {
  grid-column: 1 / -1;
}

.form-field label {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-field input,
.form-field textarea,
.form-field select {
  width: 100%;
  padding: 0.875rem 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.95rem;
  transition: all 0.2s ease;
  background: #fafafa;
}

.form-field input:focus,
.form-field textarea:focus,
.form-field select:focus {
  outline: none;
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-field textarea {
  min-height: 100px;
  resize: vertical;
}

/* File Upload Styling */
.file-upload-wrapper {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.file-upload-wrapper input[type="file"] {
  display: none;
}

.file-upload-label {
  background: #667eea;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.file-upload-label:hover {
  background: #5a67d8;
  transform: translateY(-1px);
}

.file-name {
  color: #10b981;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  background: #f0fdf4;
  border-radius: 6px;
}

/* Policy Management Container */
.upload-framework .policy-management-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

/* Enhanced Compliance Management */
.compliance-management-section {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
  margin-top: 1.5rem;
  border-left: none;
}

.compliance-header {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  padding: 1.5rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.compliance-title {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.compliance-title h4 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.upload-framework .policy-ref {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.compliance-stats {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.compliance-count {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
}

.add-compliance-btn {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.add-compliance-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

/* Compliance Grid - Enhanced Width */
.compliance-grid {
  padding: 2rem;
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
  max-width: none;
}

.compliance-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  width: 100%;
  max-width: none;
}

.compliance-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.compliance-card-header {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.compliance-identifier {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.compliance-letter {
  background: #8b5cf6;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.9rem;
}

.compliance-number {
  font-weight: 600;
  color: #1e293b;
  font-size: 1rem;
}

.compliance-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.status-in-progress {
  background: #dbeafe;
  color: #1e40af;
}

.status-completed {
  background: #d1fae5;
  color: #065f46;
}

.status-not-applicable {
  background: #fee2e2;
  color: #991b1b;
}

.remove-compliance-btn {
  background: #ef4444;
  color: white;
  border: none;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  font-size: 0.75rem;
}

.remove-compliance-btn:hover {
  background: #dc2626;
  transform: scale(1.1);
}

/* Compliance Form Grid - Full Width */
.compliance-form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  padding: 1.5rem;
  width: 100%;
}

.compliance-form-grid .form-field.full-width {
  grid-column: 1 / -1;
}

/* Compliance Table Styles */
.compliance-table-container {
  width: 100%;
  overflow-x: auto;
  margin-top: 1rem;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.compliance-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.compliance-table thead {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 2px solid #e2e8f0;
}

.compliance-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-right: 1px solid #e2e8f0;
}

.compliance-table th:last-child {
  border-right: none;
}

.compliance-table tbody tr {
  border-bottom: 1px solid #f1f5f9;
  transition: background-color 0.2s ease;
}

.compliance-table tbody tr:hover {
  background-color: #f8fafc;
}

.compliance-table td {
  padding: 1rem;
  vertical-align: top;
  border-right: 1px solid #f1f5f9;
}

.compliance-table td:last-child {
  border-right: none;
}

.section-cell {
  font-weight: 600;
  color: #1f2937;
  min-width: 120px;
}

.order-cell {
  text-align: center;
  color: #6b7280;
  min-width: 80px;
}

.control-cell {
  max-width: 300px;
  word-wrap: break-word;
  color: #374151;
  line-height: 1.5;
  font-size: 0.85rem;
}

.compliance-cell {
  min-width: 200px;
}

.compliance-cell .compliance-textarea {
  width: 100%;
  min-height: 60px;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.85rem;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s ease;
}

.compliance-cell .compliance-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.status-select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.5em 1.5em;
  padding-right: 2.5rem;
}

/* Global Actions */
.global-actions {
  display: flex;
  justify-content: center;
  gap: 1.5rem;
  margin-top: 3rem;
  padding: 2rem;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 16px;
  border: 2px dashed #cbd5e1;
}

.save-btn.primary {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.save-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
}

.reset-btn.secondary {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(100, 116, 139, 0.3);
}

.reset-btn.secondary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(100, 116, 139, 0.4);
}

/* Status Messages */
.status-message {
  margin-top: 2rem;
  padding: 1.5rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1rem;
  font-weight: 500;
  font-size: 1rem;
}

.status-message.success {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
  color: #065f46;
  border: 2px solid #10b981;
}

.status-message.error {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #991b1b;
  border: 2px solid #ef4444;
}

/* Global Success Notification */
.global-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  max-width: 400px;
  z-index: 2000;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.global-notification.success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-left: none;
}

.notification-content {
  display: flex;
  align-items: flex-start;
  padding: 1rem;
  color: white;
}

.notification-content i {
  font-size: 1.2rem;
  margin-right: 0.75rem;
  margin-top: 0.2rem;
}

.notification-message {
  flex: 1;
  font-size: 0.95rem;
  white-space: pre-line;
}

.notification-close {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  padding: 0.25rem;
  font-size: 1rem;
  transition: all 0.2s ease;
}

.notification-close:hover {
  color: white;
  transform: scale(1.1);
}

/* Congratulations Modal */
.congratulations-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(8px);
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.congratulations-container {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 20px;
  width: 90%;
  max-width: 600px;
  padding: 3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3);
  animation: scaleIn 0.5s ease-out;
}

@keyframes scaleIn {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.congratulations-header {
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.congratulations-icon-container {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
  color: white;
  font-size: 48px;
  box-shadow: 0 20px 40px rgba(16, 185, 129, 0.3);
  animation: successPulse 2s ease-in-out infinite;
}

.congratulations-header h2 {
  color: #10b981;
  margin-bottom: 1rem;
  font-weight: 700;
  font-size: 2.5rem;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.congratulations-message {
  color: #374151;
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
}

.congratulations-content {
  margin-bottom: 2rem;
}

.congratulations-content p {
  color: #6b7280;
  font-size: 1.1rem;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.congratulations-actions {
  margin-top: 1rem;
}

.ok-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 1rem 2rem;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.ok-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
}

/* Content Viewer Section (Inline) */
.content-viewer-section {
  background: transparent;
  border-radius: 0;
  box-shadow: none;
  overflow: visible;
  margin-top: 0;
  padding: 0;
}

/* Content Viewer Modal */
.content-viewer-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.content-viewer-container {
  background-color: white;
  border-radius: 20px;
  width: 90%;
  max-width: 1200px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.content-viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 0;
  border-bottom: 2px solid #e2e8f0;
  background: transparent;
  margin-bottom: 2rem;
}

.content-viewer-actions {
  display: flex;
  gap: 1rem;
}

.content-viewer-header h3 {
  margin: 0;
  color: #1e293b;
  font-weight: 700;
  font-size: 1.5rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #64748b;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: #e2e8f0;
  color: #1e293b;
  transform: scale(1.1);
}

.content-viewer-body {
  flex-grow: 1;
  overflow-y: visible;
  padding: 0;
  max-height: none;
}

/* View Options Wrapper - uses CustomDropdown component */
.view-options-wrapper {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  flex-wrap: wrap;
}

.dropdown-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 200px;
  flex: 1;
}

.dropdown-field .dropdown-external-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0;
}

.view-mode-select,
.filter-type-select {
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
  background: white;
  color: #374151;
  cursor: pointer;
  transition: all 0.3s ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 0.5rem center;
  background-repeat: no-repeat;
  background-size: 1.5em 1.5em;
  padding-right: 2.5rem;
}

.view-mode-select:focus,
.filter-type-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.view-mode-select:hover,
.filter-type-select:hover {
  border-color: #cbd5e1;
}

.section-list {
  max-height: none;
  overflow-y: visible;
  border-radius: 0;
  border: none;
}

.section-item {
  border-bottom: 1px solid #e2e8f0;
}

.section-item:last-child {
  border-bottom: none;
}

.section-header {
  padding: 1.5rem 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background-color: transparent;
  transition: all 0.3s ease;
  border-bottom: 1px solid #e2e8f0;
}

.section-header:hover {
  background-color: transparent;
}

.section-checkbox {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-weight: 600;
  color: #1e293b;
}

.section-checkbox input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: #667eea;
}

.section-content {
  padding: 1rem 0 1.5rem 2rem;
  background-color: transparent;
}

.subsection-item {
  padding: 1rem 0;
  margin-bottom: 0.5rem;
  border-radius: 0;
  transition: all 0.3s ease;
  border-bottom: 1px solid #f1f5f9;
}

.subsection-item:hover {
  background-color: transparent;
}

  .subsection-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .subsection-checkbox {
    display: flex;
    align-items: center;
    gap: 1rem;
    color: #475569;
    font-weight: 500;
    flex: 1;
  }

  .subsection-actions {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .ai-analysis-toggle-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    font-size: 0.75rem;
    color: #6366f1;
    background: #eef2ff;
    border: 1px solid #c7d2fe;
    border-radius: 6px;
    cursor: pointer;
  }
  .ai-analysis-toggle-btn:hover {
    background: #e0e7ff;
    color: #4f46e5;
  }
  .ai-analysis-toggle-btn.step6 { margin-left: auto; }
  .ai-analysis-toggle-btn.small { padding: 2px 8px; font-size: 0.7rem; }

  .upload-ai-analysis-block {
    margin-top: 10px;
    padding: 12px 14px;
    background: #f0fdf4;
    border-left: 4px solid #10b981;
    border-radius: 8px;
    font-size: 0.85rem;
  }
  .upload-ai-analysis-block.subpolicy-ai-analysis {
    background: #eef2ff;
    border-left-color: #6366f1;
  }
  .upload-ai-analysis-header {
    font-weight: 600;
    color: #334155;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .upload-ai-analysis-header i { color: #10b981; }
  .subpolicy-ai-analysis .upload-ai-analysis-header i { color: #6366f1; }
  .upload-ai-analysis-row {
    margin-bottom: 10px;
  }
  .upload-ai-analysis-row:last-child { margin-bottom: 0; }
  .upload-ai-analysis-label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    color: #475569;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.02em;
  }
  .upload-ai-analysis-text { margin: 0; line-height: 1.45; color: #334155; font-size: 0.85rem; }
  .upload-ai-analysis-excerpt { margin: 0; font-size: 0.8rem; color: #64748b; line-height: 1.4; }

  .subsection-arrow {
    color: #64748b;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .subsection-arrow:hover {
    color: #475569;
  }

  .subpolicy-count {
    color: #64748b;
    font-size: 0.875rem;
    margin-left: 0.5rem;
  }

  .pdf-view-btn {
    background: #dc2626;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
  }

  .pdf-view-btn:hover {
    background: #b91c1c;
    transform: scale(1.1);
  }

  .pdf-view-btn i {
    font-size: 0.875rem;
  }

  .pdf-view-btn.active {
    background: #059669;
  }

  .pdf-view-btn.active:hover {
    background: #047857;
  }

  .pdf-status {
    font-size: 0.7rem;
    margin-left: 0.25rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .pdf-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    text-align: center;
    color: #dc2626;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
    margin: 1rem;
  }

  .pdf-error i {
    font-size: 2rem;
    margin-bottom: 1rem;
    color: #dc2626;
  }

  .pdf-error p {
    margin: 0 0 1rem 0;
    font-weight: 500;
  }

  .retry-btn {
    background: #dc2626;
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.875rem;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.3s ease;
  }

  .retry-btn:hover {
    background: #b91c1c;
    transform: translateY(-1px);
  }

/* Subpolicy Styles */
.subpolicy-content {
  margin-left: 2rem;
  margin-top: 0.5rem;
  padding-left: 1rem;
  border-left: none;
}

.subpolicy-item {
  padding: 0.75rem 0;
  margin-bottom: 0.25rem;
  border-bottom: 1px solid #f1f5f9;
}

.subpolicy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.subpolicy-checkbox {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #64748b;
  font-weight: 400;
  flex: 1;
}

.subpolicy-title {
  font-size: 0.9rem;
  color: #475569;
}

.subpolicy-id {
  color: #94a3b8;
  font-size: 0.8rem;
}

.subpolicy-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.subpolicy-content .subpolicy-content {
  margin-left: 0;
  padding-left: 0;
  border-left: none;
  color: #64748b;
  font-size: 0.85rem;
  line-height: 1.5;
}

/* Enhanced Subpolicy Styles */
.subpolicy-control-hint {
  background: #10b981;
  color: white;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-left: 0.5rem;
}

.details-btn {
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
}

.details-btn:hover {
  background: #2563eb;
  transform: scale(1.1);
}

.details-btn i {
  font-size: 0.75rem;
}

.subpolicy-details {
  margin-top: 0.75rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  margin-left: 1.5rem;
}

.subpolicy-description,
.subpolicy-control,
.subpolicy-content-text {
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #374151;
}

.subpolicy-description:last-child,
.subpolicy-control:last-child,
.subpolicy-content-text:last-child {
  margin-bottom: 0;
}

.subpolicy-description strong,
.subpolicy-control strong,
.subpolicy-content-text strong {
  color: #1f2937;
  font-weight: 600;
}

.pdf-view-btn.small {
  width: 28px;
  height: 28px;
  font-size: 0.75rem;
}

/* Inline PDF Viewer */
  .pdf-viewer-container {
    margin-top: 1rem;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    overflow: hidden;
    background: white;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .pdf-viewer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.5rem;
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    border-bottom: 1px solid #e2e8f0;
  }

  .pdf-title {
    font-weight: 600;
    color: #1e293b;
    font-size: 0.95rem;
  }

  .close-pdf-btn {
    background: none;
    border: none;
    color: #64748b;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 6px;
    transition: all 0.3s ease;
  }

  .close-pdf-btn:hover {
    background: #e2e8f0;
    color: #1e293b;
  }

  .pdf-viewer-body {
    height: 500px;
    overflow: hidden;
  }

  .pdf-iframe {
    width: 100%;
    height: 100%;
    border: none;
  }

.subsection-checkbox input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #667eea;
}

.content-viewer-footer {
  padding: 2rem;
  border-top: 2px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

/* Select All uses .btn-select-all, Deselect All uses .btn-deselect-all, Save Selection uses .btn-submit, and Continue uses .btn-continue from main.css */

/* Policy Extractor Modal */
.upload-framework .policy-extractor-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
}

.upload-framework .policy-extractor-container {
  background-color: white;
  border-radius: 20px;
  width: 95%;
  max-width: 1400px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.upload-framework .policy-extractor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem;
  border-bottom: 2px solid #e2e8f0;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.upload-framework .policy-extractor-header h3 {
  margin: 0;
  color: #1e293b;
  font-weight: 700;
  font-size: 1.5rem;
}

.upload-framework .policy-extractor-body {
  flex-grow: 1;
  overflow: hidden;
  padding: 2rem;
}

.upload-framework .policy-table-container {
  height: 100%;
  overflow: auto;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
}

.upload-framework .policy-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.upload-framework .policy-table th {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 1rem;
  position: sticky;
  top: 0;
  z-index: 10;
}

.upload-framework .policy-table td {
  padding: 1.5rem 1rem;
  border-bottom: 1px solid #e2e8f0;
  color: #475569;
  font-size: 0.95rem;
  line-height: 1.5;
  max-width: 300px;
  word-wrap: break-word;
  vertical-align: top;
}

.upload-framework .policy-table tr:hover {
  background-color: #f8fafc;
}

.upload-framework .policy-table tr:nth-child(even) {
  background-color: #fafbfc;
}

.upload-framework .policy-table tr:nth-child(even):hover {
  background-color: #f1f5f9;
}

.upload-framework .policy-table tr.expanded-row {
  background-color: #f1f5f9;
}

.control-cell {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.actions-cell {
  display: flex;
  gap: 0.5rem;
}

.view-btn, .edit-btn, .save-all-btn {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  font-size: 0.875rem;
  border: none;
}

.view-btn {
  background: #f8fafc;
  color: #1e293b;
  border: 1px solid #e2e8f0;
}

.view-btn:hover {
  background: #f1f5f9;
  transform: translateY(-1px);
}

.edit-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.edit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.save-all-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
  margin-right: 1rem;
}

.save-all-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.upload-framework .policy-actions {
  display: flex;
  align-items: center;
}

/* Detail row styling */
.detail-row {
  background-color: #f8fafc;
}

.upload-framework .policy-details-container {
  padding: 1.5rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.upload-framework .policy-details-section {
  margin-bottom: 1rem;
}

.upload-framework .policy-details-section h4 {
  font-size: 0.875rem;
  color: #64748b;
  margin-bottom: 0.5rem;
  font-weight: 600;
  text-transform: uppercase;
}

.detail-content {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
  font-size: 0.875rem;
  color: #334155;
}

.upload-framework .policy-details-section .control-content {
  grid-column: 1 / -1;
  white-space: pre-line;
}

.control-content ul {
  margin: 0;
  padding-left: 1.5rem;
}

.control-content li {
  margin-bottom: 0.5rem;
}

/* No policies message */
.no-policies-message {
  padding: 3rem;
  text-align: center;
  color: #64748b;
  background: #f8fafc;
  border-radius: 12px;
  border: 2px dashed #e2e8f0;
}

.no-policies-message p {
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
}

/* Policy Edit Modal */
.upload-framework .policy-edit-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
  backdrop-filter: blur(8px);
}

.upload-framework .policy-edit-container {
  background-color: white;
  border-radius: 20px;
  width: 90%;
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.upload-framework .policy-edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 2px solid #e2e8f0;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.upload-framework .policy-edit-header h3 {
  margin: 0;
  color: #1e293b;
  font-weight: 700;
  font-size: 1.5rem;
}

.upload-framework .policy-edit-actions {
  display: flex;
  gap: 1rem;
}

.upload-framework .policy-edit-body {
  padding: 2rem;
  overflow-y: auto;
  max-height: calc(90vh - 90px);
}

.upload-framework .policy-field {
  margin-bottom: 1.5rem;
}

.upload-framework .policy-field label {
  display: block;
  color: #64748b;
  font-weight: 600;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.upload-framework .policy-field input,
.upload-framework .policy-field textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.upload-framework .policy-field input:focus,
.upload-framework .policy-field textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Responsive Design */
@media (max-width: 1200px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
  
  .compliance-form-grid {
    grid-template-columns: 1fr;
  }
  
  .compliance-table-container {
    overflow-x: auto;
  }
  
  .compliance-table {
    min-width: 600px;
  }
}

@media (max-width: 768px) {
  .upload-framework-container {
    padding: 1rem;
    margin-left: 0 !important;
  }
  
  .step-indicator {
    flex-direction: column;
    gap: 1rem;
  }
  
  .step-divider {
    width: 2px;
    height: 40px;
    margin: 0;
    margin-top: 0 !important; /* Reset margin-top for vertical layout */
    align-self: center !important; /* Center horizontally in vertical layout */
  }
  
  .header h1 {
    font-size: 2rem;
  }
  
  .upload-section {
    padding: 2rem 1.5rem;
  }
  
  .processing-details,
  .extraction-details {
    flex-direction: column;
    gap: 1rem;
  }
  
  .completion-actions,
  .review-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .content-viewer-footer {
    flex-direction: column;
  }
  
  .view-options-wrapper {
    flex-direction: column;
    gap: 1rem;
  }
  
  .dropdown-field {
    min-width: 100%;
  }
  
  .upload-framework .policy-table {
    font-size: 0.875rem;
  }
  
  .upload-framework .policy-table th,
  .upload-framework .policy-table td {
    padding: 1rem 0.5rem;
  }
  
  .compliance-header {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
    gap: 1rem;
  }
  
  .compliance-stats {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .add-compliance-btn {
    width: 100%;
    justify-content: center;
  }
  
  .global-actions {
    flex-direction: column;
    gap: 1rem;
  }
  
  .save-btn.primary,
  .reset-btn.secondary {
    width: 100%;
  }
  
  .file-upload-wrapper {
    flex-direction: column;
    align-items: stretch;
  }
  
  .compliance-card-header {
    flex-direction: column;
    text-align: center;
    gap: 0.5rem;
  }
  
  .compliance-table-container {
    margin: 0.5rem 0;
  }
  
  .compliance-table {
    font-size: 0.8rem;
    min-width: 500px;
  }
  
  .compliance-table th,
  .compliance-table td {
    padding: 0.5rem;
  }
  
  .control-cell {
    max-width: 200px;
    font-size: 0.75rem;
  }
  
  .compliance-cell .compliance-textarea {
    min-height: 50px;
    padding: 0.5rem;
    font-size: 0.75rem;
  }
  
  .compliance-identifier {
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .details-header h3 {
    font-size: 1.5rem;
  }
  
  .section-title {
    padding: 1rem 1.5rem;
  }
  
  .section-title h4 {
    font-size: 1rem;
  }
  
  .form-grid {
    padding: 1.5rem;
  }
  
  .compliance-grid {
    padding: 1.5rem;
  }
  
  .compliance-form-grid {
    padding: 1rem;
  }
}
/* Enhanced Processing Animations */
.processing-animation-container {
display: flex;
justify-content: center;
margin-bottom: 2rem;
}

.document-processing-visual {
position: relative;
width: 120px;
height: 120px;
display: flex;
align-items: center;
justify-content: center;
}

.document-icon {
position: relative;
z-index: 10;
background: #f8fafc;
border-radius: 50%;
width: 60px;
height: 60px;
display: flex;
align-items: center;
justify-content: center;
box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.document-icon i {
font-size: 2rem;
color: #475569;
}

.processing-waves {
position: absolute;
top: 0;
left: 0;
width: 100%;
height: 100%;
}

.wave {
position: absolute;
border: 2px solid #e2e8f0;
border-radius: 50%;
animation: wave-pulse 2s ease-in-out infinite;
}

.wave-1 {
width: 80px;
height: 80px;
top: 20px;
left: 20px;
animation-delay: 0s;
}

.wave-2 {
width: 100px;
height: 100px;
top: 10px;
left: 10px;
animation-delay: 0.5s;
}

.wave-3 {
width: 120px;
height: 120px;
top: 0;
left: 0;
animation-delay: 1s;
}

@keyframes wave-pulse {
0% {
  transform: scale(0.8);
  opacity: 1;
  border-color: #cbd5e1;
}
50% {
  transform: scale(1);
  opacity: 0.7;
  border-color: #94a3b8;
}
100% {
  transform: scale(1.2);
  opacity: 0;
  border-color: #64748b;
}
}

.extraction-particles {
position: absolute;
width: 100%;
height: 100%;
}

.particle {
position: absolute;
width: 4px;
height: 4px;
background: #64748b;
border-radius: 50%;
animation: particle-float 3s ease-in-out infinite;
}

.particle:nth-child(1) { top: 10%; left: 20%; animation-delay: 0s; }
.particle:nth-child(2) { top: 30%; right: 15%; animation-delay: 0.5s; }
.particle:nth-child(3) { bottom: 20%; left: 25%; animation-delay: 1s; }
.particle:nth-child(4) { bottom: 35%; right: 20%; animation-delay: 1.5s; }
.particle:nth-child(5) { top: 60%; left: 10%; animation-delay: 2s; }
.particle:nth-child(6) { top: 50%; right: 10%; animation-delay: 2.5s; }

@keyframes particle-float {
0%, 100% {
  transform: translateY(0) scale(1);
  opacity: 0.6;
}
50% {
  transform: translateY(-20px) scale(1.2);
  opacity: 1;
}
}

.processing-details-enhanced {
text-align: center;
max-width: 600px;
margin: 0 auto;
}

.main-status {
font-size: 1.1rem;
color: #475569;
margin-bottom: 1.5rem;
}

.document-info {
display: flex;
align-items: center;
justify-content: center;
gap: 0.75rem;
margin-bottom: 2rem;
padding: 1rem;
background: #f8fafc;
border-radius: 8px;
color: #64748b;
}

.processing-stages {
display: flex;
justify-content: center;
gap: 1.5rem;
flex-wrap: wrap;
margin: 2rem 0;
}

.stage {
display: flex;
flex-direction: column;
align-items: center;
gap: 0.75rem;
opacity: 0.3;
transition: all 0.4s ease;
padding: 1rem;
border-radius: 8px;
min-width: 120px;
}

.stage.active {
opacity: 1;
transform: translateY(-2px);
background: rgba(102, 126, 234, 0.1);
box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.stage-dot {
width: 16px;
height: 16px;
border-radius: 50%;
background: #cbd5e1;
transition: all 0.4s ease;
position: relative;
}

.stage.active .stage-dot {
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
transform: scale(1.3);
box-shadow: 0 0 15px rgba(102, 126, 234, 0.4);
}

.stage.active .stage-dot::after {
content: '';
position: absolute;
top: 50%;
left: 50%;
transform: translate(-50%, -50%);
width: 6px;
height: 6px;
background: white;
border-radius: 50%;
}

.stage span {
font-size: 0.875rem;
color: #64748b;
font-weight: 500;
text-align: center;
line-height: 1.2;
}

.stage.active span {
color: #1e293b;
font-weight: 600;
}

/* AI Extraction Animations */
.ai-extraction-container {
display: flex;
justify-content: center;
margin-bottom: 2rem;
}

.ai-brain-visual {
position: relative;
width: 140px;
height: 140px;
display: flex;
align-items: center;
justify-content: center;
}

.brain-core {
position: relative;
z-index: 10;
background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
border-radius: 50%;
width: 70px;
height: 70px;
display: flex;
align-items: center;
justify-content: center;
box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
animation: brain-pulse 2s ease-in-out infinite;
}

.brain-core i {
font-size: 2.5rem;
color: #64748b;
}

@keyframes brain-pulse {
0%, 100% {
  transform: scale(1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}
50% {
  transform: scale(1.05);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.15);
}
}

.neural-network {
position: absolute;
width: 100%;
height: 100%;
}

.neuron {
position: absolute;
width: 6px;
height: 6px;
background: #94a3b8;
border-radius: 50%;
animation: neuron-pulse 2s ease-in-out infinite;
}

.neuron:nth-child(1) { top: 15%; left: 30%; animation-delay: 0s; }
.neuron:nth-child(2) { top: 25%; right: 20%; animation-delay: 0.25s; }
.neuron:nth-child(3) { top: 45%; left: 15%; animation-delay: 0.5s; }
.neuron:nth-child(4) { top: 55%; right: 25%; animation-delay: 0.75s; }
.neuron:nth-child(5) { bottom: 25%; left: 25%; animation-delay: 1s; }
.neuron:nth-child(6) { bottom: 35%; right: 15%; animation-delay: 1.25s; }
.neuron:nth-child(7) { bottom: 15%; left: 40%; animation-delay: 1.5s; }
.neuron:nth-child(8) { top: 35%; left: 50%; animation-delay: 1.75s; }

@keyframes neuron-pulse {
0%, 100% {
  transform: scale(1);
  opacity: 0.6;
}
50% {
  transform: scale(1.5);
  opacity: 1;
}
}

.data-flow {
position: absolute;
width: 100%;
height: 100%;
}

.data-bit {
position: absolute;
width: 3px;
height: 3px;
background: #64748b;
border-radius: 50%;
animation: data-flow-animation 4s linear infinite;
}

.data-bit:nth-child(odd) {
animation-direction: normal;
}

.data-bit:nth-child(even) {
animation-direction: reverse;
}

@keyframes data-flow-animation {
0% {
  transform: rotate(0deg) translateX(60px) rotate(0deg);
  opacity: 0;
}
25% {
  opacity: 1;
}
75% {
  opacity: 1;
}
100% {
  transform: rotate(360deg) translateX(60px) rotate(-360deg);
  opacity: 0;
}
}

.ai-processing-details {
text-align: center;
max-width: 700px;
margin: 0 auto;
}

.ai-stages {
display: flex;
justify-content: center;
gap: 2rem;
flex-wrap: wrap;
margin-top: 2rem;
}

.ai-stage {
display: flex;
flex-direction: column;
align-items: center;
gap: 0.75rem;
opacity: 0.3;
transition: all 0.3s ease;
padding: 1rem;
border-radius: 8px;
}

.ai-stage.active {
opacity: 1;
background: #f8fafc;
transform: translateY(-2px);
}

.ai-stage-icon {
width: 40px;
height: 40px;
border-radius: 50%;
background: #e2e8f0;
display: flex;
align-items: center;
justify-content: center;
transition: all 0.3s ease;
}

.ai-stage.active .ai-stage-icon {
background: #64748b;
color: white;
transform: scale(1.1);
}

.ai-stage span {
font-size: 0.875rem;
color: #64748b;
font-weight: 500;
text-align: center;
}

/* Responsive Design */
@media (max-width: 768px) {
  .processing-stages,
  .ai-stages {
    gap: 1rem;
  }
  
  .stage,
  .ai-stage {
    min-width: 80px;
    padding: 0.75rem;
  }
  
  .stage span,
  .ai-stage span {
    font-size: 0.8rem;
  }
  
  .document-processing-visual,
  .ai-brain-visual {
    width: 100px;
    height: 100px;
  }
  
  .document-icon {
    width: 50px;
    height: 50px;
  }
  
  .brain-core {
    width: 60px;
    height: 60px;
  }
  
  .progress-container {
    padding: 1.5rem;
  }
  
  .progress-header {
    flex-direction: column;
    gap: 0.5rem;
    text-align: center;
  }
  
  .progress-stats {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .time-info {
    padding: 1rem;
  }
  
  .time-display,
  .time-estimate {
    font-size: 0.9rem;
  }
}
/* Current Section Indicator */
.current-section {
margin: 1.5rem 0;
padding: 1rem;
background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
border-radius: 8px;
border-left: none;
}

.section-indicator {
display: flex;
align-items: center;
gap: 0.75rem;
color: #475569;
font-weight: 500;
}

.section-indicator i {
color: #64748b;
}

/* Time Information Styles */
.time-info {
margin-top: 2rem;
padding: 1.5rem;
background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
border-radius: 12px;
border: 1px solid #e2e8f0;
}

.time-display, .time-estimate {
display: flex;
align-items: center;
gap: 0.75rem;
margin-bottom: 0.75rem;
color: #475569;
font-weight: 500;
}

.time-display:last-child, .time-estimate:last-child {
margin-bottom: 0;
}

.time-display i, .time-estimate i {
color: #667eea;
font-size: 1.1rem;
}

.time-display span, .time-estimate span {
font-size: 0.95rem;
}

.time-estimate {
color: #059669;
}

.time-estimate i {
color: #059669;
}

/* Processing Activity Indicator */
.processing-activity {
margin-top: 2rem;
display: flex;
align-items: center;
justify-content: center;
gap: 1rem;
color: #64748b;
font-size: 0.9rem;
}

.activity-dots {
display: flex;
gap: 0.25rem;
}

.activity-dots .dot {
width: 6px;
height: 6px;
background: #64748b;
border-radius: 50%;
animation: activity-pulse 1.5s ease-in-out infinite;
}

.activity-dots .dot:nth-child(1) {
animation-delay: 0s;
}

.activity-dots .dot:nth-child(2) {
animation-delay: 0.3s;
}

.activity-dots .dot:nth-child(3) {
animation-delay: 0.6s;
}

@keyframes activity-pulse {
0%, 100% {
  transform: scale(1);
  opacity: 0.5;
}
50% {
  transform: scale(1.2);
  opacity: 1;
}
}

/* Enhanced stage indicators */
.stage.active {
opacity: 1;
transform: translateY(-2px);
}

.stage.active .stage-dot {
background: #64748b;
transform: scale(1.2);
box-shadow: 0 0 10px rgba(100, 116, 139, 0.3);
}

/* Additional styles for content viewer */
.subsection-title {
  font-weight: 500;
  color: #475569;
}

.control-id {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 400;
}

.subsection-content {
  margin-left: 1.5rem;
  padding: 0.5rem 0;
  background-color: transparent;
  border-radius: 0;
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.5;
  border-left: none;
}

.subsection-count {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 400;
  margin-left: 0.5rem;
}

.expand-hint {
  color: #667eea;
  font-size: 0.75rem;
  font-style: italic;
  margin-left: 1rem;
  opacity: 0.8;
}

.content-instructions {
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 1rem 0;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.content-instructions p {
  margin: 0;
  color: #475569;
  font-size: 0.9rem;
  line-height: 1.4;
}

.content-instructions i {
  color: #667eea;
  margin-right: 0.5rem;
}

/* Step 6 Vertical Layout Styles */
.vertical-edit-container {
  padding: 1.5rem;
  background: #f5f7fa;
  max-width: 100%;
}

/* Level Section - Each hierarchy level gets its own card (no left border) */
.level-section {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid #e5e7eb;
  border-left: none;
  transition: all 0.3s ease;
}

.level-section:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

/* Level sections – no left border */
.framework-level {
  border-left: none;
  background: white;
}

.upload-framework .policy-level {
  border-left: none;
  background: white;
}

.subpolicy-level {
  border-left: none;
  background: white;
  margin-left: 2rem;
}

.compliance-level {
  border-left: none;
  background: white;
  margin-left: 4rem;
}

/* Level Headers */
.level-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e5e7eb;
}

.level-header h3,
.level-header h4,
.level-header h5,
.level-header h6 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
}

.level-header h3 {
  color: #1e293b;
  font-size: 1.5rem;
}

.level-header h4 {
  color: #1e293b;
  font-size: 1.3rem;
}

.level-header h5 {
  color: #1e293b;
  font-size: 1.1rem;
}

.level-header h6 {
  color: #1e293b;
  font-size: 1rem;
}

/* Vertical Form - Full width, stacked fields */
.vertical-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.v-form-row {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.v-form-row label {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #374151;
  font-size: 0.95rem;
}

.v-form-row input,
.v-form-row textarea,
.v-form-row select {
  width: 100%;
  padding: 0.625rem 0.875rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  font-size: 0.8125rem;
  font-family: inherit;
  color: #4b5563;
  transition: all 0.2s ease;
  background: #ffffff;
}

.v-form-row input:focus,
.v-form-row textarea:focus,
.v-form-row select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.v-form-row textarea {
  resize: vertical;
  min-height: 80px;
}

/* Section Divider for vertical layout (neutral) */
.section-divider-vertical {
  background: #f1f5f9;
  color: #1e293b;
  padding: 1.25rem 1.5rem;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  margin: 2rem 0 1.5rem 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.section-divider-vertical h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 1.4rem;
  font-weight: 600;
}

/* Badges */
.v-badge {
  background: #3b82f6;
  color: white;
  padding: 0.4rem 0.9rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}

.v-badge-small {
  padding: 0.3rem 0.7rem;
  font-size: 0.75rem;
}

.v-criticality-badge {
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.v-criticality-badge.v-low {
  background: #10b981;
}

.v-criticality-badge.v-medium {
  background: #f59e0b;
}

.v-criticality-badge.v-high {
  background: #ef4444;
}

.v-criticality-badge.v-critical {
  background: #991b1b;
}

/* No Compliances Message */
.no-compliances-vertical {
  text-align: center;
  padding: 1.5rem;
  background: #fef3c7;
  border: 2px dashed #f59e0b;
  border-radius: 8px;
  margin: 1rem 0 1rem 4rem;
  color: #92400e;
}

.no-compliances-vertical p {
  margin: 0;
  font-weight: 500;
}

.no-compliances-vertical i {
  margin-right: 0.5rem;
}

/* Save actions: layout only; button uses .btn-submit from main.css */
.save-actions {
  text-align: center;
  margin-top: 3rem;
}

.loading-container {
  text-align: center;
  padding: 4rem;
}

.loading-container i {
  font-size: 3rem;
  color: #667eea;
  margin-bottom: 1rem;
}
</style>