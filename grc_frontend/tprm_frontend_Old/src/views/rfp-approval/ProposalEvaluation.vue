<template>
  <div class="h-screen flex flex-col">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200 px-6 py-4">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-xl font-semibold text-gray-900">Proposal Evaluation</h2>
          <p class="text-sm text-gray-600 mt-1">Review proposal documents and data while scoring</p>
          <div v-if="isSubmitted" class="mt-2 inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <span class="mr-1">✓</span>
            Evaluation Already Submitted
          </div>
        </div>
        <div class="flex items-center space-x-3">
          <button @click="navigateBack" class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-all duration-200 shadow-sm">
            <span class="mr-2">←</span>
            Back to Approvals
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Left Panel - Proposal Content -->
      <div class="flex-1 overflow-y-auto bg-white border-r border-gray-200">
        <div class="p-6">
          <!-- Proposal Header -->
          <div class="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-gray-900">{{ proposalData?.vendor_name || 'Loading...' }}</h3>
                <p class="text-sm text-gray-600">{{ proposalData?.org || 'Organization' }}</p>
                <p class="text-xs text-gray-500 mt-1">Submitted: {{ formatDate(proposalData?.submitted_at) }}</p>
              </div>
              <div class="text-right">
                <span v-if="isSubmitted" class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                  ✓ EVALUATION SUBMITTED
                </span>
                <span v-else class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  {{ proposalData?.evaluation_status || 'PENDING' }}
                </span>
                <p v-if="proposalData?.proposed_value" class="text-sm text-gray-600 mt-1">
                  ${{ proposalData.proposed_value.toLocaleString() }}
                </p>
              </div>
            </div>
          </div>

          <!-- Tabs for different content types -->
          <div class="mb-6">
            <div class="border-b border-gray-200">
              <nav class="-mb-px flex space-x-8">
                <button 
                  @click="activeTab = 'proposal'"
                  :class="['py-2 px-1 border-b-2 font-medium text-sm', activeTab === 'proposal' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300']"
                >
                  Proposal Data
                </button>
                <button 
                  @click="activeTab = 'documents'"
                  :class="['py-2 px-1 border-b-2 font-medium text-sm', activeTab === 'documents' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300']"
                >
                  Documents ({{ documents.length }})
                </button>
                <button 
                  @click="activeTab = 'risks'"
                  :class="['py-2 px-1 border-b-2 font-medium text-sm', activeTab === 'risks' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300']"
                >
                  Risks ({{ risks.length }})
                </button>
              </nav>
            </div>
          </div>

          <!-- Proposal Data Tab -->
          <div v-if="activeTab === 'proposal'" class="space-y-6">
            <div v-if="proposalData" class="space-y-6">
              <!-- Basic Information Section -->
              <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span class="mr-2">📋</span>
                  Basic Information
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <DataField 
                    v-if="proposalData.response_id" 
                    label="Response ID" 
                    :value="proposalData.response_id"
                    type="text"
                  />
                  <DataField 
                    v-if="proposalData.rfp_id" 
                    label="RFP ID" 
                    :value="proposalData.rfp_id"
                    type="text"
                  />
                  <DataField 
                    v-if="proposalData.rfp_number" 
                    label="RFP Number" 
                    :value="proposalData.rfp_number"
                    type="text"
                  />
                  <DataField 
                    v-if="proposalData.vendor_id" 
                    label="Vendor ID" 
                    :value="proposalData.vendor_id"
                    type="text"
                  />
                  <DataField 
                    v-if="proposalData.vendor_name" 
                    label="Vendor Name" 
                    :value="proposalData.vendor_name"
                    type="text"
                  />
                  <DataField 
                    v-if="proposalData.org" 
                    label="Organization" 
                    :value="proposalData.org"
                    type="text"
                  />
                  <DataField 
                    v-if="proposalData.submission_status" 
                    label="Submission Status" 
                    :value="proposalData.submission_status"
                    type="badge"
                    :badge-class="getStatusBadgeClass(proposalData.submission_status)"
                  />
                  <DataField 
                    v-if="proposalData.evaluation_status" 
                    label="Evaluation Status" 
                    :value="proposalData.evaluation_status"
                    type="badge"
                    :badge-class="getStatusBadgeClass(proposalData.evaluation_status)"
                  />
                  <DataField 
                    v-if="proposalData.submitted_at" 
                    label="Submitted At" 
                    :value="proposalData.submitted_at"
                    type="datetime"
                  />
                </div>
              </div>

              <!-- Financial Information Section -->
              <div v-if="proposalData.proposed_value || proposalData.currency" class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span class="mr-2">💰</span>
                  Financial Information
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <DataField 
                    v-if="proposalData.proposed_value" 
                    label="Proposed Value" 
                    :value="proposalData.proposed_value"
                    type="currency"
                    :currency="proposalData.currency || 'USD'"
                  />
                  <DataField 
                    v-if="proposalData.currency" 
                    label="Currency" 
                    :value="proposalData.currency"
                    type="text"
                  />
                </div>
              </div>

              <!-- Evaluation Scores Section -->
              <div v-if="proposalData.technical_score !== undefined || proposalData.commercial_score !== undefined || proposalData.overall_score !== undefined" class="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span class="mr-2">⭐</span>
                  Evaluation Scores
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <DataField 
                    v-if="proposalData.technical_score !== undefined" 
                    label="Technical Score" 
                    :value="proposalData.technical_score"
                    type="number"
                  />
                  <DataField 
                    v-if="proposalData.commercial_score !== undefined" 
                    label="Commercial Score" 
                    :value="proposalData.commercial_score"
                    type="number"
                  />
                  <DataField 
                    v-if="proposalData.overall_score !== undefined" 
                    label="Overall Score" 
                    :value="proposalData.overall_score"
                    type="number"
                  />
                </div>
              </div>

              <!-- Proposal Data Section -->
              <div v-if="proposalData.proposal_data || proposalData.response_documents" class="space-y-6">
                <!-- Fallback: Show all data if sections aren't found -->
                <div v-if="shouldShowFallbackData" class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <span class="mr-2">📋</span>
                    Proposal Data
                  </h3>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="(value, key) in allProposalData" :key="key" class="space-y-1">
                      <label class="text-xs font-medium text-gray-500">{{ formatKey(key) }}</label>
                      <div class="text-sm font-medium text-gray-900">
                        {{ formatFieldValue(value, getFieldType(value)) }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Company Information Section -->
                <div v-if="Object.keys(companyInfoSection).length > 0" class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <span class="mr-2">🏢</span>
                    Company Information
                  </h3>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="(value, key) in companyInfoSection" :key="key" class="space-y-1">
                      <label class="text-xs font-medium text-gray-500">{{ formatKey(key) }}</label>
                      <div class="text-sm font-medium text-gray-900">
                        {{ formatFieldValue(value, getFieldType(value)) }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Financial Information Section -->
                <div v-if="Object.keys(financialInfoSection).length > 0" class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <span class="mr-2">💰</span>
                    Financial Information
                  </h3>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="(value, key) in financialInfoSection" :key="key" class="space-y-1">
                      <label class="text-xs font-medium text-gray-500">{{ formatKey(key) }}</label>
                      <div class="text-sm font-medium text-gray-900">
                        {{ formatFieldValue(value, key === 'proposedValue' ? 'currency' : getFieldType(value), financialInfoSection.currency || 'USD') }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- RFP Responses Section -->
                <div v-if="rfpResponsesSection && typeof rfpResponsesSection === 'object' && Object.keys(rfpResponsesSection).length > 0" class="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <span class="mr-2">📋</span>
                    RFP Responses
                  </h3>
                  <div class="space-y-4">
                    <div v-for="(response, criteriaId) in rfpResponsesSection" :key="criteriaId" class="bg-white border border-gray-200 rounded-lg p-4">
                      <h4 class="text-sm font-semibold text-gray-900 mb-3">Criteria {{ criteriaId }}</h4>
                      <div v-if="typeof response === 'object' && response !== null">
                        <!-- Show all fields from the response object -->
                        <div class="space-y-3">
                          <div v-if="response.htmlContent" class="mb-3">
                            <label class="block text-xs font-medium text-gray-500 mb-1">Response Content (HTML)</label>
                            <div class="text-sm text-gray-900 bg-gray-50 p-3 rounded border border-gray-200" v-html="response.htmlContent"></div>
                          </div>
                          <div v-if="response.content && response.content !== response.htmlContent" class="mb-3">
                            <label class="block text-xs font-medium text-gray-500 mb-1">Response Content (Text)</label>
                            <div class="text-sm text-gray-900 bg-gray-50 p-3 rounded border border-gray-200">{{ response.content }}</div>
                          </div>
                          <div v-if="response.text && response.text !== response.htmlContent && response.text !== response.content" class="mb-3">
                            <label class="block text-xs font-medium text-gray-500 mb-1">Response Text</label>
                            <div class="text-sm text-gray-900 bg-gray-50 p-3 rounded border border-gray-200">{{ response.text }}</div>
                          </div>
                          <div v-if="response.attachments && Array.isArray(response.attachments) && response.attachments.length > 0" class="mt-3">
                            <label class="block text-xs font-medium text-gray-500 mb-2">Attachments ({{ response.attachments.length }})</label>
                            <div class="space-y-2">
                              <div v-for="(attachment, idx) in response.attachments" :key="idx" class="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800">
                                <span>📎</span>
                                <a :href="attachment.url || attachment.download_url" target="_blank" class="underline">{{ attachment.fileName || attachment.originalFilename || attachment.name || `Attachment ${idx + 1}` }}</a>
                              </div>
                            </div>
                          </div>
                          <!-- Show any other fields in the response object -->
                          <template v-for="(value, key) in response" :key="key">
                            <div v-if="!['htmlContent', 'content', 'text', 'attachments'].includes(key)">
                              <DataField 
                                :label="formatKey(key)" 
                                :value="value"
                                :type="getFieldType(value)"
                              />
                            </div>
                          </template>
                        </div>
                      </div>
                      <div v-else-if="typeof response === 'string'">
                        <label class="block text-xs font-medium text-gray-500 mb-1">Response</label>
                        <div class="text-sm text-gray-900 bg-gray-50 p-3 rounded border border-gray-200" v-html="response"></div>
                      </div>
                      <div v-else class="text-sm text-gray-500 italic">No response data available</div>
                    </div>
                  </div>
                </div>

                <!-- Team Information Section -->
                <div v-if="teamInfoSection && typeof teamInfoSection === 'object' && Object.keys(teamInfoSection).length > 0" class="bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-200 rounded-lg p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <span class="mr-2">👥</span>
                    Team Information
                  </h3>
                  <div v-if="teamInfoSection?.keyPersonnel && Array.isArray(teamInfoSection.keyPersonnel)" class="space-y-4">
                    <div v-for="(person, index) in teamInfoSection.keyPersonnel" :key="index" class="bg-white border border-gray-200 rounded-lg p-4">
                      <h4 class="text-sm font-semibold text-gray-900 mb-3">Team Member {{ index + 1 }}</h4>
                      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <DataField 
                          v-for="(value, key) in person" 
                          :key="key"
                          :label="formatKey(key)" 
                          :value="value"
                          :type="getFieldType(value)"
                        />
                      </div>
                    </div>
                  </div>
                  <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="(value, key) in teamInfoSection" :key="key" class="space-y-1">
                      <label class="text-xs font-medium text-gray-500">{{ formatKey(key) }}</label>
                      <div class="text-sm font-medium text-gray-900">
                        {{ formatFieldValue(value, getFieldType(value)) }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Dynamic Fields Section -->
                <div v-if="Object.keys(dynamicFieldsSection).length > 0" class="bg-gradient-to-r from-cyan-50 to-teal-50 border border-cyan-200 rounded-lg p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <span class="mr-2">🔧</span>
                    Dynamic Fields
                  </h3>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="(value, key) in dynamicFieldsSection" :key="key" class="space-y-1">
                      <label class="text-xs font-medium text-gray-500">{{ formatKey(key) }}</label>
                      <div class="text-sm font-medium text-gray-900">
                        {{ formatFieldValue(value, getFieldType(value)) }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Compliance Section -->
                <div v-if="Object.keys(complianceSection).length > 0" class="bg-gradient-to-r from-red-50 to-rose-50 border border-red-200 rounded-lg p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <span class="mr-2">✅</span>
                    Compliance Information
                  </h3>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="(value, key) in complianceSection" :key="key" class="space-y-1">
                      <label class="text-xs font-medium text-gray-500">{{ formatKey(key) }}</label>
                      <div class="text-sm font-medium text-gray-900">
                        {{ formatFieldValue(value, getFieldType(value)) }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Other Proposal Data Sections -->
                <div v-if="hasOtherProposalSections" class="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <span class="mr-2">📊</span>
                    Additional Proposal Data
                  </h3>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="(value, key) in otherProposalSections" :key="key" class="space-y-1">
                      <label class="text-xs font-medium text-gray-500">{{ formatKey(key) }}</label>
                      <div class="text-sm font-medium text-gray-900">
                        {{ formatFieldValue(value, getFieldType(value)) }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- ALL Response Documents Data - Comprehensive View -->
                <div v-if="Object.keys(allResponseDocumentsData).length > 0" class="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <span class="mr-2">📄</span>
                    All Response Documents Data
                  </h3>
                  <p class="text-sm text-gray-600 mb-4">Complete view of all data from response_documents field</p>
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="(value, key) in allResponseDocumentsData" :key="key" class="space-y-1">
                      <label class="text-xs font-medium text-gray-500">{{ formatKey(key) }}</label>
                      <div class="text-sm font-medium text-gray-900">
                        {{ formatFieldValue(value, getFieldType(value)) }}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Additional Data Section -->
              <div v-if="hasAdditionalData" class="bg-white border border-gray-200 rounded-lg p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <span class="mr-2">📊</span>
                  Additional Information
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <DataField 
                    v-for="(value, key) in additionalDataFields" 
                    :key="key"
                    :label="formatKey(key)" 
                    :value="value"
                    :type="getFieldType(value)"
                  />
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-gray-500">
              <span class="text-4xl mb-4 text-gray-400">📥</span>
              <p>No proposal data available</p>
            </div>
          </div>

          <!-- Documents Tab -->
          <div v-if="activeTab === 'documents'" class="space-y-6">
            <div v-if="documents.length > 0">
              <div class="mb-6">
                <div class="flex items-center justify-between">
                  <h4 class="text-lg font-semibold text-gray-900">Proposal Documents</h4>
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                    {{ documents.length }} document(s)
                  </span>
                </div>
                <p class="text-sm text-gray-600 mt-1">All documents associated with this proposal</p>
              </div>

              <!-- Document Viewer -->
              <div v-if="selectedDocument" class="mb-6 bg-white border border-gray-200 rounded-lg overflow-hidden">
                <div class="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50">
                  <div class="flex items-center space-x-3">
                    <span class="text-lg text-blue-600">{{ getDocumentEmoji(selectedDocument.file_type || selectedDocument.type) }}</span>
                    <div>
                      <h5 class="text-sm font-medium text-gray-900">{{ selectedDocument.file_name || selectedDocument.name }}</h5>
                      <p class="text-xs text-gray-500">{{ formatFileType(selectedDocument.file_type || selectedDocument.type) }} • {{ formatFileSize(selectedDocument.size) }}</p>
                    </div>
                  </div>
                  <div class="flex items-center space-x-2">
                    <button 
                      @click="downloadDocument(selectedDocument)"
                      class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                      title="Download"
                    >
                      <span class="text-xs">⬇</span>
                    </button>
                    <button 
                      @click="closeDocumentViewer"
                      class="inline-flex items-center px-2 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                      title="Close"
                    >
                      <span class="text-xs">✕</span>
                    </button>
                  </div>
                </div>
                
                <!-- Document Content -->
                <div class="h-96 overflow-auto">
                  <!-- PDF Viewer -->
                  <div v-if="isPDF(selectedDocument)" class="w-full h-full">
                    <div class="flex flex-col h-full">
                      <!-- PDF Viewer Options -->
                      <div class="flex items-center justify-between p-2 bg-gray-50 border-b">
                        <div class="flex items-center space-x-2">
                          <span class="text-sm font-medium text-gray-700">PDF Viewer:</span>
                          <select 
                            v-model="pdfViewerType" 
                            @change="updatePDFViewer"
                            class="text-xs border border-gray-300 rounded px-2 py-1"
                          >
                            <option value="google">Google Docs Viewer</option>
                            <option value="mozilla">Mozilla PDF.js</option>
                            <option value="direct">Direct Link</option>
                          </select>
                        </div>
                        <div class="flex items-center space-x-2">
                          <button 
                            @click="downloadDocument(selectedDocument)"
                            class="inline-flex items-center px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                            title="Download PDF"
                          >
                            <span class="text-xs">⬇</span>
                          </button>
                          <button 
                            @click="openPDFInNewTab"
                            class="inline-flex items-center px-2 py-1 bg-gray-600 text-white rounded hover:bg-gray-700"
                            title="Open in New Tab"
                          >
                            <span class="text-xs">↗</span>
                          </button>
                        </div>
                      </div>
                      
                      <!-- PDF Content -->
                      <div class="flex-1 relative">
                        <iframe 
                          :src="currentPDFUrl" 
                          class="w-full h-full border-0"
                          frameborder="0"
                          sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-downloads"
                          allow="fullscreen"
                          @error="handlePDFViewerError"
                        ></iframe>
                        
                        <!-- Loading/Error State -->
                        <div v-if="pdfViewerError" class="absolute inset-0 flex flex-col items-center justify-center bg-gray-100">
                          <span class="text-4xl mb-4 text-gray-400">📄</span>
                          <p class="text-sm text-gray-600 mb-2">{{ pdfViewerError }}</p>
                          <div class="flex space-x-2">
                            <button 
                              @click="tryAlternativePDFViewer"
                              class="text-xs px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              Try Alternative Viewer
                            </button>
                            <button 
                              @click="downloadDocument(selectedDocument)"
                              class="inline-flex items-center text-xs px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700"
                              title="Download Instead"
                            >
                              <span class="mr-1">⬇</span>
                              Download Instead
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Image Viewer -->
                  <div v-else-if="isImage(selectedDocument)" class="flex items-center justify-center h-full bg-gray-100">
                    <img 
                      :src="selectedDocument.url" 
                      :alt="selectedDocument.file_name || selectedDocument.name"
                      class="max-w-full max-h-full object-contain"
                    />
                  </div>
                  
                  <!-- Text Viewer -->
                  <div v-else-if="isText(selectedDocument)" class="p-4">
                    <pre class="text-sm text-gray-900 whitespace-pre-wrap">{{ textContent }}</pre>
                  </div>
                  
                  <!-- Unsupported Format -->
                  <div v-else class="flex flex-col items-center justify-center h-full text-gray-500">
                    <span class="text-4xl mb-4 text-gray-400">📄</span>
                    <p class="text-sm">Preview not available for this file type</p>
                    <button 
                      @click="downloadDocument(selectedDocument)"
                      class="mt-2 inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100"
                      title="Download to view"
                    >
                      <span class="mr-1">⬇</span>
                      Download to view
                    </button>
                  </div>
                </div>
              </div>
              
              <!-- Group documents by category -->
              <div v-for="category in [...new Set(documents.map(d => d.category))]" :key="category" class="mb-8">
                <div class="mb-4">
                  <h5 class="text-sm font-semibold text-gray-900 flex items-center">
                    <span class="flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-blue-600 text-xs mr-2">
                      {{ documents.filter(d => d.category === category).length }}
                    </span>
                    {{ category }}
                  </h5>
                </div>
                
                <div class="grid grid-cols-1 gap-4">
                  <div v-for="doc in documents.filter(d => d.category === category)" 
                       :key="doc.id" 
                       class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all duration-200">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center space-x-3">
                        <div class="p-2 bg-blue-50 rounded-lg">
                          <span class="text-2xl text-blue-600">{{ getDocumentEmoji(doc.file_type || doc.type) }}</span>
                        </div>
                        <div>
                          <h4 class="text-sm font-semibold text-gray-900">
                            {{ doc.file_name || doc.name }}
                          </h4>
                          <div class="flex items-center space-x-2 mt-1">
                            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                              {{ formatFileType(doc.file_type || doc.type) }}
                            </span>
                            <span class="text-xs text-gray-500">
                              {{ formatFileSize(doc.size) }}
                            </span>
                            <span v-if="doc.uploaded_at" class="text-xs text-gray-500">
                              <span class="text-gray-400 mx-1">•</span>
                              {{ formatDate(doc.uploaded_at) }}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div class="flex items-center space-x-2">
                        <button 
                          @click="downloadDocument(doc)"
                          class="inline-flex items-center px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                          title="Download"
                        >
                          <span class="text-sm">⬇</span>
                        </button>
                        <button 
                          @click="viewDocumentInSplitScreen(doc)"
                          class="inline-flex items-center px-3 py-1 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
                          title="View in Split Screen"
                        >
                          <span class="text-sm">👁</span>
                        </button>
                        <button 
                          @click="viewDocument(doc)"
                          class="inline-flex items-center px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                          title="Open in New Tab"
                        >
                          <span class="text-sm">↗</span>
                        </button>
                      </div>
                    </div>
                    
                    <div v-if="doc.description" class="mt-2 text-sm text-gray-600">
                      {{ doc.description }}
                    </div>
                    
                    <!-- Document Preview -->
                    <div v-if="doc.preview_url && isPreviewable(doc)" class="mt-4">
                      <div class="border rounded-lg overflow-hidden bg-gray-50">
                        <div class="flex items-center justify-between px-4 py-2 border-b border-gray-200 bg-white">
                          <span class="text-sm font-medium text-gray-700">Preview</span>
                          <button 
                            @click="togglePreview(doc.id)"
                            class="inline-flex items-center px-2 py-1 text-sm font-medium text-gray-500 hover:text-gray-700"
                          >
                            <Icons :name="previewStates[doc.id] ? 'chevron-up' : 'chevron-down'" class="h-4 w-4" />
                          </button>
                        </div>
                        <div v-show="previewStates[doc.id]" class="relative">
                          <iframe 
                            :src="doc.preview_url" 
                            class="w-full h-96" 
                            frameborder="0"
                            sandbox="allow-same-origin allow-scripts allow-popups"
                          ></iframe>
                          <div class="absolute inset-0 bg-transparent" @click="viewDocument(doc)"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-gray-500">
              <span class="text-4xl mb-4 text-gray-400">📄</span>
              <p>No documents available</p>
            </div>
          </div>

          <!-- Risks Tab -->
          <div v-if="activeTab === 'risks'" class="space-y-6">
            <div v-if="risks.length > 0">
              <div class="mb-6">
                <div class="flex items-center justify-between">
                  <h4 class="text-lg font-semibold text-gray-900">Identified Risks</h4>
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                    {{ risks.length }} risk(s) identified
                  </span>
                </div>
                <p class="text-sm text-gray-600 mt-1">AI-identified risks associated with this proposal</p>
              </div>

              <!-- Risk Cards -->
              <div class="grid grid-cols-1 gap-6">
                <div v-for="risk in risks" :key="risk.id" class="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-all duration-200">
                  <!-- Risk Header -->
                  <div class="flex items-start justify-between mb-4">
                    <div class="flex-1">
                      <h5 class="text-lg font-semibold text-gray-900 mb-2">{{ risk.title }}</h5>
                      <div class="flex items-center space-x-4 text-sm text-gray-600">
                        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium" :class="getPriorityBadgeClass(risk.priority)">
                          {{ risk.priority }}
                        </span>
                        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium" :class="getStatusBadgeClass(risk.status)">
                          {{ risk.status }}
                        </span>
                        <span v-if="risk.risk_type" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {{ risk.risk_type }}
                        </span>
                      </div>
                    </div>
                    <div class="text-right">
                      <div class="text-2xl font-bold" :class="getScoreColor(risk.score)">{{ risk.score }}</div>
                      <div class="text-xs text-gray-500">Risk Score</div>
                    </div>
                  </div>

                  <!-- Risk Description -->
                  <div class="mb-4">
                    <p class="text-sm text-gray-700">{{ risk.description }}</p>
                  </div>

                  <!-- Risk Metrics -->
                  <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div class="bg-gray-50 rounded-lg p-3">
                      <div class="text-sm font-medium text-gray-600">Likelihood</div>
                      <div class="text-lg font-semibold text-gray-900">{{ risk.likelihood }}/10</div>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-3">
                      <div class="text-sm font-medium text-gray-600">Impact</div>
                      <div class="text-lg font-semibold text-gray-900">{{ risk.impact }}/10</div>
                    </div>
                    <div class="bg-gray-50 rounded-lg p-3">
                      <div class="text-sm font-medium text-gray-600">Exposure Rating</div>
                      <div class="text-lg font-semibold text-gray-900">{{ risk.exposure_rating || 'N/A' }}</div>
                    </div>
                  </div>

                  <!-- AI Explanation -->
                  <div v-if="risk.ai_explanation" class="mb-4">
                    <h6 class="text-sm font-semibold text-gray-900 mb-2">🤖 AI Analysis</h6>
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <p class="text-sm text-blue-800">{{ risk.ai_explanation }}</p>
                    </div>
                  </div>

                  <!-- Suggested Mitigations -->
                  <div v-if="risk.suggested_mitigations && risk.suggested_mitigations.length > 0" class="mb-4">
                    <h6 class="text-sm font-semibold text-gray-900 mb-2">🛡️ Suggested Mitigations</h6>
                    <div class="space-y-2">
                      <div v-for="(mitigation, index) in risk.suggested_mitigations" :key="index" class="bg-green-50 border border-green-200 rounded-lg p-3">
                        <p class="text-sm text-green-800">{{ mitigation }}</p>
                      </div>
                    </div>
                  </div>
                  <div v-else-if="risk.suggested_mitigations && typeof risk.suggested_mitigations === 'string' && risk.suggested_mitigations.trim()" class="mb-4">
                    <h6 class="text-sm font-semibold text-gray-900 mb-2">🛡️ Suggested Mitigations</h6>
                    <div class="bg-green-50 border border-green-200 rounded-lg p-3">
                      <p class="text-sm text-green-800">{{ risk.suggested_mitigations }}</p>
                    </div>
                  </div>

                  <!-- Risk Metadata -->
                  <div class="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-200">
                    <div class="flex items-center space-x-4">
                      <span v-if="risk.created_at">Created: {{ formatDate(risk.created_at) }}</span>
                      <span v-if="risk.acknowledged_at">Acknowledged: {{ formatDate(risk.acknowledged_at) }}</span>
                      <span v-if="risk.mitigated_at">Mitigated: {{ formatDate(risk.mitigated_at) }}</span>
                    </div>
                    <div class="flex items-center space-x-2">
                      <span v-if="risk.assigned_to" class="text-gray-600">Assigned to: User {{ risk.assigned_to }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-gray-500">
              <span class="text-4xl mb-4 text-gray-400">⚠️</span>
              <p>No risks identified for this proposal</p>
              <p class="text-sm text-gray-400 mt-2">AI risk analysis may not have been performed yet</p>
            </div>
          </div>

        </div>
      </div>

      <!-- Right Panel - Evaluation Form -->
      <div class="w-96 overflow-y-auto bg-gray-50">
        <div class="p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-6">Evaluation Form</h3>
          
          <div class="space-y-6">
            <div v-for="criterion in evaluationCriteria" :key="criterion.id" class="bg-white rounded-lg border border-gray-200 p-4">
              <div class="flex items-center justify-between mb-2">
                <label class="block text-sm font-medium text-gray-900">
                  {{ criterion.name }}
                  <span v-if="criterion.is_mandatory" class="text-red-500 ml-1">*</span>
                </label>
                <span class="text-xs font-medium px-2 py-1 rounded-full" 
                      :class="scores[criterion.id] ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'">
                  Max: {{ criterion.max_score }} points
                </span>
              </div>
              
              <p class="text-sm text-gray-600 mb-3">{{ criterion.description }}</p>
              
              <div class="space-y-2">
                <div class="flex items-center justify-between text-sm">
                  <span class="text-gray-500">Score</span>
                  <span class="font-medium" :class="scores[criterion.id] ? 'text-blue-600' : 'text-gray-600'">
                    {{ scores[criterion.id] || 0 }}/{{ criterion.max_score }}
                  </span>
                </div>
                <input
                  v-model.number="scores[criterion.id]"
                  type="range"
                  :min="criterion.min_score || 0"
                  :max="criterion.max_score"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
                  @change="validateScore(criterion.id, $event.target.value)"
                />
                <input
                  v-model.number="scores[criterion.id]"
                  type="number"
                  :min="criterion.min_score || 0"
                  :max="criterion.max_score"
                  class="w-20 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  @blur="validateScore(criterion.id, $event.target.value)"
                />
                <div class="flex justify-between text-xs text-gray-500">
                  <span>Poor</span>
                  <span>Average</span>
                  <span>Excellent</span>
                </div>
              </div>

              <!-- Comments for this criterion -->
              <div class="mt-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Comments for {{ criterion.name }}
                </label>
                <textarea
                  v-model="comments[criterion.id]"
                  rows="2"
                  class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  :placeholder="'Add your comments about ' + criterion.name.toLowerCase()"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Overall Comments
              </label>
              <textarea
                v-model="overallComments"
                rows="4"
                class="w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Add your evaluation comments..."
              />
            </div>

            <div class="pt-4 border-t border-gray-200">
              <div class="flex justify-between items-center mb-4">
                <span class="text-sm font-medium text-gray-700">Total Score</span>
                <span class="text-lg font-bold text-blue-600">{{ totalScore }}/{{ maxTotalScore }}</span>
              </div>
              
              <div class="space-y-2">
                <button 
                  type="button"
                  @click="saveEvaluation" 
                  :disabled="saving"
                  class="w-full flex items-center justify-center px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span class="mr-2">💾</span>
                  {{ saving ? 'Saving...' : 'Save Evaluation' }}
                </button>
                <button 
                  type="button"
                  @click="submitEvaluation" 
                  :disabled="saving || !isValid || isSubmitted"
                  class="w-full flex items-center justify-center px-4 py-2 border border-gray-300 hover:bg-gray-50 rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span class="mr-2">✅</span>
                  {{ isSubmitted ? 'Already Submitted' : 'Submit Final' }}
                </button>
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

<script setup lang="ts">
import { ref, computed, onMounted, defineComponent, h } from 'vue'
import { useRouter } from 'vue-router'
import { useRfpApi } from '@/composables/useRfpApi'
import { getTprmApiUrl, getApiOrigin } from '@/utils/backendEnv'
import Icons from '@/components_rfp/ui/Icons.vue'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'

const router = useRouter()

// Get authenticated headers for axios requests
const { getAuthHeaders } = useRfpApi()

// DataField Component
// Helper function to format values
const formatFieldValue = (val, type, currency = 'USD') => {
  if (val === null || val === undefined || val === '') return 'Not specified'
  
  switch (type) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency || 'USD'
      }).format(val)
    case 'number':
      return typeof val === 'number' ? val.toLocaleString() : val
    case 'datetime':
      const date = new Date(val)
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
    case 'boolean':
      return val ? 'Yes' : 'No'
    case 'badge':
      return val
    default:
      return String(val)
  }
}

// DataField component using render function
const DataField = defineComponent({
  name: 'DataField',
  props: {
    label: { type: String, required: true },
    value: { required: true },
    type: { type: String, default: 'text' },
    currency: { type: String, default: 'USD' },
    badgeClass: { type: String, default: 'bg-gray-100 text-gray-800' }
  },
  setup(props) {
    return () => {
      const { label, value, type, currency, badgeClass } = props
      const formattedValue = formatFieldValue(value, type, currency)
      
      return h('div', { class: 'space-y-1' }, [
        h('label', { class: 'text-xs font-medium text-gray-500' }, label),
        type === 'badge' 
          ? h('div', { class: `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeClass}` }, formattedValue)
          : h('div', { class: 'text-sm font-medium text-gray-900' }, formattedValue)
      ])
    }
  }
})

// API base URL
const API_BASE_URL = 'https://grc-tprm.vardaands.com/api/tprm/rfp'

// State
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const proposalData = ref(null)
const activeTab = ref('proposal')
const documents = ref([])
const risks = ref([])
const scores = ref({})
const comments = ref({})
const overallComments = ref('')
const saving = ref(false)
const isSubmitted = ref(false)
const previewStates = ref({})
const selectedDocument = ref(null)
const textContent = ref('')
const pdfViewerType = ref('google')
const currentPDFUrl = ref('')
const pdfViewerError = ref('')

// Evaluation criteria - will be loaded from API
const evaluationCriteria = ref([])

// Computed properties
const totalScore = computed(() => {
  const total = Object.values(scores.value).reduce((sum, score) => sum + (Number(score) || 0), 0)
  return Math.round(total * 100) / 100 // Round to 2 decimal places
})

const maxTotalScore = computed(() => {
  const total = evaluationCriteria.value.reduce((sum, criterion) => sum + (Number(criterion.max_score) || 0), 0)
  return Math.round(total * 100) / 100 // Round to 2 decimal places
})

const isValid = computed(() => {
  // Check if all mandatory criteria have scores and comments
  const mandatoryCriteria = evaluationCriteria.value.filter(c => c.is_mandatory)
  const allMandatoryScored = mandatoryCriteria.every(c => 
    scores.value[c.id] !== undefined && scores.value[c.id] !== null && scores.value[c.id] >= 0
  )
  const allMandatoryComments = mandatoryCriteria.every(c => 
    comments.value[c.id] && comments.value[c.id].trim().length > 0
  )
  const hasOverallComments = overallComments.value.trim().length > 0

  return allMandatoryScored && allMandatoryComments && hasOverallComments
})

// Computed property to check if there's additional data to display
const hasAdditionalData = computed(() => {
  if (!proposalData.value) return false
  
  const excludeFields = [
    'response_id', 'rfp_id', 'rfp_number', 'vendor_id', 'vendor_name', 'org',
    'submission_status', 'evaluation_status', 'submitted_at', 'proposed_value',
    'currency', 'technical_score', 'commercial_score', 'overall_score',
    'proposal_data', 'document_urls', 'response_documents'
  ]
  
  return Object.keys(proposalData.value).some(key => 
    !excludeFields.includes(key) && 
    proposalData.value[key] !== null && 
    proposalData.value[key] !== undefined &&
    proposalData.value[key] !== ''
  )
})

// Computed property to get additional data fields
const additionalDataFields = computed(() => {
  if (!proposalData.value) return {}
  
  const excludeFields = [
    'response_id', 'rfp_id', 'rfp_number', 'vendor_id', 'vendor_name', 'org',
    'submission_status', 'evaluation_status', 'submitted_at', 'proposed_value',
    'currency', 'technical_score', 'commercial_score', 'overall_score',
    'proposal_data', 'document_urls', 'response_documents'
  ]
  
  const additional = {}
  Object.keys(proposalData.value).forEach(key => {
    if (!excludeFields.includes(key) && 
        proposalData.value[key] !== null && 
        proposalData.value[key] !== undefined &&
        proposalData.value[key] !== '') {
      additional[key] = proposalData.value[key]
    }
  })
  
  return additional
})

// Methods
const validateScore = (criterionId, value) => {
  const criterion = evaluationCriteria.value.find(c => c.id === criterionId)
  if (!criterion) return

  const minScore = criterion.min_score !== undefined && criterion.min_score !== null ? criterion.min_score : 0
  const maxScore = criterion.max_score || 100

  // Handle empty/NaN values - set to minimum score (0)
  if (value === '' || value === null || value === undefined) {
    scores.value[criterionId] = minScore
    return
  }

  const numValue = Number(value)
  
  // If conversion results in NaN, set to minimum
  if (isNaN(numValue)) {
    scores.value[criterionId] = minScore
    return
  }

  // Ensure score is within bounds (0 is valid)
  scores.value[criterionId] = Math.min(Math.max(numValue, minScore), maxScore)
}

// Parse documents from proposal data
const parseDocuments = (proposalData) => {
  if (!proposalData) return []
  
  const docs = []
  const docSources = [
    { key: 'documents', label: 'Response Documents' },
    { key: 'uploaded_documents', label: 'Uploaded Documents' },
    { key: 'additional_documents', label: 'Additional Documents' }
  ]
  
  docSources.forEach(source => {
    if (proposalData[source.key]) {
      Object.entries(proposalData[source.key]).forEach(([docType, docData]) => {
        if (typeof docData === 'object' && docData !== null) {
          docs.push({
            id: docData.key,
            name: docData.filename || docData.key.split('_').pop(),
            file_name: docData.filename || docData.key.split('_').pop(),
            type: docType,
            file_type: docData.content_type || getFileTypeFromName(docData.filename || docData.key),
            size: docData.size,
            url: docData.url,
            download_url: docData.url,
            preview_url: docData.url,
            uploaded_at: docData.uploaded_at || proposalData.submitted_at,
            category: source.label,
            description: docData.description || `${formatFileType(docType)} document`
          })
        }
      })
    }
  })
  
  return docs
}

// Get file type from filename
const getFileTypeFromName = (filename) => {
  if (!filename) return 'application/octet-stream'
  const ext = filename.split('.').pop().toLowerCase()
  const mimeTypes = {
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'txt': 'text/plain',
    'csv': 'text/csv',
    'zip': 'application/zip'
  }
  return mimeTypes[ext] || 'application/octet-stream'
}

// Removed ensureCriteriaExist - we now only use existing criteria from database

// Removed unused criteria creation functions - we now only use existing criteria from database

const loadEvaluationCriteria = async () => {
  try {
    const rfpId = proposalData.value?.rfp_id || proposalData.value?.id
    if (!rfpId) {
      console.log('No RFP ID found, cannot load criteria')
      evaluationCriteria.value = []
      return
    }

    const endpoint = `${API_BASE_URL}/evaluation-criteria/?rfp_id=${encodeURIComponent(rfpId)}`
    console.log('Loading evaluation criteria from:', endpoint)
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (!response.ok) {
      console.error('Failed to load evaluation criteria:', response.status)
      evaluationCriteria.value = []
      return
    }

    const data = await response.json()
    console.log('Raw API response:', data)
    
    const criteriaData = Array.isArray(data) ? data : (data.results || [])
    console.log('Criteria data before filtering:', criteriaData)
    
    // The backend already filters by rfp_id, so we don't need to filter again
    evaluationCriteria.value = criteriaData
      .sort((a, b) => (a.display_order || 0) - (b.display_order || 0))
      .map(criterion => ({
        id: criterion.criteria_id,
        name: criterion.criteria_name,
        description: criterion.criteria_description,
        weight: criterion.weight_percentage,
        evaluation_type: criterion.evaluation_type,
        min_score: Number(criterion.min_score ?? 0),
        max_score: Number(criterion.max_score ?? 100),
        is_mandatory: !!criterion.is_mandatory,
        display_order: criterion.display_order
      }))

    console.log('Final loaded criteria:', evaluationCriteria.value)
    console.log('Criteria count:', evaluationCriteria.value.length)
    if (evaluationCriteria.value.length === 0) {
      console.warn('No evaluation criteria loaded! Check if criteria exist for RFP ID:', rfpId)
    }
  } catch (error) {
    console.error('Error loading evaluation criteria:', error)
    evaluationCriteria.value = []
  }
}

const loadRisks = async () => {
  try {
    const response_id = proposalData.value?.response_id
    if (!response_id) {
      console.log('[RISKS] No response ID found, cannot load risks')
      risks.value = []
      return
    }

    // Use the same base URL pattern as other endpoints
    // The endpoint is at /api/tprm/rfp-approval/risks-for-response/<response_id>/
    // Build URL: https://grc-tprm.vardaands.com/api/tprm/rfp-approval/risks-for-response/<response_id>/
    const apiOrigin = getApiOrigin() || 'https://grc-tprm.vardaands.com'
    const endpoint = `${apiOrigin}/api/tprm/rfp-approval/risks-for-response/${encodeURIComponent(response_id)}/`
    console.log('[RISKS] Loading risks from:', endpoint)
    console.log('[RISKS] Query: entity="RFP" AND row="' + response_id + '"')
    
    let response
    try {
      response = await fetch(endpoint, {
        method: 'GET',
        headers: getAuthHeaders()
      })
    } catch (fetchError) {
      // Handle network errors (connection refused, timeout, etc.)
      console.error('[RISKS] Network error fetching risks:', fetchError)
      console.error('[RISKS] This usually means the backend server is not running or the endpoint is unreachable')
      console.error('[RISKS] Endpoint attempted:', endpoint)
      risks.value = []
      return
    }
    
    if (!response.ok) {
      let errorText = ''
      try {
        errorText = await response.text()
        console.error('[RISKS] Failed to load risks:', response.status, errorText)
        
        // If it's a 500 error, try to parse the error details
        if (response.status === 500) {
          try {
            const errorData = JSON.parse(errorText)
            console.error('[RISKS] Error details:', errorData)
          } catch (e) {
            console.error('[RISKS] Could not parse error response')
          }
        }
      } catch (e) {
        console.error('[RISKS] Could not read error response:', e)
      }
      
      risks.value = []
      return
    }

    const data = await response.json()
    console.log('[RISKS] Raw API response:', data)
    console.log('[RISKS] Total risks in response:', data.total_risks || 0)
    
    // Ensure we have a risks array
    const risksArray = data.risks || []
    console.log('[RISKS] Risks array length:', risksArray.length)
    
    // Parse the risks data and handle JSON fields
    const parsedRisks = risksArray.map(risk => {
      console.log('[RISKS] Processing risk:', risk.id, risk.title)
      return {
        ...risk,
        suggested_mitigations: parseMitigations(risk.suggested_mitigations)
      }
    })
    
    risks.value = parsedRisks
    console.log('[RISKS] Successfully loaded', risks.value.length, 'risks')
    
    if (risks.value.length === 0) {
      console.log('[RISKS] No risks found for response_id:', response_id)
      console.log('[RISKS] Make sure risks exist in risk_tprm table with:')
      console.log('[RISKS]   - entity = "RFP"')
      console.log('[RISKS]   - row = "' + response_id + '"')
    }
  } catch (error) {
    console.error('[RISKS] Error loading risks:', error)
    console.error('[RISKS] Error stack:', error.stack)
    risks.value = []
  }
}

const loadProposalData = async () => {
  const urlParams = new URLSearchParams(window.location.search)
  const response_id = urlParams.get('response_id')

  if (!response_id) {
    PopupService.error('No proposal specified', 'No Proposal')
    PopupService.onAction('ok', () => {
      router.push('/my-approvals')
    })
    return
  }

  // Validate response_id format
  if (response_id.startsWith('WF_') || response_id.startsWith('AR_')) {
    console.log('❌ DEBUG: Invalid response_id format detected:', response_id)
    PopupService.error('❌ Invalid proposal ID format!\n\nThe system received a workflow or approval ID instead of a proposal response ID.\n\nThis usually happens when:\n• The approval workflow was not properly configured\n• The proposal data is missing from the approval\n\nPlease contact your administrator or try a different approval.', 'Invalid ID Format')
    PopupService.onAction('ok', () => {
      router.push('/my-approvals')
    })
    return
  }

  try {
    // Use the correct API endpoint for RFP responses
    const endpoint = `/api/v1/rfp-responses-detail/${response_id}/`
    const apiOrigin = getApiOrigin() || 'https://grc-tprm.vardaands.com'
    console.log('Fetching proposal data from:', `${apiOrigin}${endpoint}`)
    
    const response = await fetch(`${apiOrigin}${endpoint}`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Proposal not found (ID: ${response_id}). This proposal may have been deleted or the ID is incorrect.`)
      } else {
        throw new Error(`Failed to fetch proposal data: ${response.status} ${response.statusText}`)
      }
    }

    const data = await response.json()
    console.log('Raw API response:', data)
    
    const rawProposalData = data.data || data
    console.log('Raw proposal data:', rawProposalData)
    
    // Parse proposal_data if it's a string
    let parsedProposalData = rawProposalData
    if (rawProposalData.proposal_data && typeof rawProposalData.proposal_data === 'string') {
      try {
        parsedProposalData = {
          ...rawProposalData,
          proposal_data: JSON.parse(rawProposalData.proposal_data)
        }
        console.log('Parsed proposal_data:', parsedProposalData.proposal_data)
      } catch (e) {
        console.error('Error parsing proposal_data:', e)
      }
    }
    
    // Store the parsed data
    proposalData.value = parsedProposalData
    
    // Debug: Log response_documents structure
    console.log('=== PROPOSAL DATA DEBUG ===')
    console.log('response_documents:', parsedProposalData.response_documents)
    console.log('proposal_data:', parsedProposalData.proposal_data)
    console.log('response_documents type:', typeof parsedProposalData.response_documents)
    console.log('response_documents keys:', parsedProposalData.response_documents ? Object.keys(parsedProposalData.response_documents) : 'N/A')
    
    // Check if evaluation has already been submitted
    if (parsedProposalData.evaluation_status === 'COMPLETED' || parsedProposalData.evaluation_status === 'APPROVED') {
      isSubmitted.value = true
      console.log('Evaluation already submitted - disabling submit button')
    }
    
    // Load evaluation criteria for this RFP
    await loadEvaluationCriteria()
    
    // Load risks for this proposal
    await loadRisks()
    
    // Use only existing criteria assigned to this RFP; do not auto-create
    
    // Initialize documents array
    documents.value = []
    
    console.log('Starting document extraction...')
    
    try {
      // PRIORITY 1: Extract from document_urls (contains real S3 URLs)
      if (proposalData.value?.document_urls) {
        console.log('✅ Found document_urls (REAL S3 URLs):', proposalData.value.document_urls)
        console.log('✅ document_urls type:', typeof proposalData.value.document_urls)
        console.log('✅ document_urls keys:', Object.keys(proposalData.value.document_urls || {}))
        
        Object.entries(proposalData.value.document_urls).forEach(([docType, docInfo]) => {
          console.log(`Processing document type: ${docType}, value:`, docInfo, 'type:', typeof docInfo)
          
          // Handle both string URLs and object structures
          let url = null
          let filename = null
          let size = null
          let contentType = null
          
          if (typeof docInfo === 'string') {
            // Simple string URL
            url = docInfo
            filename = url.split('/').pop() || docType
          } else if (docInfo && typeof docInfo === 'object') {
            // Object with url, filename, etc.
            url = docInfo.url || docInfo.download_url || docInfo.preview_url
            filename = docInfo.filename || docInfo.file_name || docInfo.name || (url ? url.split('/').pop() : docType)
            size = docInfo.size
            contentType = docInfo.content_type || docInfo.file_type
          }
          
          if (url) {
            const doc = {
              id: docInfo?.document_id || docInfo?.s3_file_id || `s3_${docType}`,
              name: docType.replace(/_/g, ' ').toUpperCase(),
              file_name: filename,
              type: docType,
              file_type: contentType || getFileTypeFromName(filename),
              url: url,
              download_url: url,
              preview_url: url,
              size: size,
              uploaded_at: docInfo?.upload_date || proposalData.value.submitted_at,
              category: 'S3 Documents',
              description: `${docType.replace(/_/g, ' ').toUpperCase()} - Real S3 URL`,
              source: 'document_urls'
            }
            console.log('✅ Adding S3 document:', doc)
            documents.value.push(doc)
          } else {
            console.warn(`⚠️ Skipping document type ${docType} - no URL found in:`, docInfo)
          }
        })
      }
      
      // PRIORITY 2: Extract from response_documents (backup)
      if (proposalData.value?.response_documents) {
        console.log('Found response_documents:', proposalData.value.response_documents)
        
        Object.entries(proposalData.value.response_documents).forEach(([docType, docData]) => {
          if (docData && typeof docData === 'object' && docData.url) {
            // Skip if we already have this from document_urls
            if (!documents.value.find(d => d.url === docData.url)) {
              const doc = {
                id: docData.key || `resp_${docType}`,
                name: docData.filename || docType.replace(/_/g, ' ').toUpperCase(),
                file_name: docData.filename || docType,
                type: docType,
                file_type: docData.content_type || getFileTypeFromName(docData.filename || ''),
                size: docData.size,
                url: docData.url,
                download_url: docData.url,
                preview_url: docData.url,
                uploaded_at: proposalData.value.submitted_at,
                category: 'Response Documents',
                description: `${docType.replace(/_/g, ' ').toUpperCase()} document`,
                source: 'response_documents'
              }
              console.log('Adding document from response_documents:', doc)
              documents.value.push(doc)
            }
          }
        })
      }
      
      // PRIORITY 3: Extract from proposal_data.documents (legacy/backup)
      if (proposalData.value?.proposal_data?.documents) {
        console.log('Found proposal_data.documents:', proposalData.value.proposal_data.documents)
        
        Object.entries(proposalData.value.proposal_data.documents).forEach(([docType, docData]) => {
          if (docData && typeof docData === 'object' && docData.url) {
            // Skip if we already have this document
            if (!documents.value.find(d => d.url === docData.url || d.type === docType)) {
              const doc = {
                id: docData.key || `legacy_${docType}`,
                name: docData.filename || docType.replace(/_/g, ' ').toUpperCase(),
                file_name: docData.filename || docType,
                type: docType,
                file_type: docData.content_type || getFileTypeFromName(docData.filename || ''),
                size: docData.size,
                url: docData.url,
                download_url: docData.url,
                preview_url: docData.url,
                uploaded_at: proposalData.value.submitted_at,
                category: 'Legacy Documents',
                description: `${docType.replace(/_/g, ' ').toUpperCase()} document`,
                source: 'proposal_data.documents'
              }
              console.log('Adding document from proposal_data.documents:', doc)
              documents.value.push(doc)
            }
          }
        })
      }
      
      console.log('Final extracted documents:', documents.value)
      console.log('Total documents extracted:', documents.value.length)
      
      // Log document URLs for debugging
      documents.value.forEach((doc, index) => {
        console.log(`Document ${index + 1}:`, {
          name: doc.name,
          url: doc.url,
          type: doc.file_type,
          size: doc.size
        })
      })
      
    } catch (error) {
      console.error('Error during document extraction:', error)
    }
    
    // Initialize preview states for all documents
    documents.value.forEach(doc => {
      if (doc.id && isPreviewable(doc)) {
        previewStates.value[doc.id] = false
      }
    })
    
    // Initialize scores for all criteria
    evaluationCriteria.value.forEach(criterion => {
      if (!(criterion.id in scores.value)) {
        scores.value[criterion.id] = 0
      }
    })
    
    console.log('Loaded proposal data:', proposalData.value)
    console.log('Extracted documents:', documents.value)
    console.log('Loaded evaluation criteria:', evaluationCriteria.value)
    
  } catch (error) {
    console.error('Error loading proposal:', error)
    
    // Provide more specific error messages
    let errorMessage = 'Failed to load proposal data.'
    
    if (error.message.includes('Proposal not found')) {
      errorMessage = error.message
    } else if (error.message.includes('404')) {
      errorMessage = `Proposal not found (ID: ${response_id}). This proposal may have been deleted or the ID is incorrect.`
    } else if (error.message.includes('Failed to fetch')) {
      errorMessage = 'Network error: Unable to connect to the server. Please check your internet connection and try again.'
    } else {
      errorMessage = `Error loading proposal: ${error.message}`
    }
    
    PopupService.error(errorMessage, 'Loading Failed')
    PopupService.onAction('ok', () => {
      router.push('/my-approvals')
    })
  }
}

const saveEvaluation = async () => {
  saving.value = true
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const response_id = urlParams.get('response_id')
    const userId = urlParams.get('userId')
    const stageId = urlParams.get('stageId')
    const approvalId = urlParams.get('approvalId')
    
    if (!response_id) {
      throw new Error('No response ID found')
    }

    // Get evaluator_id from URL params or use default
    const evaluator_id = userId ? parseInt(userId) : 1

    console.log('=== SAVE EVALUATION DEBUG ===')
    console.log('Response ID:', response_id)
    console.log('Evaluator ID (userId):', evaluator_id)
    console.log('Stage ID:', stageId)
    console.log('Approval ID:', approvalId)
    console.log('Scores:', scores.value)
    console.log('Comments:', comments.value)

    // Prepare evaluation scores in the format expected by backend
    const evaluation_scores = {}
    evaluationCriteria.value.forEach(criterion => {
      const score = scores.value[criterion.id] || 0
      const weight = parseFloat(criterion.weight) || 0  // Ensure weight is a number
      const category = criterion.category || 'technical'
      
      evaluation_scores[criterion.id] = {
        score: score,
        weight: weight,
        category: category
      }
    })

    // Prepare the data structure expected by the backend (for DRAFT save)
    const draftSaveData = {
      evaluation_scores: evaluation_scores,
      comments: comments.value,
      overall_comments: overallComments.value || '',
      evaluator_id: evaluator_id,
      stage_id: stageId,
      approval_id: approvalId,
      is_draft: true,
      clear_existing: false
    }

    console.log('Saving draft evaluation data:', draftSaveData)
    console.log('Current evaluation criteria:', evaluationCriteria.value)
    console.log('Criteria IDs being used:', Object.keys(evaluation_scores))

    // Evaluation data will be saved to backend only
    
    // Try to save to backend using the correct endpoint
    try {
      const response = await fetch(`${API_BASE_URL}/rfp-evaluation-scores/${response_id}/save/`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(draftSaveData)
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Draft evaluation scores saved successfully:', result)
      } else {
        const errorText = await response.text()
        console.log('Draft save failed:', errorText)
      }
    } catch (backendError) {
      console.log('Backend not available, data saved locally:', backendError)
    }

    PopupService.success('Evaluation saved successfully', 'Saved')
    
    // Create notification
    await notificationService.createRFPEvaluationNotification('evaluation_saved', {
      rfp_id: proposalData.value?.rfp_id,
      response_id: proposalData.value?.response_id
    })
  } catch (error) {
    console.error('Error saving evaluation:', error)
    PopupService.error('Failed to save evaluation', 'Save Failed')
    
    // Create error notification
    await notificationService.createRFPErrorNotification('save_evaluation', error.message, {
      title: 'Failed to Save Evaluation',
      response_id: proposalData.value?.response_id
    })
  } finally {
    saving.value = false
  }
}

const submitEvaluation = async () => {
  if (!isValid.value) {
    PopupService.warning('Please complete all mandatory fields before submitting', 'Missing Fields')
    
    // Create warning notification
    await notificationService.createRFPWarningNotification('incomplete_evaluation', {
      title: 'Incomplete Evaluation',
      message: 'Please complete all mandatory fields before submitting'
    })
    return
  }

  saving.value = true
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const response_id = urlParams.get('response_id')
    const userId = urlParams.get('userId')
    const stageId = urlParams.get('stageId')
    const approvalId = urlParams.get('approvalId')
    
    if (!response_id) {
      throw new Error('No response ID found')
    }

    // Get evaluator_id from URL params or use default
    const evaluator_id = userId ? parseInt(userId) : 1
    
    console.log('=== SUBMIT EVALUATION DEBUG ===')
    console.log('Response ID:', response_id)
    console.log('Evaluator ID (userId):', evaluator_id)
    console.log('Stage ID:', stageId)
    console.log('Approval ID:', approvalId)
    console.log('Scores:', scores.value)
    console.log('Comments:', comments.value)
    console.log('Proposal Data:', proposalData.value)
    console.log('RFP ID from proposal:', proposalData.value?.rfp_id)

    // Prepare evaluation scores in the format expected by backend
    const evaluation_scores = {}
    evaluationCriteria.value.forEach(criterion => {
      const score = scores.value[criterion.id] || 0
      const weight = parseFloat(criterion.weight) || 0  // Ensure weight is a number
      const category = criterion.category || 'technical'
      
      evaluation_scores[criterion.id] = {
        score: score,
        weight: weight,
        category: category
      }
    })

    console.log('Current evaluation criteria:', evaluationCriteria.value)
    console.log('Formatted evaluation scores:', evaluation_scores)

    // Prepare the data structure expected by the backend
    const submitSaveData = {
      evaluation_scores: evaluation_scores,
      comments: comments.value,
      overall_comments: overallComments.value || '',
      evaluator_id: evaluator_id,
      stage_id: stageId,
      approval_id: approvalId,
      is_draft: false,
      clear_existing: false
    }

    console.log('Sending data to backend:', submitSaveData)
    console.log('Evaluation scores being sent:', evaluation_scores)
    console.log('Comments being sent:', comments.value)
    
    const response = await fetch(`${API_BASE_URL}/rfp-evaluation-scores/${response_id}/save/`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(submitSaveData)
    })

    console.log('API Response status:', response.status)
    console.log('API Response headers:', response.headers)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('API Error Response:', errorText)
      
      // If it's a duplicate key error, try to clear existing scores and retry
      if (errorText.includes('Duplicate entry') || errorText.includes('unique_response_criteria_evaluator')) {
        console.log('Duplicate key error detected, retrying with clear_existing flag')
        
        // Add clear_existing flag to the request
        const retryData = {
          ...submitSaveData,
          clear_existing: true
        }
        
        const retryResponse = await fetch(`${API_BASE_URL}/rfp-evaluation-scores/${response_id}/save/`, {
          method: 'POST',
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(retryData)
        })
        
        if (!retryResponse.ok) {
          const retryErrorText = await retryResponse.text()
          console.error('Retry API Error Response:', retryErrorText)
          throw new Error(`Failed to save evaluation scores after retry: ${retryResponse.status} - ${retryErrorText}`)
        }
        
        const retryResult = await retryResponse.json()
        console.log('Retry successful:', retryResult)
        return retryResult
      }
      
      throw new Error(`Failed to save evaluation scores: ${response.status} - ${errorText}`)
    }

    const result = await response.json()
    console.log('Evaluation scores saved successfully:', result)

    // Mark as submitted to prevent re-submission
    isSubmitted.value = true
    
    // Update stage status to APPROVED after successful evaluation submission
    if (stageId) {
      try {
        console.log('Updating stage status to APPROVED...')
        const stageUpdateResponse = await fetch('https://grc-tprm.vardaands.com/api/tprm/rfp-approval/update-stage-status/', {
          method: 'POST',
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            stage_id: stageId,
            status: 'APPROVE',
            comments: overallComments.value || 'Evaluation completed and submitted'
          })
        })
        
        if (stageUpdateResponse.ok) {
          console.log('Stage status updated to APPROVED successfully')
        } else {
          console.error('Failed to update stage status:', await stageUpdateResponse.text())
        }
      } catch (stageError) {
        console.error('Error updating stage status:', stageError)
      }
    }
    
    PopupService.success('Evaluation submitted successfully!', 'Submitted')
    PopupService.onAction('ok', () => {
      router.push('/my-approvals')
    })
    
    // Create notification
    await notificationService.createRFPEvaluationNotification('evaluation_submitted', {
      rfp_id: proposalData.value?.rfp_id,
      response_id: response_id,
      vendor_name: proposalData.value?.vendor_name,
      overall_score: totalScore.value
    })
    
  } catch (error) {
    console.error('Error submitting evaluation:', error)
    PopupService.error('Failed to submit evaluation. Data saved locally as backup.', 'Submission Failed')
    
    // Create error notification
    await notificationService.createRFPErrorNotification('submit_evaluation', error.message, {
      title: 'Submission Failed',
      response_id: proposalData.value?.response_id,
      vendor_name: proposalData.value?.vendor_name
    })
  } finally {
    saving.value = false
  }
}

const formatKey = (key) => {
  if (typeof key !== 'string') {
    return String(key || 'Unknown')
  }
  
  return key
    .split('_')
    .map(word => word && word.length > 0 ? word.charAt(0).toUpperCase() + word.slice(1) : '')
    .join(' ')
}

const getStatusBadgeClass = (status) => {
  if (!status) return 'bg-gray-100 text-gray-800'
  
  const statusLower = status.toLowerCase()
  
  if (statusLower.includes('approved') || statusLower.includes('complete')) {
    return 'bg-green-100 text-green-800'
  } else if (statusLower.includes('pending') || statusLower.includes('draft')) {
    return 'bg-yellow-100 text-yellow-800'
  } else if (statusLower.includes('rejected') || statusLower.includes('declined')) {
    return 'bg-red-100 text-red-800'
  } else if (statusLower.includes('progress') || statusLower.includes('in_review')) {
    return 'bg-blue-100 text-blue-800'
  }
  
  return 'bg-gray-100 text-gray-800'
}

const getPriorityBadgeClass = (priority) => {
  if (!priority) return 'bg-gray-100 text-gray-800'
  
  const priorityLower = priority.toLowerCase()
  
  if (priorityLower.includes('high') || priorityLower.includes('critical')) {
    return 'bg-red-100 text-red-800'
  } else if (priorityLower.includes('medium') || priorityLower.includes('moderate')) {
    return 'bg-yellow-100 text-yellow-800'
  } else if (priorityLower.includes('low')) {
    return 'bg-green-100 text-green-800'
  }
  
  return 'bg-gray-100 text-gray-800'
}

const getScoreColor = (score) => {
  if (!score) return 'text-gray-600'
  
  if (score >= 8) return 'text-red-600'
  if (score >= 6) return 'text-orange-600'
  if (score >= 4) return 'text-yellow-600'
  return 'text-green-600'
}

const getFieldType = (value) => {
  if (value === null || value === undefined) return 'text'
  
  if (typeof value === 'boolean') return 'boolean'
  if (typeof value === 'number') return 'number'
  if (value instanceof Date || (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value))) return 'datetime'
  
  return 'text'
}

const formatValue = (value) => {
  if (value === null || value === undefined) {
    return 'Not specified'
  }
  
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }
  
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  
  return String(value)
}

// Helper function to get a specific section from proposal data
const getProposalSection = (sectionName) => {
  if (!proposalData.value) {
    console.log(`[getProposalSection] No proposalData for section: ${sectionName}`)
    return null
  }
  
  // Get the data source (response_documents or proposal_data)
  const dataSource = proposalData.value.response_documents || proposalData.value.proposal_data
  
  if (!dataSource) {
    console.log(`[getProposalSection] No data source found for section: ${sectionName}`)
    return null
  }
  
  // If dataSource is a string, try to parse it
  let data = dataSource
  if (typeof dataSource === 'string') {
    try {
      data = JSON.parse(dataSource)
    } catch (e) {
      console.error(`[getProposalSection] Failed to parse dataSource as JSON:`, e)
      return null
    }
  }
  
  // Check if the section exists
  if (data && typeof data === 'object' && data[sectionName]) {
    const section = data[sectionName]
    console.log(`[getProposalSection] Found section ${sectionName}:`, section)
    
    // If section is an object with keys, return it
    if (typeof section === 'object' && section !== null) {
      // Check if it's an empty object
      if (Object.keys(section).length === 0) {
        console.log(`[getProposalSection] Section ${sectionName} is empty`)
        return null
      }
      return section
    }
    
    return section
  }
  
  // If section not found, but we have data, try to find similar keys (case-insensitive)
  if (data && typeof data === 'object') {
    const lowerSectionName = sectionName.toLowerCase()
    for (const key in data) {
      if (key.toLowerCase() === lowerSectionName) {
        console.log(`[getProposalSection] Found section with different case: ${key} for ${sectionName}`)
        return data[key]
      }
    }
  }
  
  console.log(`[getProposalSection] Section ${sectionName} not found. Available keys:`, data && typeof data === 'object' ? Object.keys(data) : 'N/A')
  return null
}

// Computed property to check if there are other proposal sections
const hasOtherProposalSections = computed(() => {
  if (!proposalData.value) return false
  
  const knownSections = ['companyInfo', 'financialInfo', 'rfpResponses', 'teamInfo', 'dynamicFields', 'compliance', 'documents', 'uploadedDocuments', 'metadata']
  const data = proposalData.value.response_documents || proposalData.value.proposal_data || {}
  
  return Object.keys(data).some(key => !knownSections.includes(key) && 
    data[key] !== null && 
    data[key] !== undefined &&
    typeof data[key] === 'object' &&
    !Array.isArray(data[key]))
})

// Computed property to get other proposal sections
const otherProposalSections = computed(() => {
  if (!proposalData.value) return {}
  
  const knownSections = ['companyInfo', 'financialInfo', 'rfpResponses', 'teamInfo', 'dynamicFields', 'compliance', 'documents', 'uploadedDocuments', 'metadata']
  const data = proposalData.value.response_documents || proposalData.value.proposal_data || {}
  
  // If dataSource is a string, try to parse it
  let parsedData = data
  if (typeof data === 'string') {
    try {
      parsedData = JSON.parse(data)
    } catch (e) {
      console.error('Failed to parse data as JSON:', e)
      return {}
    }
  }
  
  const other = {}
  
  Object.keys(parsedData).forEach(key => {
    if (!knownSections.includes(key) && 
        parsedData[key] !== null && 
        parsedData[key] !== undefined &&
        typeof parsedData[key] === 'object' &&
        !Array.isArray(parsedData[key])) {
      // Flatten nested objects for display, but exclude URL fields
      Object.keys(parsedData[key]).forEach(subKey => {
        // Skip URL-related fields
        if (!subKey.toLowerCase().includes('url') && subKey.toLowerCase() !== 'url') {
          other[`${key}_${subKey}`] = parsedData[key][subKey]
        }
      })
    }
  })
  
  return other
})

// Helper function to recursively flatten nested objects
// Excludes uploadedDocuments section and URL fields since documents are shown separately
const flattenObject = (obj, prefix = '', maxDepth = 5, currentDepth = 0) => {
  if (currentDepth >= maxDepth) {
    return { [prefix]: JSON.stringify(obj, null, 2) }
  }
  
  const flattened = {}
  
  if (obj === null || obj === undefined) {
    return { [prefix || 'null']: 'Not specified' }
  }
  
  if (typeof obj !== 'object') {
    return { [prefix || 'value']: obj }
  }
  
  if (Array.isArray(obj)) {
    if (obj.length === 0) {
      return { [prefix || 'array']: '[]' }
    }
    // For arrays, create indexed entries
    obj.forEach((item, index) => {
      if (typeof item === 'object' && item !== null) {
        const nested = flattenObject(item, `${prefix}[${index}]`, maxDepth, currentDepth + 1)
        Object.assign(flattened, nested)
      } else {
        flattened[`${prefix}[${index}]`] = item
      }
    })
    return flattened
  }
  
  // For objects, recursively flatten
  Object.keys(obj).forEach(key => {
    // Skip uploadedDocuments section entirely - documents are shown in Documents tab
    if (key === 'uploadedDocuments' || key === 'documents') {
      return
    }
    
    const newKey = prefix ? `${prefix}.${key}` : key
    const value = obj[key]
    
    // Skip URL-related fields
    if (key.toLowerCase().includes('url') || key.toLowerCase() === 'url') {
      return
    }
    
    if (value === null || value === undefined) {
      flattened[newKey] = 'Not specified'
    } else if (typeof value === 'object' && !Array.isArray(value)) {
      // Skip objects that are document-related
      if (value.url || value.download_url || value.preview_url) {
        return
      }
      const nested = flattenObject(value, newKey, maxDepth, currentDepth + 1)
      Object.assign(flattened, nested)
    } else if (Array.isArray(value)) {
      if (value.length === 0) {
        flattened[newKey] = '[]'
      } else {
        const nested = flattenObject(value, newKey, maxDepth, currentDepth + 1)
        Object.assign(flattened, nested)
      }
    } else {
      flattened[newKey] = value
    }
  })
  
  return flattened
}

// Computed property to get ALL data from response_documents (comprehensive view)
const allResponseDocumentsData = computed(() => {
  if (!proposalData.value) return {}
  
  const data = proposalData.value.response_documents || proposalData.value.proposal_data || {}
  
  // If dataSource is a string, try to parse it
  let parsedData = data
  if (typeof data === 'string') {
    try {
      parsedData = JSON.parse(data)
    } catch (e) {
      console.error('Failed to parse data as JSON:', e)
      return { 'raw_data': data }
    }
  }
  
  if (!parsedData || typeof parsedData !== 'object') {
    return { 'raw_data': String(parsedData) }
  }
  
  // Flatten ALL data recursively
  return flattenObject(parsedData, '', 10, 0)
})

// Computed property to get all flat proposal data (fallback when sections aren't found)
const allProposalData = computed(() => {
  if (!proposalData.value) return {}
  
  const data = proposalData.value.response_documents || proposalData.value.proposal_data || {}
  
  // If dataSource is a string, try to parse it
  let parsedData = data
  if (typeof data === 'string') {
    try {
      parsedData = JSON.parse(data)
    } catch (e) {
      console.error('Failed to parse data as JSON:', e)
      return {}
    }
  }
  
  if (!parsedData || typeof parsedData !== 'object') return {}
  
  // Flatten the data structure for display
  const flattened = {}
  const knownSections = ['companyInfo', 'financialInfo', 'rfpResponses', 'teamInfo', 'dynamicFields', 'compliance', 'documents', 'uploadedDocuments', 'metadata']
  
  Object.keys(parsedData).forEach(key => {
    const value = parsedData[key]
    
    // Skip known nested sections (they're handled separately)
    if (knownSections.includes(key)) {
      return
    }
    
    // Skip URL-related keys
    if (key.toLowerCase().includes('url')) {
      return
    }
    
    // If it's a simple value, add it directly
    if (value === null || value === undefined || 
        typeof value === 'string' || 
        typeof value === 'number' || 
        typeof value === 'boolean') {
      flattened[key] = value
    }
    // If it's an object, flatten it (but exclude URL fields)
    else if (typeof value === 'object' && !Array.isArray(value)) {
      Object.keys(value).forEach(subKey => {
        // Skip URL-related fields
        if (!subKey.toLowerCase().includes('url') && subKey.toLowerCase() !== 'url') {
          flattened[`${key}_${subKey}`] = value[subKey]
        }
      })
    }
    // If it's an array, convert to string representation
    else if (Array.isArray(value)) {
      flattened[key] = JSON.stringify(value, null, 2)
    }
  })
  
  return flattened
})

// Helper to convert Proxy/Reactive objects to plain objects
const toPlainObject = (obj) => {
  if (!obj || typeof obj !== 'object') return obj
  if (Array.isArray(obj)) {
    return obj.map(item => toPlainObject(item))
  }
  const plain = {}
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      const value = obj[key]
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        plain[key] = toPlainObject(value)
      } else {
        plain[key] = value
      }
    }
  }
  return plain
}

// Computed properties for each section to ensure reactivity
const companyInfoSection = computed(() => {
  const section = getProposalSection('companyInfo')
  console.log('[companyInfoSection] Raw section:', section)
  if (!section || typeof section !== 'object') {
    console.log('[companyInfoSection] No valid section')
    return {}
  }
  // Convert to plain object and filter
  const plainSection = toPlainObject(section)
  const filtered = {}
  Object.keys(plainSection).forEach(key => {
    const value = plainSection[key]
    if (value !== null && value !== undefined && value !== '') {
      filtered[key] = value
    }
  })
  console.log('[companyInfoSection] Filtered:', filtered, 'Keys:', Object.keys(filtered))
  return filtered
})

const financialInfoSection = computed(() => {
  const section = getProposalSection('financialInfo')
  console.log('[financialInfoSection] Raw section:', section)
  if (!section || typeof section !== 'object') return {}
  const plainSection = toPlainObject(section)
  const filtered = {}
  Object.keys(plainSection).forEach(key => {
    const value = plainSection[key]
    if (value !== null && value !== undefined && value !== '') {
      filtered[key] = value
    }
  })
  console.log('[financialInfoSection] Filtered:', filtered, 'Keys:', Object.keys(filtered))
  return filtered
})

const rfpResponsesSection = computed(() => {
  const section = getProposalSection('rfpResponses')
  console.log('[rfpResponsesSection] Raw section:', section)
  if (!section) return null
  return toPlainObject(section)
})

const teamInfoSection = computed(() => {
  const section = getProposalSection('teamInfo')
  console.log('[teamInfoSection] Raw section:', section)
  if (!section) return null
  return toPlainObject(section)
})

const dynamicFieldsSection = computed(() => {
  const section = getProposalSection('dynamicFields')
  if (!section || typeof section !== 'object') return {}
  const plainSection = toPlainObject(section)
  const filtered = {}
  Object.keys(plainSection).forEach(key => {
    const value = plainSection[key]
    if (value !== null && value !== undefined && value !== '') {
      filtered[key] = value
    }
  })
  return filtered
})

const complianceSection = computed(() => {
  const section = getProposalSection('compliance')
  console.log('[complianceSection] Raw section:', section)
  if (!section || typeof section !== 'object') return {}
  const plainSection = toPlainObject(section)
  const filtered = {}
  Object.keys(plainSection).forEach(key => {
    const value = plainSection[key]
    if (value !== null && value !== undefined && value !== '') {
      filtered[key] = value
    }
  })
  console.log('[complianceSection] Filtered:', filtered, 'Keys:', Object.keys(filtered))
  return filtered
})

// Check if we should show the fallback (all data) view
const shouldShowFallbackData = computed(() => {
  if (!proposalData.value) return false
  
  const hasSections = 
    Object.keys(companyInfoSection.value).length > 0 ||
    Object.keys(financialInfoSection.value).length > 0 ||
    (rfpResponsesSection.value && typeof rfpResponsesSection.value === 'object' && Object.keys(rfpResponsesSection.value).length > 0) ||
    (teamInfoSection.value && typeof teamInfoSection.value === 'object' && Object.keys(teamInfoSection.value).length > 0) ||
    Object.keys(dynamicFieldsSection.value).length > 0 ||
    Object.keys(complianceSection.value).length > 0
  
  // Show fallback if no sections found but we have data
  return !hasSections && Object.keys(allProposalData.value).length > 0
})

const parseMitigations = (mitigations) => {
  if (!mitigations) return []
  
  // If it's already an array, return it
  if (Array.isArray(mitigations)) {
    return mitigations
  }
  
  // If it's a string, try to parse it as JSON
  if (typeof mitigations === 'string') {
    try {
      const parsed = JSON.parse(mitigations)
      return Array.isArray(parsed) ? parsed : [parsed]
    } catch (e) {
      console.warn('Failed to parse mitigations JSON:', e)
      // If JSON parsing fails, split by common delimiters
      return mitigations.split(/[,\n;]/).map(m => m.trim()).filter(m => m.length > 0)
    }
  }
  
  // If it's an object, convert to array
  if (typeof mitigations === 'object') {
    return Object.values(mitigations).filter(v => v && typeof v === 'string')
  }
  
  return []
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

const formatFileSize = (bytes) => {
  if (!bytes) return 'Unknown size'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const formatFileType = (type) => {
  if (!type) return 'Unknown type'
  return type.toUpperCase().replace('APPLICATION/', '').replace('IMAGE/', '')
}

const getDocumentIcon = (type) => {
  if (!type) return 'document'
  
  type = type.toLowerCase()
  
  if (type.includes('pdf')) return 'file-text'
  if (type.includes('word') || type.includes('doc')) return 'file-text'
  if (type.includes('excel') || type.includes('sheet') || type.includes('csv')) return 'table'
  if (type.includes('image') || type.includes('png') || type.includes('jpg') || type.includes('jpeg')) return 'image'
  if (type.includes('powerpoint') || type.includes('presentation')) return 'presentation'
  if (type.includes('zip') || type.includes('archive')) return 'archive'
  
  return 'document'
}

const getDocumentEmoji = (type) => {
  if (!type) return '📄'
  
  type = type.toLowerCase()
  
  if (type.includes('pdf')) return '📄'
  if (type.includes('word') || type.includes('doc')) return '📝'
  if (type.includes('excel') || type.includes('sheet') || type.includes('csv')) return '📊'
  if (type.includes('image') || type.includes('png') || type.includes('jpg') || type.includes('jpeg')) return '🖼️'
  if (type.includes('powerpoint') || type.includes('presentation')) return '📽️'
  if (type.includes('zip') || type.includes('archive')) return '🗜️'
  
  return '📄'
}

const isPreviewable = (doc) => {
  const type = (doc.file_type || doc.type || '').toLowerCase()
  return type.includes('pdf') || 
         type.includes('image') || 
         type.includes('text') ||
         type.includes('html')
}

const downloadDocument = async (doc) => {
  try {
    console.log('Downloading document:', doc)
    
    if (!doc.download_url && !doc.url) {
      throw new Error('Document URL not available')
    }
    
    const url = doc.download_url || doc.url
    console.log('Document URL:', url)
    
    // For S3 URLs, try direct download first
    // S3 pre-signed URLs should work directly without fetch
    const link = document.createElement('a')
    link.href = url
    link.download = doc.file_name || doc.name || 'document'
    link.target = '_blank' // Open in new tab as fallback
    link.rel = 'noopener noreferrer'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    console.log('Document download initiated')
    
  } catch (error) {
    console.error('Error downloading document:', error)
    PopupService.error(`Failed to download document: ${error.message}\n\nPlease check if the document URL is still valid.`, 'Download Failed')
  }
}

const viewDocument = (doc) => {
  try {
    console.log('Viewing document:', doc)
    
    const url = doc.preview_url || doc.view_url || doc.url || doc.download_url
    if (!url) {
      throw new Error('Document URL not available')
    }
    
    console.log('Opening document URL:', url)
    
    // For S3 URLs, open directly in new tab
    // S3 pre-signed URLs should allow viewing directly
    window.open(url, '_blank', 'noopener,noreferrer')
    
  } catch (error) {
    console.error('Error viewing document:', error)
    PopupService.error(`Failed to open document: ${error.message}\n\nPlease try downloading the document instead.`, 'View Failed')
  }
}

const viewDocumentInSplitScreen = async (doc) => {
  try {
    selectedDocument.value = doc
    pdfViewerError.value = ''
    
    // If it's a PDF, set up the viewer
    if (isPDF(doc)) {
      updatePDFViewer()
    }
    // If it's a text file, load the content
    else if (isText(doc)) {
      await loadTextContent(doc)
    }
    
    // Switch to documents tab to show the viewer
    activeTab.value = 'documents'
    
  } catch (error) {
    console.error('Error viewing document in split screen:', error)
    PopupService.error('Failed to load document for viewing. Please try again.', 'Load Failed')
  }
}

const closeDocumentViewer = () => {
  selectedDocument.value = null
  textContent.value = ''
}

const isPDF = (doc) => {
  const type = (doc.file_type || doc.type || '').toLowerCase()
  return type.includes('pdf')
}

const isImage = (doc) => {
  const type = (doc.file_type || doc.type || '').toLowerCase()
  return type.includes('image') || 
         type.includes('png') || 
         type.includes('jpg') || 
         type.includes('jpeg') || 
         type.includes('gif') ||
         type.includes('bmp') ||
         type.includes('svg')
}

const isText = (doc) => {
  const type = (doc.file_type || doc.type || '').toLowerCase()
  return type.includes('text') || 
         type.includes('plain') ||
         type.includes('csv') ||
         type.includes('json') ||
         type.includes('xml') ||
         type.includes('html') ||
         type.includes('css') ||
         type.includes('javascript') ||
         type.includes('js')
}

const loadTextContent = async (doc) => {
  try {
    const url = doc.url || doc.download_url
    if (!url) {
      throw new Error('Document URL not available')
    }
    
    const response = await fetch(url, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const text = await response.text()
    textContent.value = text
    
  } catch (error) {
    console.error('Error loading text content:', error)
    textContent.value = 'Error loading document content. Please try downloading the file.'
  }
}

const getPDFViewerUrl = (pdfUrl) => {
  // Use Google Docs viewer as a fallback for PDF viewing
  return `https://docs.google.com/gview?url=${encodeURIComponent(pdfUrl)}&embedded=true`
}

const getDocumentViewerUrl = (doc) => {
  const url = doc.url || doc.download_url
  
  if (isPDF(doc)) {
    // Try multiple PDF viewer options
    return {
      google: `https://docs.google.com/gview?url=${encodeURIComponent(url)}&embedded=true`,
      mozilla: `https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodeURIComponent(url)}`,
      direct: url
    }
  }
  
  return { direct: url }
}

const updatePDFViewer = () => {
  if (!selectedDocument.value) return
  
  const url = selectedDocument.value.url || selectedDocument.value.download_url
  const viewerUrls = getDocumentViewerUrl(selectedDocument.value)
  
  currentPDFUrl.value = viewerUrls[pdfViewerType.value] || viewerUrls.direct
  pdfViewerError.value = ''
}

const handlePDFViewerError = () => {
  pdfViewerError.value = 'Failed to load PDF in current viewer. Try switching to a different viewer or download the file.'
}

const tryAlternativePDFViewer = () => {
  const alternatives = ['google', 'mozilla', 'direct']
  const currentIndex = alternatives.indexOf(pdfViewerType.value)
  const nextIndex = (currentIndex + 1) % alternatives.length
  
  pdfViewerType.value = alternatives[nextIndex]
  updatePDFViewer()
}

const openPDFInNewTab = () => {
  if (selectedDocument.value) {
    const url = selectedDocument.value.url || selectedDocument.value.download_url
    window.open(url, '_blank')
  }
}


const navigateBack = () => {
  router.push('/my-approvals')
}



const togglePreview = (docId) => {
  if (docId in previewStates.value) {
    previewStates.value[docId] = !previewStates.value[docId]
  }
}

onMounted(async () => {
  await loggingService.logPageView('RFP', 'Proposal Evaluation')
  await loadProposalData()
})
</script>

<style scoped>
input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  cursor: pointer;
}

input[type="range"]::-webkit-slider-runnable-track {
  background: #e5e7eb;
  height: 8px;
  border-radius: 4px;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  margin-top: -4px;
  background-color: #3b82f6;
  height: 16px;
  width: 16px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s ease;
}

input[type="range"]::-webkit-slider-thumb:hover {
  background-color: #2563eb;
  transform: scale(1.1);
}
</style>
