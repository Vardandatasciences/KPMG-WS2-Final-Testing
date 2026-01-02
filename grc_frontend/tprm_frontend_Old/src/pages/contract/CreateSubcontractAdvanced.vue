<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button @click="navigate(id ? `/contracts/${id}/edit-advanced` : '/contracts')" class="p-2 hover:bg-muted rounded-md">
          <ArrowLeft class="w-4 h-4" />
        </button>
        <div>
          <h1 class="text-3xl font-bold">Create Subcontract</h1>
          <p class="text-muted-foreground">
            {{ id ? `Parent Contract #${id} • Delegate work to subcontractor` : 'Create a new subcontract for work delegation' }}
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button @click="showOCR = !showOCR" class="inline-flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-muted">
          <Upload class="w-4 h-4" />
          OCR Upload
        </button>
        <button @click="handleSaveDraft" class="inline-flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-muted">
          <Save class="w-4 h-4" />
          Save Draft
        </button>
        <button @click="debugFormData" class="inline-flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-muted">
          <Search class="w-4 h-4" />
          Debug Form
        </button>
        
        <!-- Version Type Selector -->
        <div class="flex items-center gap-2">
          <label class="text-sm font-medium">Version Type:</label>
          <select v-model="versionType" class="px-3 py-1 border rounded-md text-sm">
            <option value="minor">Minor Version</option>
            <option value="major">Major Version</option>
          </select>
        </div>
        
        <button @click="handleSubmitForReview" :disabled="isSubmitting" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50">
          <Send class="w-4 h-4" />
          {{ isSubmitting ? 'Creating...' : 'Submit for Review' }}
        </button>
      </div>
    </div>

    <!-- Preview Dialog -->
    <div v-if="showPreview" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" :key="`preview-${previewTimestamp}`">
      <div class="bg-background border rounded-lg max-w-6xl max-h-[90vh] overflow-y-auto w-full mx-4">
        <div class="p-6 border-b">
          <h2 class="text-xl font-semibold flex items-center gap-2">
            <Eye class="w-5 h-5" />
            Contract & Subcontract Preview
          </h2>
          <p class="text-sm text-muted-foreground">Review both main contract and subcontract details before submitting for approval</p>
          <!-- Debug info to confirm fresh data -->
          <div class="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-xs">
            <strong>Preview Generated:</strong> {{ new Date(previewTimestamp).toLocaleTimeString() }} |
            <strong>Form Title:</strong> "{{ formData.title }}" |
            <strong>Value:</strong> {{ formData.value }}
          </div>
        </div>
        
        <div class="p-6 space-y-6">
          <!-- Main Contract Information -->
          <div v-if="mainContractData" class="space-y-3">
            <h3 class="text-lg font-semibold border-b pb-2 text-blue-600">Main Contract Details</h3>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="font-medium">Contract Title:</span>
                <p class="text-muted-foreground">{{ mainContractData.contract_title || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Contract Number:</span>
                <p class="text-muted-foreground">{{ mainContractData.contract_number || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Contract Type:</span>
                <p class="text-muted-foreground">{{ mainContractData.contract_type || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Contract Value:</span>
                <p class="text-muted-foreground">
                  {{ mainContractData.contract_value ? `${mainContractData.currency} ${Number(mainContractData.contract_value).toLocaleString()}` : "Not specified" }}
                </p>
              </div>
              <div>
                <span class="font-medium">Start Date:</span>
                <p class="text-muted-foreground">{{ mainContractData.start_date || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">End Date:</span>
                <p class="text-muted-foreground">{{ mainContractData.end_date || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Contract Owner:</span>
                <p class="text-muted-foreground">{{ mainContractData.contract_owner || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Legal Reviewer:</span>
                <p class="text-muted-foreground">{{ mainContractData.legal_reviewer || "Not specified" }}</p>
              </div>
            </div>
          </div>

          <!-- Subcontract Information -->
          <div class="space-y-3">
            <h3 class="text-lg font-semibold border-b pb-2 text-green-600">Subcontract Details</h3>
            <div class="space-y-3">
              <h4 class="text-md font-semibold border-b pb-1">Primary Information</h4>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="font-medium">Title:</span>
                <p class="text-muted-foreground">{{ formData.title || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Contract Number:</span>
                <p class="text-muted-foreground">{{ formData.contract_number || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Type:</span>
                <p class="text-muted-foreground">{{ formData.type || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Risk Level:</span>
                <p class="text-muted-foreground">{{ formData.risk_level || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Contract Category:</span>
                <p class="text-muted-foreground">{{ formData.contract_category || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Parent Contract ID:</span>
                <p class="text-muted-foreground">{{ formData.parent_contract_id || "Not specified" }}</p>
              </div>
              <div class="col-span-2">
                <span class="font-medium">Description:</span>
                <p class="text-muted-foreground">{{ formData.description || "Not specified" }}</p>
              </div>
            </div>
          </div>
          </div>


          <!-- Financial Details -->
          <div class="space-y-3">
            <h3 class="text-lg font-semibold border-b pb-2">Financial Details</h3>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="font-medium">Value:</span>
                <p class="text-muted-foreground">
                  {{ formData.value ? `${formData.currency} ${Number(formData.value).toLocaleString()}` : "Not specified" }}
                </p>
              </div>
              <div>
                <span class="font-medium">Currency:</span>
                <p class="text-muted-foreground">{{ formData.currency }}</p>
              </div>
              <div>
                <span class="font-medium">Liability Cap:</span>
                <p class="text-muted-foreground">
                  {{ formData.liability_cap ? `${formData.currency} ${Number(formData.liability_cap).toLocaleString()}` : "Not specified" }}
                </p>
              </div>
            </div>
          </div>

          <!-- Dates & Terms -->
          <div class="space-y-3">
            <h3 class="text-lg font-semibold border-b pb-2">Dates & Terms</h3>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="font-medium">Start Date:</span>
                <p class="text-muted-foreground">{{ formData.start_date || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">End Date:</span>
                <p class="text-muted-foreground">{{ formData.end_date || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Notice Period:</span>
                <p class="text-muted-foreground">{{ formData.notice_period_days }} days</p>
              </div>
              <div>
                <span class="font-medium">Auto Renewal:</span>
                <p class="text-muted-foreground">{{ formData.auto_renew ? "Enabled" : "Disabled" }}</p>
              </div>
            </div>
          </div>


          <!-- Contract Terms -->
          <div v-if="contractTerms.length > 0" class="space-y-3">
            <h3 class="text-lg font-semibold border-b pb-2">Contract Terms ({{ contractTerms.length }})</h3>
            <div class="space-y-2">
              <div v-for="(term, index) in contractTerms" :key="term.term_id" class="border rounded p-3 text-sm">
                <div class="font-medium">{{ term.term_title || `Term #${index + 1}` }}</div>
                <div class="text-muted-foreground">Category: {{ term.term_category }}</div>
                <div class="text-muted-foreground">Risk Level: {{ term.risk_level }}</div>
                <div v-if="term.term_text" class="text-muted-foreground mt-1 text-xs">{{ term.term_text.substring(0, 100) }}...</div>
              </div>
            </div>
          </div>

          <!-- Contract Clauses -->
          <div v-if="contractClauses.length > 0" class="space-y-3">
            <h3 class="text-lg font-semibold border-b pb-2">Contract Clauses ({{ contractClauses.length }})</h3>
            <div class="space-y-2">
              <div v-for="(clause, index) in contractClauses" :key="clause.clause_id" class="border rounded p-3 text-sm">
                <div class="font-medium">{{ clause.clause_name || `Clause #${index + 1}` }}</div>
                <div class="text-muted-foreground">Type: {{ clause.clause_type }}</div>
                <div class="text-muted-foreground">Risk Level: {{ clause.risk_level }}</div>
                <div v-if="clause.clause_text" class="text-muted-foreground mt-1 text-xs">{{ clause.clause_text.substring(0, 100) }}...</div>
              </div>
            </div>
          </div>


          <!-- Compliance -->
          <div v-if="formData.compliance_frameworks.length > 0" class="space-y-3">
            <h3 class="text-lg font-semibold border-b pb-2">Compliance Frameworks</h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="framework in formData.compliance_frameworks" :key="framework" class="px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs">
                {{ framework }}
              </span>
            </div>
          </div>

          <!-- Legal & Risk Management -->
          <div class="space-y-3">
            <h3 class="text-lg font-semibold border-b pb-2">Legal & Risk Management</h3>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="font-medium">Risk Score:</span>
                <p class="text-muted-foreground">{{ formData.contract_risk_score || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Dispute Resolution:</span>
                <p class="text-muted-foreground">{{ formData.dispute_resolution || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Governing Law:</span>
                <p class="text-muted-foreground">{{ formData.governing_law || "Not specified" }}</p>
              </div>
              <div>
                <span class="font-medium">Termination Clause:</span>
                <p class="text-muted-foreground">{{ formData.termination_clause || "Not specified" }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="p-6 border-t flex justify-end gap-2">
          <button @click="handleEditSubcontract" class="inline-flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-muted">
            <Edit class="w-4 h-4" />
            Edit Subcontract
          </button>
          <button @click="handleFinalSubmit" :disabled="isSubmitting" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50">
            <Send class="w-4 h-4" />
            {{ isSubmitting ? 'Creating...' : 'Submit for Review' }}
          </button>
        </div>
      </div>
    </div>

      <!-- OCR Upload Section -->
      <div v-if="showOCR" class="border rounded-lg bg-card">
        <div class="p-6 border-b">
          <h3 class="text-lg font-semibold flex items-center gap-2">
            <Upload class="w-5 h-5" />
            OCR Document Upload
          </h3>
          <p class="text-sm text-muted-foreground">Upload a subcontract document to auto-populate fields using OCR</p>
        </div>
        <div class="p-6">
          <!-- OCR Error Message -->
          <div v-if="errors.ocr" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div class="flex items-center gap-2 text-red-800">
              <AlertTriangle class="w-5 h-5" />
              <span>{{ errors.ocr }}</span>
            </div>
          </div>
          
          <div 
            v-if="uploadStep === 'upload'" 
            :class="[
              'border-2 border-dashed rounded-lg p-8 text-center transition-colors',
              isDragOver 
                ? 'border-primary bg-primary/5' 
                : 'border-muted-foreground/25 hover:border-primary/50'
            ]"
            @dragover.prevent="handleDragOver"
            @dragenter.prevent="handleDragEnter"
            @dragleave.prevent="handleDragLeave"
            @drop.prevent="handleFileDrop"
          >
            <FileText class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 class="text-lg font-semibold mb-2">Upload Subcontract Document</h3>
            <p class="text-muted-foreground mb-4">Drag and drop or click to select • Supports PDF, PNG, JPG, TIFF files up to 10MB</p>
            <div class="relative">
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.tiff"
                @change="handleFileUpload"
                class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <button class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                <Upload class="w-4 h-4" />
                Choose File
              </button>
            </div>
          </div>

          <div v-if="uploadStep === 'processing'" class="space-y-4">
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span>Processing: {{ selectedFile?.name }}</span>
                <span>{{ uploadProgress }}%</span>
              </div>
              <div class="w-full bg-secondary rounded-full h-2">
                <div class="bg-primary h-2 rounded-full transition-all duration-300" :style="{ width: uploadProgress + '%' }"></div>
              </div>
            </div>
            <div class="text-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p class="text-muted-foreground">Analyzing document and extracting subcontract data...</p>
            </div>
          </div>

          <div v-if="uploadStep === 'review'" class="space-y-4">
            <!-- S3 Upload Status -->
            <div v-if="s3UploadInfo" class="p-4 border rounded-lg" :class="s3UploadInfo.success ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'">
              <div class="flex items-center gap-2">
                <CheckCircle v-if="s3UploadInfo.success" class="w-5 h-5 text-green-600" />
                <AlertTriangle v-else class="w-5 h-5 text-yellow-600" />
                <div>
                  <h4 class="font-medium" :class="s3UploadInfo.success ? 'text-green-800' : 'text-yellow-800'">
                    {{ s3UploadInfo.success ? 'Document Stored Successfully' : 'Storage Notice' }}
                  </h4>
                  <p class="text-sm" :class="s3UploadInfo.success ? 'text-green-600' : 'text-yellow-600'">
                    {{ s3UploadInfo.success ? 'Your subcontract document has been securely uploaded to cloud storage.' : s3UploadInfo.error || 'Cloud storage is temporarily unavailable.' }}
                  </p>
                  <div v-if="!s3UploadInfo.success" class="mt-2 p-2 bg-yellow-100 rounded text-xs text-yellow-800">
                    <strong>Note:</strong> Your document has been processed successfully. You can still proceed with subcontract creation.
                  </div>
                  <p v-if="s3UploadInfo.success && s3UploadInfo.file_info?.url" class="text-xs text-green-500 mt-1">
                    Storage URL: {{ s3UploadInfo.file_info.url }}
                  </p>
                </div>
              </div>
            </div>
            
            <div class="space-y-3">
              <div v-for="(result, index) in ocrResults" :key="index" class="flex items-center justify-between p-3 border rounded-lg">
                <div class="flex-1 space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-sm">{{ result.field.replace('_', ' ').toUpperCase() }}</span>
                    <AlertTriangle v-if="result.needsReview" class="w-4 h-4 text-warning" />
                    <CheckCircle v-else class="w-4 h-4 text-success" />
                  </div>
                  <!-- Contract Value or Liability Cap -->
                  <input
                    v-if="result.field === 'value' || result.field === 'liability_cap'"
                    type="number"
                    :value="result.value"
                    @input="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                    placeholder="Enter amount (e.g., 50000)"
                  />
                  
                  <!-- Date fields -->
                  <input
                    v-else-if="result.field === 'start_date' || result.field === 'end_date'"
                    type="date"
                    :value="result.value"
                    @input="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                  />
                  
                  <!-- Notice Period -->
                  <input
                    v-else-if="result.field === 'notice_period_days'"
                    type="number"
                    :value="result.value"
                    @input="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                    placeholder="Enter number of days"
                  />
                  
                  <!-- Contract Risk Score -->
                  <input
                    v-else-if="result.field === 'contract_risk_score'"
                    type="number"
                    step="0.1"
                    min="0"
                    max="10"
                    :value="result.value"
                    @input="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                    placeholder="Enter risk score (0-10)"
                  />
                  
                  <!-- Auto Renewal -->
                  <select
                    v-else-if="result.field === 'auto_renew'"
                    :value="result.value"
                    @change="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                  >
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                  
                  <!-- Risk Level -->
                  <select
                    v-else-if="result.field === 'risk_level'"
                    :value="result.value"
                    @change="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                  
                  <!-- Contract Type -->
                  <select
                    v-else-if="result.field === 'type'"
                    :value="result.value"
                    @change="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                  >
                    <option value="SOW">Statement of Work (SOW)</option>
                    <option value="SERVICE_AGREEMENT">Service Agreement</option>
                    <option value="PURCHASE_ORDER">Purchase Order</option>
                    <option value="LICENSE">License</option>
                    <option value="NDA">Non-Disclosure Agreement (NDA)</option>
                  </select>
                  
                  <!-- Contract Category -->
                  <select
                    v-else-if="result.field === 'contract_category'"
                    :value="result.value"
                    @change="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                  >
                    <option value="goods">Goods</option>
                    <option value="services">Services</option>
                    <option value="technology">Technology</option>
                    <option value="consulting">Consulting</option>
                    <option value="others">Others</option>
                  </select>
                  
                  <!-- Dispute Resolution -->
                  <select
                    v-else-if="result.field === 'dispute_resolution'"
                    :value="result.value"
                    @change="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                  >
                    <option value="negotiation">Negotiation</option>
                    <option value="mediation">Mediation</option>
                    <option value="arbitration">Arbitration</option>
                    <option value="litigation">Litigation</option>
                  </select>
                  
                  <!-- Termination Clause -->
                  <select
                    v-else-if="result.field === 'termination_clause'"
                    :value="result.value"
                    @change="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                  >
                    <option value="convenience">Convenience</option>
                    <option value="cause">Cause</option>
                    <option value="both">Both</option>
                    <option value="none">None</option>
                  </select>
                  
                  <!-- Terms, Clauses, Renewal, Termination, Insurance, Data Protection -->
                  <textarea
                    v-else-if="result.field.startsWith('term_') || result.field.startsWith('clause_') || result.field.startsWith('renewal_') || result.field.startsWith('termination_') || result.field.startsWith('insurance_') || result.field.startsWith('data_protection_') || result.field === 'renewal_terms' || result.field === 'description'"
                    :value="result.value"
                    @input="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                    rows="3"
                    placeholder="Enter detailed text..."
                  ></textarea>
                  
                  <!-- Default text input -->
                  <input
                    v-else
                    type="text"
                    :value="result.value"
                    @input="handleOCRValueChange(result.field, $event.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground text-sm"
                  />
                </div>
                <div class="ml-4">
                  <span :class="getConfidenceBadgeClass(result.confidence)" class="px-2 py-1 rounded text-xs font-medium">
                    {{ result.confidence >= 90 ? 'High' : result.confidence >= 70 ? 'Medium' : 'Low' }} ({{ result.confidence }}%)
                  </span>
                </div>
              </div>
            </div>
            
            <div class="flex justify-between items-center pt-4 border-t">
              <div class="text-sm text-muted-foreground">
                {{ ocrResults.filter(r => r.needsReview).length }} fields need review
              </div>
              <div class="flex gap-2">
                <button @click="showOCR = false" class="px-4 py-2 border rounded-md hover:bg-muted">
                  Cancel
                </button>
                <button @click="applyOCRData" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                  <Eye class="w-4 h-4" />
                  Apply to Form
                </button>
                <button @click="applyOCRDataWithClear" class="inline-flex items-center gap-2 px-4 py-2 border border-destructive text-destructive rounded-md hover:bg-destructive hover:text-destructive-foreground">
                  <Trash2 class="w-4 h-4" />
                  Clear & Apply
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Success Message -->
      <div v-if="successMessage" class="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div class="flex items-center gap-2 text-green-800">
          <CheckCircle class="w-5 h-5" />
          <span>{{ successMessage }}</span>
        </div>
      </div>

      <!-- Error Messages -->
      <div v-if="errors.general" class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
        <div class="flex items-center gap-2 text-red-800">
          <AlertTriangle class="w-5 h-5" />
          <span>{{ errors.general }}</span>
        </div>
      </div>

      <!-- Risk Analysis Notification -->
      <div v-if="showRiskAnalysisNotification" class="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div class="flex items-center gap-2 text-blue-800">
          <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span class="text-sm">Risk analysis is running in the background. You can continue working while it completes.</span>
          <button @click="showRiskAnalysisNotification = false" class="ml-auto p-1 hover:bg-blue-100 rounded">
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Risk Analysis Triggered Notification -->
      <div v-if="showRiskAnalysisTriggered" class="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div class="flex items-center gap-2 text-green-800">
          <CheckCircle class="w-4 h-4" />
          <span class="text-sm">Risk analysis has been triggered and will run in the background.</span>
          <button @click="showRiskAnalysisTriggered = false" class="ml-auto p-1 hover:bg-green-100 rounded">
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="space-y-6" :key="formKey">
        <div class="flex border-b overflow-x-auto">
          <button
            v-for="tab in tabs"
            :key="tab.value"
            @click="activeTab = tab.value"
            :class="[
              'px-4 py-2 border-b-2 transition-colors whitespace-nowrap',
              activeTab === tab.value
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            ]"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab Content -->
        <div v-if="activeTab === 'basic'" class="space-y-6">
          <!-- Basic Information Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <FileText class="w-5 h-5" />
                Primary Information
              </h3>
              <p class="text-sm text-muted-foreground">Enter the fundamental subcontract details</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium">Subcontract Title *</label>
                  <input
                    id="title"
                    :value="formData.title"
                    @input="(e) => {
                      const oldValue = formData.title;
                      formData.title = e.target.value;
                      console.log('📝 Title updated:');
                      console.log('  - Old value:', oldValue);
                      console.log('  - New value:', formData.title);
                      console.log('  - formData.value object:', formData);
                    }"
                    placeholder="e.g., UI/UX Design Services Subcontract"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  />
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Contract Number</label>
                  <input
                    id="contract_number"
                    :value="formData.contract_number"
                    @input="(e) => formData.contract_number = e.target.value"
                    placeholder="e.g., SUB-2024-001"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  />
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium flex items-center gap-2">
                    Vendor *
                    <span v-if="formData.vendor_id && mainContractData?.vendor?.vendor_id === formData.vendor_id" class="text-xs text-blue-600">
                      (From Parent Contract)
                    </span>
                  </label>
                  <select
                    :value="formData.vendor_id"
                    @change="handleVendorChange"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  >
                    <option value="">Select a vendor</option>
                    <option 
                      v-for="vendor in availableVendors" 
                      :key="vendor.vendor_id" 
                      :value="vendor.vendor_id"
                    >
                      {{ vendor.company_name }} ({{ vendor.vendor_code || vendor.vendor_id }})
                    </option>
                  </select>
                  <p v-if="formData.vendor_id" class="text-xs text-muted-foreground">
                    Selected Vendor ID: {{ formData.vendor_id }}
                  </p>
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Contract Type *</label>
                  <select 
                    :value="formData.type"
                    @change="(e) => {
                      formData.type = e.target.value;
                      console.log('📝 Type updated:', formData.type);
                    }"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  >
                    <option value="">Select contract type</option>
                    <option value="SOW">Statement of Work (SOW)</option>
                    <option value="SERVICE_AGREEMENT">Service Agreement</option>
                    <option value="PURCHASE_ORDER">Purchase Order</option>
                    <option value="LICENSE">License</option>
                    <option value="NDA">Non-Disclosure Agreement (NDA)</option>
                  </select>
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Risk Level *</label>
                  <select :value="formData.risk_level" @change="(e) => formData.risk_level = e.target.value" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                    <option value="">Select risk level</option>
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Contract Category</label>
                  <select :value="formData.contract_category" @change="(e) => formData.contract_category = e.target.value" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                    <option value="">Select category</option>
                    <option value="goods">Goods</option>
                    <option value="services">Services</option>
                    <option value="technology">Technology</option>
                    <option value="consulting">Consulting</option>
                    <option value="others">Others</option>
                  </select>
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Parent Contract ID</label>
                  <input
                    :value="formData.parent_contract_id"
                    @input="(e) => formData.parent_contract_id = e.target.value"
                    placeholder="e.g., 1001 (optional)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  />
                </div>
              </div>

              <div class="space-y-2">
                <label class="text-sm font-medium">Description</label>
                <textarea
                  id="description"
                  :value="formData.description"
                  @input="(e) => formData.description = e.target.value"
                  placeholder="Brief description of the subcontract purpose and scope..."
                  rows="3"
                  class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                ></textarea>
              </div>

              <!-- Subcontract Visibility Permission -->
              <div class="space-y-2 border-t pt-4 mt-4">
                <div class="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    id="permission_required"
                    :checked="formData.permission_required"
                    @change="(e) => formData.permission_required = e.target.checked"
                    class="mt-1 rounded border-gray-300"
                  />
                  <div>
                    <label for="permission_required" class="text-sm font-medium cursor-pointer">
                      Allow parent contract to view this subcontract
                    </label>
                    <p class="text-xs text-muted-foreground mt-1">
                      Enable this to grant the parent contract permission to view and access this subcontract's details.
                      If disabled, this subcontract will remain private and separate from the parent contract.
                    </p>
                  </div>
                </div>
              </div>

            </div>
          </div>

        </div>

        <div v-if="activeTab === 'financial'" class="space-y-6">
          <!-- Financial Details Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <DollarSign class="w-5 h-5" />
                Financial Details
              </h3>
              <p class="text-sm text-muted-foreground">Set subcontract value and financial terms</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium">Contract Value *</label>
                  <input
                    id="value"
                    :value="formData.value"
                    @input="(e) => {
                      const oldValue = formData.value;
                      formData.value = e.target.value;
                      console.log('💰 Contract Value updated:');
                      console.log('  - Old value:', oldValue);
                      console.log('  - New value:', formData.value);
                    }"
                    type="number"
                    placeholder="50000"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  />
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Currency</label>
                  <select :value="formData.currency" @change="(e) => formData.currency = e.target.value" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                    <option value="USD">USD - US Dollar</option>
                    <option value="EUR">EUR - Euro</option>
                    <option value="GBP">GBP - British Pound</option>
                    <option value="CAD">CAD - Canadian Dollar</option>
                  </select>
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Liability Cap</label>
                  <input
                    id="liability_cap"
                    :value="formData.liability_cap"
                    @input="(e) => formData.liability_cap = e.target.value"
                    type="number"
                    placeholder="e.g., 75000"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'dates'" class="space-y-6">
          <!-- Dates & Terms Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <Calendar class="w-5 h-5" />
                Dates & Terms
              </h3>
              <p class="text-sm text-muted-foreground">Define subcontract duration and renewal terms</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium">Start Date *</label>
                  <input
                    id="start_date"
                    :value="formData.start_date"
                    @input="(e) => {
                      formData.start_date = e.target.value;
                      console.log('📝 Start date updated:', formData.start_date);
                    }"
                    type="date"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  />
                </div>
                
                <div class="space-y-2">
                  <label class="text-sm font-medium">End Date *</label>
                  <input
                    id="end_date"
                    :value="formData.end_date"
                    @input="(e) => {
                      formData.end_date = e.target.value;
                      console.log('📝 End date updated:', formData.end_date);
                    }"
                    type="date"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  />
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Notice Period (Days)</label>
                  <input
                    id="notice_period_days"
                    :value="formData.notice_period_days"
                    @input="(e) => formData.notice_period_days = e.target.value"
                    type="number"
                    placeholder="30"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  />
                </div>
              </div>

            </div>
          </div>
        </div>

        <div v-if="activeTab === 'stakeholders'" class="space-y-6">
          <!-- Stakeholders & Responsibilities Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <Users class="w-5 h-5" />
                Stakeholders & Responsibilities
              </h3>
              <p class="text-sm text-muted-foreground">
                Assign subcontract ownership and reviewers
              </p>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium">Contract Owner *</label>
                  <select 
                    :value="formData.contract_owner" 
                    @change="(e) => formData.contract_owner = parseInt(e.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  >
                    <option value="">Select contract owner</option>
                    <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                      {{ user.display_name }} (ID: {{ user.user_id }})
                    </option>
                  </select>
                  <div class="text-sm text-gray-500">Select the user who will own this subcontract</div>
                </div>
                
                <div class="space-y-2">
                  <label class="text-sm font-medium">Legal Reviewer</label>
                  <select 
                    :value="formData.legal_reviewer" 
                    @change="(e) => formData.legal_reviewer = parseInt(e.target.value)"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  >
                    <option value="">Select legal reviewer</option>
                    <option v-for="reviewer in legalReviewers" :key="reviewer.user_id" :value="reviewer.user_id">
                      {{ reviewer.display_name }} (ID: {{ reviewer.user_id }})
                    </option>
                  </select>
                  <div class="text-sm text-gray-500">Select a user with legal review permissions</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'compliance'" class="space-y-6">
          <!-- Compliance & Frameworks Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <Shield class="w-5 h-5" />
                Compliance & Frameworks
              </h3>
              <p class="text-sm text-muted-foreground">
                Select applicable compliance frameworks for this subcontract
              </p>
            </div>
            <div class="p-6 space-y-4">
              <div class="space-y-3">
                <label class="text-sm font-medium">Compliance Framework</label>
                <select 
                  :value="formData.compliance_frameworks && formData.compliance_frameworks.length > 0 ? formData.compliance_frameworks[0] : ''"
                  @change="(e) => {
                    if (e.target.value) {
                      formData.compliance_frameworks = [e.target.value]
                    } else {
                      formData.compliance_frameworks = []
                    }
                  }"
                  class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                >
                  <option value="">Select compliance framework</option>
                  <option value="SOC2">SOC2</option>
                  <option value="GDPR">GDPR</option>
                  <option value="CCPA">CCPA</option>
                  <option value="ISO27001">ISO27001</option>
                  <option value="PCI DSS">PCI DSS</option>
                  <option value="HIPAA">HIPAA</option>
                  <option value="Other">Other</option>
                </select>
                <div class="text-sm text-muted-foreground">
                  Select the primary compliance framework applicable to this subcontract
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'terms'" class="space-y-6">
          <!-- Contract Terms Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <FileCheck class="w-5 h-5" />
                Contract Terms
              </h3>
              <p class="text-sm text-muted-foreground">Define and manage subcontract terms with risk assessment</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-medium">Terms List</h3>
                <button @click="addNewTerm" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                  <Plus class="w-4 h-4" />
                  Add Term
                </button>
              </div>
              
              <div class="space-y-4">
                <div v-for="(term, index) in contractTerms" :key="term.term_id" class="border rounded-lg bg-card p-4">
                  <div class="space-y-4">
                    <div class="flex items-center justify-between">
                      <h4 class="font-medium">Term #{{ index + 1 }}</h4>
                      <button @click="removeTerm(index)" class="inline-flex items-center gap-2 px-3 py-1 text-sm border rounded-md hover:bg-muted">
                        <Trash2 class="w-4 h-4" />
                      </button>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div class="space-y-2">
                        <label class="text-sm font-medium">Term Category *</label>
                        <select :value="term.term_category" @change="(e) => term.term_category = e.target.value" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" :class="!term.term_category ? 'border-red-500' : ''">
                          <option value="">Select category</option>
                          <option value="Payment">Payment</option>
                          <option value="Delivery">Delivery</option>
                          <option value="Performance">Performance</option>
                          <option value="Liability">Liability</option>
                          <option value="Termination">Termination</option>
                          <option value="Intellectual Property">Intellectual Property</option>
                          <option value="Confidentiality">Confidentiality</option>
                        </select>
                        <div v-if="!term.term_category" class="text-sm text-red-500">Term category is required</div>
                      </div>
                      
                      <div class="space-y-2">
                        <label class="text-sm font-medium">Term Title</label>
                        <input
                          :value="term.term_title"
                          @input="(e) => term.term_title = e.target.value"
                          placeholder="e.g., Payment Schedule"
                          class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        />
                      </div>

                      </div>

                      <div class="space-y-2">
                      <label class="text-sm font-medium">Term Text *</label>
                      <textarea
                        :value="term.term_text"
                        @input="(e) => term.term_text = e.target.value"
                        placeholder="Enter the detailed term text..."
                        rows="3"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        :class="!term.term_text ? 'border-red-500' : ''"
                      ></textarea>
                      <div v-if="!term.term_text" class="text-sm text-red-500">Term text is required</div>
                    </div>

                    <div class="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        :id="`standard_${index}`"
                        :checked="term.is_standard"
                        @change="(e) => term.is_standard = e.target.checked"
                        class="rounded border-gray-300"
                      />
                      <label :for="`standard_${index}`" class="text-sm">Standard Term</label>
                    </div>

                    <div v-if="term.term_title || term.term_category" class="mt-4">
                      <div class="border rounded-lg bg-muted/40">
                        <button
                          type="button"
                          class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-muted/60 transition"
                          @click="toggleTemplateSection(term.term_id)"
                        >
                          <div class="flex flex-col gap-1">
                            <span class="text-sm font-medium text-foreground">Questionnaire Templates</span>
                            <span class="text-xs text-muted-foreground">
                              <template v-if="getSelectedTemplateForTerm(term.term_id)">
                                Selected: {{ getSelectedTemplateForTerm(term.term_id)?.template_name }}
                              </template>
                              <template v-else-if="getTemplatesForTerm(term.term_id).length">
                                {{ getTemplatesForTerm(term.term_id).length }} {{ getTemplatesForTerm(term.term_id).length === 1 ? 'template available' : 'templates available' }}
                              </template>
                              <template v-else-if="hasLoadedTemplatesForTerm(term.term_id)">
                                No templates found for this term
                              </template>
                              <template v-else>
                                Click to load and manage templates
                              </template>
                            </span>
                          </div>
                          <div class="flex items-center gap-3">
                            <span class="hidden text-xs text-muted-foreground sm:inline">
                              {{ hasQuestionnaires(term) ? `${getQuestionnaireCount(term)} questions` : 'No questions yet' }}
                            </span>
                            <ChevronDown
                              class="w-4 h-4 transition-transform duration-200"
                              :class="{ 'rotate-180': isTemplateSectionExpanded(term.term_id) }"
                            />
                          </div>
                        </button>

                        <div
                          v-if="isTemplateSectionExpanded(term.term_id)"
                          class="border-t px-4 py-4 space-y-4 bg-background"
                        >
                          <div class="flex flex-wrap items-center justify-between gap-2">
                            <div class="text-sm text-muted-foreground">
                              Manage questionnaire templates for this term
                            </div>
                            <div class="flex flex-wrap gap-2">
                              <button
                                @click="loadTemplatesForTerm(term)"
                                class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted text-sm"
                              >
                                <Search class="w-4 h-4" />
                                Load Templates
                              </button>
                              <button
                                @click="createQuestionnaires(term)"
                                class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted text-sm"
                              >
                                <Plus class="w-4 h-4" />
                                Create Template
                              </button>
                              <button
                                v-if="hasQuestionnaires(term)"
                                @click="viewQuestionnaires(term)"
                                class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted text-sm"
                              >
                                <FileText class="w-4 h-4" />
                                View {{ getQuestionnaireCount(term) }} Questions
                              </button>
                            </div>
                          </div>

                          <div
                            v-if="getSelectedTemplateForTerm(term.term_id)"
                            class="p-3 bg-blue-50 border border-blue-200 rounded-lg"
                          >
                            <div class="flex items-center justify-between gap-3">
                              <div class="space-y-1">
                                <div class="font-medium text-blue-900">
                                  Selected: {{ getSelectedTemplateForTerm(term.term_id)?.template_name }}
                                </div>
                                <div class="text-xs text-blue-700">
                                  {{ getSelectedTemplateForTerm(term.term_id)?.question_count || 0 }} questions • Version {{ getSelectedTemplateForTerm(term.term_id)?.template_version || '—' }}
                                </div>
                              </div>
                              <div class="flex gap-2">
                                <button
                                  @click="viewTemplateQuestions(term.term_id, getSelectedTemplateForTerm(term.term_id)?.template_id)"
                                  class="inline-flex items-center gap-1 px-2 py-1 border border-blue-400 text-blue-700 rounded-md hover:bg-blue-100 text-xs"
                                >
                                  <FileText class="w-4 h-4" />
                                  View
                                </button>
                                <button
                                  @click="clearTemplateSelection(term.term_id)"
                                  class="inline-flex items-center gap-1 px-2 py-1 text-blue-700 hover:text-blue-900 text-xs"
                                >
                                  <X class="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          </div>

                          <div v-if="getTemplatesForTerm(term.term_id).length > 0" class="space-y-2">
                            <div
                              v-for="template in getTemplatesForTerm(term.term_id)"
                              :key="template.template_id"
                              class="p-3 border rounded-lg hover:bg-muted cursor-pointer transition-colors"
                              :class="getSelectedTemplateForTerm(term.term_id)?.template_id === template.template_id ? 'bg-blue-50 border-blue-300' : ''"
                              @click="selectTemplateForTerm(term.term_id, template)"
                            >
                              <div class="flex items-center justify-between gap-3">
                                <div>
                                  <div class="font-medium">{{ template.template_name }}</div>
                                  <div class="text-xs text-muted-foreground">
                                    {{ template.question_count }} questions • Version {{ template.template_version }}
                                  </div>
                                  <div v-if="template.template_description" class="text-xs text-muted-foreground mt-1">
                                    {{ template.template_description }}
                                  </div>
                                </div>
                                <div class="flex items-center gap-2">
                                  <button
                                    @click.stop="viewTemplateQuestions(term.term_id, template.template_id)"
                                    class="inline-flex items-center gap-1 px-2 py-1 border border-input rounded-md hover:bg-muted text-xs"
                                  >
                                    <FileText class="w-4 h-4" />
                                    Preview
                                  </button>
                                  <div
                                    v-if="getSelectedTemplateForTerm(term.term_id)?.template_id === template.template_id"
                                    class="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center"
                                  >
                                    <CheckCircle class="w-4 h-4 text-white" />
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          <div
                            v-else-if="hasLoadedTemplatesForTerm(term.term_id)"
                            class="text-sm text-muted-foreground text-center py-4"
                          >
                            No templates found. Create a new template to get started.
                          </div>
                        </div>
                      </div>
                    </div>

                  </div>
                </div>
                
                <div v-if="contractTerms.length === 0" class="text-center py-8 text-muted-foreground">
                  No contract terms added yet. Click "Add Term" to get started.
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'clauses'" class="space-y-6">
          <!-- Contract Clauses Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <FileText class="w-5 h-5" />
                Contract Clauses Library
              </h3>
              <p class="text-sm text-muted-foreground">Manage standardized subcontract clauses</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-medium">Clauses List</h3>
                <button @click="addNewClause" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                  <Plus class="w-4 h-4" />
                  Add Clause
                </button>
              </div>
              
              <div class="space-y-4">
                <div v-for="(clause, index) in contractClauses" :key="clause.clause_id" class="border rounded-lg bg-card p-4">
                  <div class="space-y-4">
                    <div class="flex items-center justify-between">
                      <h4 class="font-medium">Clause #{{ index + 1 }}</h4>
                      <button @click="removeClause(index)" class="inline-flex items-center gap-2 px-3 py-1 text-sm border rounded-md hover:bg-muted">
                        <Trash2 class="w-4 h-4" />
                      </button>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div class="space-y-2">
                        <label class="text-sm font-medium">Clause Name</label>
                        <input
                          :value="clause.clause_name"
                          @input="(e) => clause.clause_name = e.target.value"
                          placeholder="e.g., Limitation of Liability"
                          class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        />
                      </div>
                      
                      <div class="space-y-2">
                        <label class="text-sm font-medium">Clause Type</label>
                        <select :value="clause.clause_type" @change="(e) => clause.clause_type = e.target.value" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                          <option value="standard">Standard</option>
                          <option value="risk">Risk</option>
                          <option value="compliance">Compliance</option>
                          <option value="financial">Financial</option>
                          <option value="operational">Operational</option>
                          <option value="renewal">Renewal</option>
                          <option value="termination">Termination</option>
                          <option value="other">Other</option>
                        </select>
                      </div>

                      <div class="space-y-2">
                        <label class="text-sm font-medium">Legal Category</label>
                        <input
                          :value="clause.legal_category"
                          @input="(e) => clause.legal_category = e.target.value"
                          placeholder="e.g., Commercial Law"
                          class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        />
                      </div>
                    </div>

                    <div class="space-y-2">
                      <label class="text-sm font-medium">Clause Text</label>
                      <textarea
                        :value="clause.clause_text"
                        @input="(e) => clause.clause_text = e.target.value"
                        placeholder="Enter the detailed clause text..."
                        rows="4"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      ></textarea>
                    </div>

                    <div class="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        :id="`standard_clause_${index}`"
                        :checked="clause.is_standard"
                        @change="(e) => clause.is_standard = e.target.checked"
                        class="rounded border-gray-300"
                      />
                      <label :for="`standard_clause_${index}`" class="text-sm">Standard Clause</label>
                    </div>
                  </div>
                </div>
                
                <div v-if="contractClauses.length === 0" class="text-center py-8 text-muted-foreground">
                  No contract clauses added yet. Click "Add Clause" to get started.
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'renewal'" class="space-y-6">
          <!-- Renewal Clauses Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <Calendar class="w-5 h-5" />
                Renewal Clauses
              </h3>
              <p class="text-sm text-muted-foreground">Define subcontract renewal terms and conditions</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-medium">Renewal Clauses</h3>
                <button @click="addNewRenewalClause" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                  <Plus class="w-4 h-4" />
                  Add Renewal Clause
                </button>
              </div>
              
              <div class="space-y-4">
                <div v-for="(clause, index) in contractClauses.filter(c => c.clause_type === 'renewal')" :key="clause.clause_id" class="border rounded-lg bg-card p-4">
                  <div class="space-y-4">
                    <div class="flex items-center justify-between">
                      <h4 class="font-medium">Renewal Clause #{{ index + 1 }}</h4>
                      <button @click="removeClause(clause.clause_id)" class="inline-flex items-center gap-2 px-3 py-1 text-sm border rounded-md hover:bg-muted">
                        <Trash2 class="w-4 h-4" />
                      </button>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div class="space-y-2">
                        <label class="text-sm font-medium">Notice Period (Days)</label>
                        <input
                          :value="clause.notice_period_days"
                          @input="(e) => clause.notice_period_days = e.target.value"
                          type="number"
                          placeholder="30"
                          class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        />
                      </div>
                    </div>

                    <div class="space-y-2">
                      <label class="text-sm font-medium">Renewal Terms</label>
                      <textarea
                        :value="clause.renewal_terms"
                        @input="(e) => clause.renewal_terms = e.target.value"
                        placeholder="Enter the detailed renewal terms..."
                        rows="4"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      ></textarea>
                    </div>

                    <div class="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        :id="`auto_renew_${clause.clause_id}`"
                        :checked="clause.auto_renew"
                        @change="(e) => clause.auto_renew = e.target.checked"
                        class="rounded border-gray-300"
                      />
                      <label :for="`auto_renew_${clause.clause_id}`" class="text-sm">Enable Auto-Renewal</label>
                    </div>
                  </div>
                </div>
                
                <div v-if="contractClauses.filter(c => c.clause_type === 'renewal').length === 0" class="text-center py-8 text-muted-foreground">
                  No renewal clauses added yet. Click "Add Renewal Clause" to get started.
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'termination'" class="space-y-6">
          <!-- Termination Clauses Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <FileText class="w-5 h-5" />
                Termination Clauses
              </h3>
              <p class="text-sm text-muted-foreground">Define subcontract termination conditions and penalties</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="flex justify-between items-center">
                <h3 class="text-lg font-medium">Termination Clauses</h3>
                <button @click="addNewTerminationClause" class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90">
                  <Plus class="w-4 h-4" />
                  Add Termination Clause
                </button>
              </div>
              
              <div class="space-y-4">
                <div v-for="(clause, index) in contractClauses.filter(c => c.clause_type === 'termination')" :key="clause.clause_id" class="border rounded-lg bg-card p-4">
                  <div class="space-y-4">
                    <div class="flex items-center justify-between">
                      <h4 class="font-medium">Termination Clause #{{ index + 1 }}</h4>
                      <button @click="removeClause(clause.clause_id)" class="inline-flex items-center gap-2 px-3 py-1 text-sm border rounded-md hover:bg-muted">
                        <Trash2 class="w-4 h-4" />
                      </button>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div class="space-y-2">
                        <label class="text-sm font-medium">Notice Period (Days)</label>
                        <input
                          :value="clause.termination_notice_period"
                          @input="(e) => clause.termination_notice_period = e.target.value"
                          type="number"
                          placeholder="30"
                          class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        />
                      </div>

                      <div class="space-y-2">
                        <label class="text-sm font-medium">Early Termination Fee</label>
                        <input
                          :value="clause.early_termination_fee"
                          @input="(e) => clause.early_termination_fee = e.target.value"
                          type="number"
                          placeholder="0"
                          class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        />
                      </div>
                    </div>

                    <div class="space-y-2">
                      <label class="text-sm font-medium">Termination Conditions</label>
                      <textarea
                        :value="clause.termination_conditions"
                        @input="(e) => clause.termination_conditions = e.target.value"
                        placeholder="Enter the detailed termination conditions..."
                        rows="4"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      ></textarea>
                    </div>
                  </div>
                </div>
                
                <div v-if="contractClauses.filter(c => c.clause_type === 'termination').length === 0" class="text-center py-8 text-muted-foreground">
                  No termination clauses added yet. Click "Add Termination Clause" to get started.
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'legal'" class="space-y-6">
          <!-- Legal & Risk Management Card -->
          <div class="border rounded-lg bg-card">
            <div class="p-6 border-b">
              <h3 class="text-lg font-semibold flex items-center gap-2">
                <Shield class="w-5 h-5" />
                Legal & Risk Management
              </h3>
              <p class="text-sm text-muted-foreground">Legal terms, risk assessment, and dispute resolution</p>
            </div>
            <div class="p-6 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium">Dispute Resolution</label>
                  <select :value="formData.dispute_resolution" @change="(e) => formData.dispute_resolution = e.target.value" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                    <option value="">Select resolution method</option>
                    <option value="negotiation">Negotiation</option>
                    <option value="mediation">Mediation</option>
                    <option value="arbitration">Arbitration</option>
                    <option value="litigation">Litigation</option>
                    <option value="hybrid">Hybrid</option>
                  </select>
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Governing Law</label>
                  <input
                    id="governing_law"
                    :value="formData.governing_law"
                    @input="(e) => formData.governing_law = e.target.value"
                    placeholder="e.g., California, USA"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  />
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Termination Clause</label>
                  <select :value="formData.termination_clause" @change="(e) => formData.termination_clause = e.target.value" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                    <option value="">Select termination type</option>
                    <option value="convenience">Convenience</option>
                    <option value="cause">Cause</option>
                    <option value="both">Both</option>
                    <option value="none">None</option>
                  </select>
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Insurance Requirements</label>
                  <textarea
                    :value="formData.insurance_requirements"
                    @input="(e) => formData.insurance_requirements = e.target.value"
                    placeholder="Enter insurance requirements..."
                    rows="3"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  ></textarea>
                </div>

                <div class="space-y-2">
                  <label class="text-sm font-medium">Data Protection Clauses</label>
                  <textarea
                    :value="formData.data_protection_clauses"
                    @input="(e) => formData.data_protection_clauses = e.target.value"
                    placeholder="Enter data protection clauses..."
                    rows="3"
                    class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                  ></textarea>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  <!-- Questionnaires Modal -->
  <div
    v-if="showQuestionnairesModal"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click="closeQuestionnairesModal"
  >
    <div
      class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden"
      @click.stop
    >
      <div class="flex items-center justify-between p-6 border-b">
        <h2 class="text-2xl font-bold">
          Questionnaires for "{{ selectedTermTitle || 'Unknown Term' }}"
        </h2>
        <button @click="closeQuestionnairesModal" class="text-gray-500 hover:text-gray-700">
          <X class="w-5 h-5" />
        </button>
      </div>
      <div class="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
        <div class="space-y-4">
          <div
            v-for="(question, index) in selectedQuestionnaires"
            :key="question.question_id || index"
            class="border rounded-lg p-4 bg-gray-50"
          >
            <div class="flex items-start justify-between mb-2">
              <div class="flex items-start gap-3 flex-1">
                <div class="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white text-sm font-medium">
                  {{ index + 1 }}
                </div>
                <div class="flex-1 space-y-1">
                  <h3 class="font-medium text-lg">{{ question.question_text }}</h3>
                  <div class="flex items-center gap-4 text-sm text-muted-foreground flex-wrap">
                    <span>Type: <span class="font-medium capitalize">{{ question.question_type }}</span></span>
                    <span>Weight: <span class="font-medium">{{ question.scoring_weightings }}%</span></span>
                    <span v-if="question.is_required" class="text-red-600 font-medium">Required</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="!selectedQuestionnaires || selectedQuestionnaires.length === 0" class="text-center py-8 text-muted-foreground">
          No questionnaires found for this term.
        </div>
      </div>
      <div class="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
        <button
          class="inline-flex items-center gap-2 px-4 py-2 border border-input rounded-md hover:bg-muted"
          @click="closeQuestionnairesModal"
        >
          Close
        </button>
        <button
          class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-60 disabled:cursor-not-allowed"
          :disabled="!selectedTerm"
          @click="selectedTerm && editQuestionnaires(selectedTerm, selectedQuestionnaires)"
        >
          <FileText class="w-4 h-4" />
          Edit Questionnaires
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, reactive, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ArrowLeft, Save, Send, FileText, Building, DollarSign, Calendar, 
  Shield, Users, FileCheck, Plus, Trash2, Upload, Eye, CheckCircle, 
  AlertTriangle, Edit, X, ChevronDown 
} from 'lucide-vue-next'
import contractsApi from '@/services/contractsApi'
import { PopupService } from '@/popup/popupService'
import apiService from '@/services/api'
import { getApiOrigin } from '@/utils/backendEnv'

// Router and route
const router = useRouter()
const route = useRoute()
const navigate = (path) => router.push(path)
const id = route.params.id

console.log('🔍 CreateSubcontract - Route params:', route.params)
console.log('🔍 CreateSubcontract - Route query:', route.query)
console.log('🔍 CreateSubcontract - Contract ID:', id)

// Reactive state
const activeTab = ref('basic')
const showPreview = ref(false)
const previewTimestamp = ref(Date.now()) // Timestamp to force preview refresh
const showOCR = ref(false)
const uploadStep = ref('upload')
const uploadProgress = ref(0)
const selectedFile = ref(null)
const isSubmitting = ref(false)
const formKey = ref(0) // Key to force form re-rendering
const versionType = ref('minor') // Version type for parent contract versioning
const isDragOver = ref(false)
const s3UploadInfo = ref(null)
const availableVendors = ref([]) // List of all vendors for dropdown
const users = ref([]) // List of all users for contract owner selection
const legalReviewers = ref([]) // List of legal reviewers for legal reviewer selection

// Success and error messages
const successMessage = ref('')
const errors = ref({})

// Risk analysis notifications
const showRiskAnalysisNotification = ref(false)
const showRiskAnalysisTriggered = ref(false)

// Form data
const formData = ref({
  title: '',
  contract_number: '',
  vendor_id: '',
  vendor_name: '',
  type: '',
  value: '',
  currency: 'USD',
  start_date: '',
  end_date: '',
  contract_owner: '',  // Changed from 'owner' to 'contract_owner' for backend consistency
  legal_reviewer: '',
  auto_renew: false,
  notice_period_days: 30,
  risk_level: '',
  compliance_frameworks: [],
  description: '',
  parent_contract_id: id || '',
  contract_category: '',
  business_owner: '',
  procurement_contact: '',
  auto_renewal_flag: false,
  renewal_notice_period: 30,
  termination_clause: '',
  liability_cap: '',
  insurance_requirements: {},
  data_protection_clauses: {},
  dispute_resolution: '',
  governing_law: '',
  esignature_required: false,
  contract_risk_score: '',
  workflow_stage: 'under_review',
  priority: 'medium',
  assigned_to: '',
  custom_fields: {},
  compliance_status: 'under_review',
  renewal_terms: '',
  auto_renewal: false,
  status: 'PENDING_ASSIGNMENT',
  file_path: '',  // S3 URL for uploaded subcontract document
  permission_required: false,  // Whether parent contract can view this subcontract
  compliance_framework: ''  // Added for compliance tab
})

// Contract terms and clauses
const contractTerms = ref([])
const contractClauses = ref([])

// Questionnaire & template state
const allTermQuestionnaires = ref([])
const showQuestionnairesModal = ref(false)
const selectedTermTitle = ref('')
const selectedTermId = ref(null)
const selectedQuestionnaires = ref([])
const selectedTerm = computed(() =>
  contractTerms.value.find(term => String(term.term_id) === String(selectedTermId.value)) || null
)

const allTermTemplates = ref([]) // [{ term_id, templates: [] }]
const selectedTemplates = ref({}) // { [term_id]: template_id }
const loadedTemplatesForTerms = ref(new Set())
const expandedTemplateSections = ref({})
// Cache for template questions to avoid repeated API calls
const templateQuestionsCache = ref({}) // { [template_id]: questions[] }

const isTemplateSectionExpanded = (termId) => {
  const termIdStr = String(termId || '')
  if (!termIdStr) return false
  return !!expandedTemplateSections.value[termIdStr]
}

const setTemplateSectionExpanded = (termId, expanded = true) => {
  const termIdStr = String(termId || '')
  if (!termIdStr) return
  if (expanded) {
    expandedTemplateSections.value = {
      ...expandedTemplateSections.value,
      [termIdStr]: true
    }
  } else {
    const updated = { ...expandedTemplateSections.value }
    delete updated[termIdStr]
    expandedTemplateSections.value = updated
  }
}

const toggleTemplateSection = (termId) => {
  const termIdStr = String(termId || '')
  if (!termIdStr) return
  const shouldExpand = !expandedTemplateSections.value[termIdStr]
  setTemplateSectionExpanded(termIdStr, shouldExpand)
}

// OCR results with comprehensive subcontract fields mapping to database schema
const ocrResults = ref([
  // Basic Subcontract Information
  { field: "title", value: "UI/UX Design Services Subcontract", confidence: 95, needsReview: false },
  { field: "contract_number", value: "SUB-2024-001", confidence: 98, needsReview: false },
  { field: "vendor_name", value: "Design Studio Pro", confidence: 98, needsReview: false },
  { field: "vendor_id", value: "2", confidence: 85, needsReview: true },
  { field: "type", value: "SOW", confidence: 88, needsReview: false },
  { field: "contract_category", value: "services", confidence: 92, needsReview: false },
  
  // Financial Information
  { field: "value", value: "50000", confidence: 85, needsReview: true },
  { field: "currency", value: "USD", confidence: 98, needsReview: false },
  { field: "liability_cap", value: "75000", confidence: 78, needsReview: true },
  
  // Dates and Terms
  { field: "start_date", value: "2024-02-01", confidence: 92, needsReview: false },
  { field: "end_date", value: "2024-05-31", confidence: 90, needsReview: false },
  { field: "notice_period_days", value: "30", confidence: 87, needsReview: false },
  { field: "auto_renew", value: "false", confidence: 85, needsReview: true },
  { field: "renewal_terms", value: "Renewal for 6 months with 30 days notice", confidence: 82, needsReview: true },
  
  // Stakeholders
  { field: "contract_owner", value: "1", confidence: 90, needsReview: false },
  { field: "legal_reviewer", value: "2", confidence: 88, needsReview: false },
  { field: "assigned_to", value: "1", confidence: 85, needsReview: true },
  
  // Risk and Description
  { field: "risk_level", value: "Low", confidence: 85, needsReview: true },
  { field: "description", value: "UI/UX design services for mobile application development including wireframes, mockups, and user testing", confidence: 92, needsReview: false },
  { field: "contract_risk_score", value: "3.5", confidence: 75, needsReview: true },
  
  // Legal Information
  { field: "dispute_resolution", value: "mediation", confidence: 80, needsReview: true },
  { field: "governing_law", value: "California, USA", confidence: 88, needsReview: false },
  { field: "termination_clause", value: "convenience", confidence: 85, needsReview: true },
  
  // Subcontract Terms (contract_terms table) - Using only valid term categories
  { field: "term_Payment", value: "Payment due within 15 days of milestone completion", confidence: 92, needsReview: false },
  { field: "term_Delivery", value: "All design deliverables must be provided in Adobe XD format with developer handoff specifications", confidence: 88, needsReview: false },
  { field: "term_Performance", value: "Designs must follow Material Design guidelines and be responsive across all device sizes", confidence: 90, needsReview: false },
  { field: "term_Liability", value: "Designer's liability shall be limited to the subcontract value and shall not exceed $50,000", confidence: 85, needsReview: true },
  { field: "term_Intellectual_Property", value: "Client retains ownership of all final designs and design assets", confidence: 94, needsReview: false },
  { field: "term_Confidentiality", value: "Designer shall maintain confidentiality of all client information and project details", confidence: 87, needsReview: false },
  { field: "term_Termination", value: "Either party may terminate this subcontract with 15 days written notice for convenience", confidence: 85, needsReview: true },
  
  // Subcontract Clauses (contract_clauses table)
  { field: "clause_Limitation_of_Liability", value: "Designer\'s liability shall be limited to the subcontract value and shall not exceed $50,000", confidence: 92, needsReview: false },
  { field: "clause_Confidentiality", value: "Both parties agree to maintain confidentiality of all proprietary information and design concepts", confidence: 94, needsReview: false },
  { field: "clause_Force_Majeure", value: "Neither party shall be liable for delays or failures due to circumstances beyond their control", confidence: 87, needsReview: false },
  { field: "clause_Design_Ownership", value: "Client shall own all final designs upon full payment of subcontract fees", confidence: 89, needsReview: true },
  { field: "clause_Data_Protection", value: "Designer shall comply with client\'s data protection policies and GDPR requirements", confidence: 91, needsReview: false },
  { field: "clause_Communication_Protocol", value: "Regular check-ins via video conference every Tuesday at 2 PM EST", confidence: 86, needsReview: false },
  
  // Renewal Clauses (contract_clauses with clause_type='renewal')
  { field: "renewal_Notice_Period", value: "Either party may terminate this subcontract with 15 days written notice prior to expiration", confidence: 88, needsReview: false },
  { field: "renewal_Term_Length", value: "Subcontract may be renewed for additional 3-month periods with same terms and conditions", confidence: 85, needsReview: true },
  { field: "renewal_Pricing_Adjustment", value: "Pricing may be adjusted quarterly based on market rates and scope changes", confidence: 82, needsReview: true },
  { field: "renewal_Auto_Extension", value: "Subcontract shall automatically extend for one month unless terminated with proper notice", confidence: 90, needsReview: false },
  
  // Termination Clauses (contract_clauses with clause_type='termination')
  { field: "termination_Notice_Period", value: "Either party may terminate this subcontract with 15 days written notice for convenience", confidence: 92, needsReview: false },
  { field: "termination_For_Cause", value: "Either party may terminate immediately for material breach of subcontract terms", confidence: 88, needsReview: false },
  { field: "termination_Early_Fee", value: "Early termination fee shall be 15% of remaining subcontract value", confidence: 85, needsReview: true },
  { field: "termination_Transition_Support", value: "Designer shall provide 7 days transition support and file handover upon termination", confidence: 87, needsReview: false },
  
  // Insurance Requirements (JSON field)
  { field: "insurance_Professional_Liability", value: "Professional liability insurance of at least $500,000 per claim", confidence: 89, needsReview: false },
  { field: "insurance_General_Liability", value: "General liability insurance of at least $1,000,000 per occurrence", confidence: 87, needsReview: false },
  { field: "insurance_Errors_Omissions", value: "Errors and omissions insurance covering design mistakes and oversights", confidence: 85, needsReview: true },
  
  // Data Protection Clauses (JSON field)
  { field: "data_protection_Client_Data", value: "Designer shall not store or process client data outside of approved design tools", confidence: 88, needsReview: false },
  { field: "data_protection_Design_Assets", value: "All design assets must be stored in client-approved cloud storage with proper access controls", confidence: 86, needsReview: false },
  { field: "data_protection_Right_to_Deletion", value: "Designer shall delete all client data and design files within 30 days of project completion", confidence: 84, needsReview: true }
])

// Tab configuration
const tabs = [
  { value: 'basic', label: 'Basic Info' },
  { value: 'financial', label: 'Financial' },
  { value: 'dates', label: 'Dates & Terms' },
  { value: 'stakeholders', label: 'Stakeholders' },
  { value: 'compliance', label: 'Compliance' },
  { value: 'terms', label: 'Contract Terms' },
  { value: 'clauses', label: 'Clauses' },
  { value: 'renewal', label: 'Renewal' },
  { value: 'termination', label: 'Termination' },
  { value: 'legal', label: 'Legal' }
]

// Methods
const debugFormData = () => {
  console.log('🐛 DEBUG: Current form data state:')
  console.log('📋 Full formData:', JSON.stringify(formData.value, null, 2))
  console.log('🔍 Required fields check:')
  console.log('  - title:', formData.value.title, 'empty?', !formData.value.title)
  console.log('  - type:', formData.value.type, 'empty?', !formData.value.type)
  console.log('  - start_date:', formData.value.start_date, 'empty?', !formData.value.start_date)
  console.log('  - end_date:', formData.value.end_date, 'empty?', !formData.value.end_date)
  
  // Check if validation would pass
  const isValid = formData.value.title && formData.value.type && formData.value.start_date && formData.value.end_date
  console.log('✅ Validation would pass:', isValid)
  
  // Debug main contract data if available
  if (mainContractData.value) {
    console.log('📋 Main contract data:', JSON.stringify(mainContractData.value, null, 2))
    console.log('🔍 Main contract required fields:')
    console.log('  - contract_title:', mainContractData.value.contract_title, 'empty?', !mainContractData.value.contract_title)
    console.log('  - contract_type:', mainContractData.value.contract_type, 'empty?', !mainContractData.value.contract_type)
  }
  
  // Debug contract terms and clauses
  console.log('📋 Contract terms count:', contractTerms.value.length)
  console.log('📋 Contract clauses count:', contractClauses.value.length)
  
  PopupService.success(`Form Debug:\nTitle: "${formData.value.title}"\nType: "${formData.value.type}"\nStart: "${formData.value.start_date}"\nEnd: "${formData.value.end_date}"\nValid: ${isValid}\nTerms: ${contractTerms.value.length}\nClauses: ${contractClauses.value.length}`, 'Form Debug')
}

const handleEditSubcontract = () => {
  console.log('✏️ Edit Subcontract clicked from preview')
  console.log('🔍 Current form data before closing preview:')
  console.log('  - title:', formData.value.title)
  console.log('  - contract_number:', formData.value.contract_number)
  console.log('  - value:', formData.value.value)
  console.log('  - liability_cap:', formData.value.liability_cap)
  console.log('  - start_date:', formData.value.start_date)
  console.log('  - end_date:', formData.value.end_date)
  console.log('  - terms count:', contractTerms.value.length)
  console.log('  - clauses count:', contractClauses.value.length)
  
  // Clear the old preview data from session storage to prevent stale data
  console.log('🧹 Clearing old preview data from session storage')
  sessionStorage.removeItem('subcontractPreviewData')
  sessionStorage.removeItem('subcontractData')
  
  // Close the preview dialog - form data remains intact for editing
  showPreview.value = false
  
  console.log('✅ Preview closed, form is ready for editing with current data')
  console.log('⚠️ IMPORTANT: Please edit the form fields now. Changes will be captured when you click Submit for Review again.')
}

const handleInputChange = (field, value) => {
  formData.value[field] = value
}

const handleComplianceChange = (framework, checked) => {
  if (checked) {
    formData.value.compliance_frameworks.push(framework)
  } else {
    formData.value.compliance_frameworks = formData.value.compliance_frameworks.filter(f => f !== framework)
  }
}

// Handle vendor change from dropdown
const handleVendorChange = (event) => {
  const vendorId = parseInt(event.target.value) || null
  console.log('🔄 Vendor changed to:', vendorId)
  
  formData.value.vendor_id = vendorId
  
  // Update vendor name based on selection
  if (vendorId) {
    const selectedVendor = availableVendors.value.find(v => v.vendor_id === vendorId)
    if (selectedVendor) {
      formData.value.vendor_name = selectedVendor.company_name
      console.log('✅ Vendor name updated to:', formData.value.vendor_name)
    }
  } else {
    formData.value.vendor_name = ''
  }
}

// Fetch all vendors for dropdown
const fetchVendors = async () => {
  try {
    console.log('📋 Fetching vendors list...')
    
    // Fetch vendors with a large page size to get all vendors
    const response = await contractsApi.getVendors({ page_size: 1000 })
    
    if (response.success && response.data) {
      availableVendors.value = response.data
      console.log('✅ Vendors loaded:', availableVendors.value.length, 'vendors')
      
      // Log the first few vendors for debugging
      if (availableVendors.value.length > 0) {
        console.log('🔍 Sample vendors:', availableVendors.value.slice(0, 3))
      }
    } else {
      console.warn('⚠️ No vendors found or invalid response')
      availableVendors.value = []
    }
  } catch (error) {
    console.error('❌ Error fetching vendors:', error)
    availableVendors.value = []
    
    // Show error to user if vendors can't be loaded
    errors.value.general = 'Failed to load vendors list. Please refresh the page.'
  }
}

// Helper function to get stored token from localStorage
const getStoredToken = () => {
  const keys = ['access_token', 'session_token', 'token', 'jwt_token']
  for (const key of keys) {
    const val = localStorage.getItem(key)
    if (val) return val
  }
  return null
}

const handleFileUpload = async (event) => {
  console.log('📁 Subcontract file upload triggered:', event)
  
  // Clear any previous errors
  if (errors.value.ocr) {
    delete errors.value.ocr
  }
  
  const file = event.target.files?.[0]
  console.log('📁 Selected file:', file)
  
  if (!file) {
    console.log('❌ No file selected')
    return
  }
  
  // Validate file type
  const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg', 'image/tiff']
  if (!allowedTypes.includes(file.type)) {
    console.error('❌ Invalid file type:', file.type)
    errors.value.ocr = 'Please select a valid file type (PDF, PNG, JPG, TIFF)'
    return
  }
  
  // Validate file size (10MB limit)
  const maxSize = 10 * 1024 * 1024 // 10MB in bytes
  if (file.size > maxSize) {
    console.error('❌ File too large:', file.size)
    errors.value.ocr = 'File size must be less than 10MB'
    return
  }
  
  console.log('✅ File validation passed, starting processing...')
  selectedFile.value = file
  uploadStep.value = 'processing'
  uploadProgress.value = 0
  
  try {
    // Create FormData for file upload
    const uploadFormData = new FormData()
    uploadFormData.append('file', file)
    uploadFormData.append('document_type', 'subcontract')
    uploadFormData.append('extract_contract_data', 'true')
    // Hint backend to run only contract extraction
    uploadFormData.append('mode', 'contract_only')
    
    // Get authentication token
    const token = getStoredToken()
    if (!token) {
      throw new Error('Authentication required. Please log in to upload files.')
    }
    
    console.log('📤 Uploading subcontract file to OCR service...')
    
    // Simulate progress updates
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 500)
    
    // Call the OCR API endpoint with authentication
    // Note: Don't set Content-Type header - browser will set it with boundary for FormData
    const headers = {
      'Authorization': `Bearer ${token}`
    }
    
    const response = await fetch('https://grc-tprm.vardaands.com/api/tprm/ocr/upload/', {
      method: 'POST',
      headers: headers,
      body: uploadFormData,
    })
    
    clearInterval(progressInterval)
    
    // Handle 401 errors - try to refresh token and retry
    let finalResponse = response
    if (response.status === 401) {
      console.log('🔄 401 error detected, attempting token refresh...')
      
      try {
        // Try to refresh token
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const apiOrigin = getApiOrigin() || 'https://grc-tprm.vardaands.com'
          const refreshResponse = await fetch(`${apiOrigin}/api/jwt/refresh/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
          })
          
          if (refreshResponse.ok) {
            const refreshData = await refreshResponse.json()
            if (refreshData.status === 'success') {
              // Update tokens
              localStorage.setItem('access_token', refreshData.access_token)
              if (refreshData.refresh_token) {
                localStorage.setItem('refresh_token', refreshData.refresh_token)
              }
              
              // Retry the upload with new token
              console.log('✅ Token refreshed, retrying OCR upload...')
              const newToken = getStoredToken()
              const retryHeaders = {
                'Authorization': `Bearer ${newToken}`
              }
              
              finalResponse = await fetch('https://grc-tprm.vardaands.com/api/tprm/ocr/upload/', {
                method: 'POST',
                headers: retryHeaders,
                body: uploadFormData,
              })
            }
          }
        }
      } catch (refreshError) {
        console.error('❌ Token refresh failed:', refreshError)
        // Continue to error handling below
      }
    }
    
    uploadProgress.value = 100
    
    if (!finalResponse.ok) {
      const errorData = await finalResponse.json().catch(() => ({ error: 'Unknown error' }))
      const errorMessage = errorData.error || `HTTP ${finalResponse.status}: ${finalResponse.statusText}`
      if (finalResponse.status === 401) {
        throw new Error('Authentication required. Please log in again.')
      }
      throw new Error(errorMessage)
    }
    
    const result = await finalResponse.json()
    console.log('✅ OCR processing completed:', result)
    
    // Handle S3 upload information
    if (result.upload_info) {
      s3UploadInfo.value = result.upload_info
      console.log('📁 S3 Upload Info:', result.upload_info)
      if (result.upload_info.success && result.upload_info.file_info?.url) {
        // Store S3 URL in formData for subcontract creation
        formData.value.file_path = result.upload_info.file_info.url
        console.log('💾 Stored S3 URL in formData.file_path:', formData.value.file_path)
        console.log('✅ Subcontract document successfully uploaded to S3:', result.upload_info.file_info.url)
      } else {
        console.warn('⚠️ S3 upload had issues:', result.upload_info.error || 'Unknown error')
        formData.value.file_path = ''
      }
    } else {
      console.warn('⚠️ No S3 upload information available - S3 client may not be configured')
      s3UploadInfo.value = {
        success: false,
        error: 'S3 client not available. Document processing continued without cloud storage.'
      }
      formData.value.file_path = ''
    }
    
    const contractData = result?.data || result?.contract_extraction?.data || null
    if (result.success && contractData) {
      // Map the OCR extracted data to our form structure
      await processOCRResults(contractData)
      uploadStep.value = 'review'
      console.log('✅ OCR data processed, showing review step')
    } else {
      throw new Error(result.error || 'Failed to extract subcontract data')
    }
    
  } catch (error) {
    console.error('❌ Error processing file:', error)
    errors.value.ocr = `Failed to process uploaded file: ${error.message}`
    uploadStep.value = 'upload'
    uploadProgress.value = 0
  }
}

const handleOCRValueChange = (field, newValue) => {
  ocrResults.value = ocrResults.value.map(result => 
    result.field === field 
      ? { ...result, value: newValue, needsReview: false }
      : result
  )
}

const processOCRResults = async (ocrData) => {
  console.log('🔄 Processing OCR results for subcontract:', ocrData)
  
  // Helper function to calculate confidence and determine if review is needed
  const getConfidenceInfo = (value, defaultConfidence = 85) => {
    if (!value || value === '' || value === null || value === undefined) {
      return { confidence: 0, needsReview: true }
    }
    return { confidence: defaultConfidence, needsReview: defaultConfidence < 85 }
  }
  
  // Build OCR results array from the extracted data
  const results = []
  
  // Basic Subcontract Information
  if (ocrData.contract_title) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_title, 95)
    results.push({ field: 'title', value: ocrData.contract_title, confidence, needsReview })
  }
  
  if (ocrData.contract_number) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_number, 90)
    results.push({ field: 'contract_number', value: ocrData.contract_number, confidence, needsReview })
  }
  
  if (ocrData.contract_type) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_type, 88)
    results.push({ field: 'type', value: ocrData.contract_type, confidence, needsReview })
  }
  
  if (ocrData.contract_category) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_category, 85)
    results.push({ field: 'contract_category', value: ocrData.contract_category, confidence, needsReview })
  }
  
  // Vendor Information
  if (ocrData.vendor_name) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.vendor_name, 90)
    results.push({ field: 'vendor_name', value: ocrData.vendor_name, confidence, needsReview })
  }
  
  // Financial Information
  if (ocrData.contract_value) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_value, 85)
    results.push({ field: 'value', value: String(ocrData.contract_value), confidence, needsReview: true })
  }
  
  if (ocrData.currency) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.currency, 95)
    results.push({ field: 'currency', value: ocrData.currency, confidence, needsReview })
  }
  
  if (ocrData.liability_cap) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.liability_cap, 80)
    results.push({ field: 'liability_cap', value: String(ocrData.liability_cap), confidence, needsReview: true })
  }
  
  // Dates
  if (ocrData.start_date) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.start_date, 92)
    results.push({ field: 'start_date', value: ocrData.start_date, confidence, needsReview })
  }
  
  if (ocrData.end_date) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.end_date, 90)
    results.push({ field: 'end_date', value: ocrData.end_date, confidence, needsReview })
  }
  
  if (ocrData.notice_period_days) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.notice_period_days, 87)
    results.push({ field: 'notice_period_days', value: String(ocrData.notice_period_days), confidence, needsReview })
  }
  
  // Risk and Description
  if (ocrData.risk_level) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.risk_level, 85)
    results.push({ field: 'risk_level', value: ocrData.risk_level, confidence, needsReview: true })
  }
  
  if (ocrData.description) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.description, 90)
    results.push({ field: 'description', value: ocrData.description, confidence, needsReview })
  }
  
  if (ocrData.contract_risk_score) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_risk_score, 75)
    results.push({ field: 'contract_risk_score', value: String(ocrData.contract_risk_score), confidence, needsReview: true })
  }
  
  // Legal Information
  if (ocrData.dispute_resolution_method) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.dispute_resolution_method, 80)
    results.push({ field: 'dispute_resolution', value: ocrData.dispute_resolution_method, confidence, needsReview: true })
  }
  
  if (ocrData.governing_law) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.governing_law, 88)
    results.push({ field: 'governing_law', value: ocrData.governing_law, confidence, needsReview })
  }
  
  if (ocrData.termination_clause_type) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.termination_clause_type, 85)
    results.push({ field: 'termination_clause', value: ocrData.termination_clause_type, confidence, needsReview: true })
  }
  
  // Auto Renewal
  if (ocrData.auto_renewal !== undefined) {
    const { confidence, needsReview } = getConfidenceInfo(String(ocrData.auto_renewal), 85)
    results.push({ field: 'auto_renew', value: String(ocrData.auto_renewal), confidence, needsReview: true })
  }
  
  if (ocrData.renewal_terms) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.renewal_terms, 82)
    results.push({ field: 'renewal_terms', value: ocrData.renewal_terms, confidence, needsReview: true })
  }
  
  // Process contract terms from OCR
  if (ocrData.terms && Array.isArray(ocrData.terms)) {
    ocrData.terms.forEach((term, index) => {
      const fieldName = `term_${term.category || 'General'}`
      const { confidence, needsReview } = getConfidenceInfo(term.text, 85)
      results.push({ 
        field: fieldName, 
        value: term.text, 
        confidence, 
        needsReview,
        metadata: { category: term.category, title: term.title }
      })
    })
  }
  
  // Process contract clauses from OCR
  if (ocrData.clauses && Array.isArray(ocrData.clauses)) {
    console.log('🔍 Processing OCR clauses for subcontract:', ocrData.clauses.length, ocrData.clauses)
    
    ocrData.clauses.forEach((clause, index) => {
      // Determine clause type and field name prefix
      const clauseType = clause.type || 'standard'
      let fieldName = ''
      
      if (clauseType === 'renewal') {
        fieldName = `renewal_${clause.name || `Renewal_${index + 1}`}`.replace(/\s+/g, '_')
        console.log('🔄 Processing renewal clause:', clause.name, clause)
      } else if (clauseType === 'termination') {
        fieldName = `termination_${clause.name || `Termination_${index + 1}`}`.replace(/\s+/g, '_')
        console.log('🔚 Processing termination clause:', clause.name, clause)
      } else {
        fieldName = `clause_${clause.name || `Clause_${index + 1}`}`.replace(/\s+/g, '_')
        console.log('📄 Processing standard clause:', clause.name, clause)
      }
      
      const { confidence, needsReview } = getConfidenceInfo(clause.text, 85)
      
      // Always store clause text as the main value, but include metadata for additional fields
      const clauseText = clause.text || clause.name || 'Clause text not available'
      
      results.push({ 
        field: fieldName, 
        value: clauseText,  // Always store text as main value
        confidence, 
        needsReview,
        metadata: { 
          name: clause.name, 
          type: clauseType,
          fullClause: clause,  // Store full clause object in metadata
          notice_period_days: clause.notice_period_days,
          auto_renew: clause.auto_renew,
          renewal_terms: clause.renewal_terms,
          termination_notice_period: clause.termination_notice_period,
          early_termination_fee: clause.early_termination_fee,
          termination_conditions: clause.termination_conditions
        }
      })
    })
  } else {
    console.log('⚠️ No clauses found in OCR data:', ocrData)
  }
  
  // Update the ocrResults ref
  ocrResults.value = results
  
  console.log('✅ OCR results processed for subcontract:', results.length, 'fields extracted')
  console.log('🔍 OCR results:', results)
}

// Drag and drop handlers
const handleDragOver = (e) => {
  e.preventDefault()
  isDragOver.value = true
}

const handleDragEnter = (e) => {
  e.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (e) => {
  e.preventDefault()
  isDragOver.value = false
}

const handleFileDrop = async (e) => {
  e.preventDefault()
  isDragOver.value = false
  
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    // Create a synthetic event object for handleFileUpload
    const syntheticEvent = {
      target: {
        files: files
      }
    }
    await handleFileUpload(syntheticEvent)
  }
}

const getConfidenceBadgeClass = (confidence) => {
  if (confidence >= 90) {
    return 'bg-green-100 text-green-800 border-green-200'
  } else if (confidence >= 70) {
    return 'bg-yellow-100 text-yellow-800 border-yellow-200'
  } else {
    return 'bg-red-100 text-red-800 border-red-200'
  }
}

const applyOCRData = () => {
  console.log('🔄 Applying OCR data to subcontract form...')
  console.log('🔍 Current OCR results:', ocrResults.value)
  console.log('🔍 Number of OCR results:', ocrResults.value.length)
  
  // Helper functions for data conversion
  const getFieldValue = (fieldName) => {
    return ocrResults.value.find(r => r.field === fieldName)?.value || ""
  }

  const getBooleanFieldValue = (fieldName) => {
    const value = getFieldValue(fieldName)
    return value === "true" || value === "1"
  }

  const getNumberFieldValue = (fieldName) => {
    const value = getFieldValue(fieldName)
    return value ? parseFloat(value) : null
  }

  const getIntegerFieldValue = (fieldName) => {
    const value = getFieldValue(fieldName)
    return value ? parseInt(value) : null
  }

  // Build insurance requirements JSON object
  const insuranceRequirements = {}
  ocrResults.value
    .filter(r => r.field.startsWith('insurance_'))
    .forEach(insurance => {
      const key = insurance.field.replace('insurance_', '').toLowerCase()
      insuranceRequirements[key] = insurance.value
    })

  // Build data protection clauses JSON object
  const dataProtectionClauses = {}
  ocrResults.value
    .filter(r => r.field.startsWith('data_protection_'))
    .forEach(clause => {
      const key = clause.field.replace('data_protection_', '').toLowerCase()
      dataProtectionClauses[key] = clause.value
    })

  // Map OCR results to subcontract form fields
  const ocrData = {
    // Basic Subcontract Information
    title: getFieldValue("title"),
    contract_number: getFieldValue("contract_number"),
    vendor_name: getFieldValue("vendor_name"),
    vendor_id: getIntegerFieldValue("vendor_id"),
    type: getFieldValue("type"),
    contract_category: getFieldValue("contract_category"),
    
    // Financial Information
    value: getNumberFieldValue("value"),
    currency: getFieldValue("currency") || "USD",
    liability_cap: getNumberFieldValue("liability_cap"),
    
    // Dates and Terms
    start_date: getFieldValue("start_date"),
    end_date: getFieldValue("end_date"),
    notice_period_days: getIntegerFieldValue("notice_period_days") || 30,
    auto_renew: getBooleanFieldValue("auto_renew"),
    renewal_terms: getFieldValue("renewal_terms"),
    
    // Stakeholders
    contract_owner: getIntegerFieldValue("contract_owner"),
    legal_reviewer: getIntegerFieldValue("legal_reviewer"),
    assigned_to: getIntegerFieldValue("assigned_to"),
    
    // Risk and Description
    risk_level: getFieldValue("risk_level"),
    description: getFieldValue("description"),
    contract_risk_score: getNumberFieldValue("contract_risk_score"),
    
    // Legal Information
    dispute_resolution: getFieldValue("dispute_resolution"),
    governing_law: getFieldValue("governing_law"),
    termination_clause: getFieldValue("termination_clause"),
    
    // JSON Fields
    insurance_requirements: insuranceRequirements,
    data_protection_clauses: dataProtectionClauses,
    custom_fields: {}
  }
  
  // Set form data
  formData.value = { ...formData.value, ...ocrData }
  
  // Process subcontract terms from OCR
  const termFields = ocrResults.value.filter(r => r.field.startsWith("term_"))
  console.log('🔍 Found term fields:', termFields)
  
  // Helper function to map field names to valid term categories
  const mapToValidTermCategory = (fieldName) => {
    const categoryMap = {
      'term_Payment': 'Payment',
      'term_Delivery': 'Delivery', 
      'term_Performance': 'Performance',
      'term_Liability': 'Liability',
      'term_Termination': 'Termination',
      'term_Intellectual_Property': 'Intellectual Property',
      'term_Confidentiality': 'Confidentiality'
    }
    return categoryMap[fieldName] || fieldName.replace("term_", "").replace(/_/g, " ")
  }

  const ocrTerms = termFields.map((term, index) => ({
      term_id: `term_${Date.now()}_${index}`,
      term_category: mapToValidTermCategory(term.field),
      term_title: term.field.replace("term_", "").replace(/_/g, " "),
      term_text: term.value,
      risk_level: "Low",
      compliance_status: "Pending",
      is_standard: false,
      approval_status: "Pending",
      approved_by: null,
      approved_at: null,
      version_number: "1.0",
      parent_term_id: "",
      created_by: getIntegerFieldValue("contract_owner")
    }))

  // Process subcontract clauses from OCR
  const clauseFields = ocrResults.value.filter(r => r.field.startsWith("clause_"))
  const renewalFields = ocrResults.value.filter(r => r.field.startsWith("renewal_"))
  const terminationFields = ocrResults.value.filter(r => r.field.startsWith("termination_"))
  
  console.log('🔍 Found clause fields:', clauseFields)
  console.log('🔍 Found renewal fields:', renewalFields)
  console.log('🔍 Found termination fields:', terminationFields)
  
  const ocrClauses = [
    // Standard clauses
    ...clauseFields.map((clause, index) => ({
        clause_id: `clause_${Date.now()}_${index}`,
        clause_name: clause.field.replace("clause_", "").replace(/_/g, " "),
        clause_type: "standard",
        clause_text: clause.value,
        risk_level: "low",
        legal_category: "Subcontract Terms",
        version_number: "1.0",
        is_standard: false,
        created_by: getIntegerFieldValue("contract_owner")
      })),
    
    // Renewal clauses
    ...renewalFields.map((clause, index) => ({
        clause_id: `renewal_${Date.now()}_${index}`,
        clause_name: clause.field.replace("renewal_", "").replace(/_/g, " "),
        clause_type: "renewal",
        clause_text: clause.value,
        risk_level: "low",
        legal_category: "Subcontract Renewal",
        version_number: "1.0",
        is_standard: false,
        created_by: getIntegerFieldValue("contract_owner"),
        notice_period_days: clause.field.includes("notice") ? 15 : null,
        auto_renew: clause.field.includes("auto") ? true : false,
        renewal_terms: clause.value
      })),
    
    // Termination clauses
    ...terminationFields.map((clause, index) => ({
        clause_id: `termination_${Date.now()}_${index}`,
        clause_name: clause.field.replace("termination_", "").replace(/_/g, " "),
        clause_type: "termination",
        clause_text: clause.value,
        risk_level: "medium",
        legal_category: "Subcontract Termination",
        version_number: "1.0",
        is_standard: false,
        created_by: getIntegerFieldValue("contract_owner"),
        termination_notice_period: clause.field.includes("notice") ? 15 : null,
        early_termination_fee: clause.field.includes("fee") ? 15 : null,
        termination_conditions: clause.value
      }))
  ]

  // Add OCR terms and clauses to existing ones with proper reactivity
  if (ocrTerms.length > 0) {
    console.log('🔍 OCR Terms to add:', ocrTerms)
    console.log('🔍 Current contractTerms before adding:', contractTerms.value)
    
    // Create new reactive objects for each term
    const reactiveTerms = ocrTerms.map(term => reactive({ ...term }))
    contractTerms.value = [...contractTerms.value, ...reactiveTerms]
    
    console.log('✅ Added OCR subcontract terms:', ocrTerms.length)
    console.log('🔍 Updated contractTerms after adding:', contractTerms.value)
    console.log('🔍 Total terms now:', contractTerms.value.length)
  }

  if (ocrClauses.length > 0) {
    console.log('🔍 OCR Clauses to add:', ocrClauses)
    console.log('🔍 Current contractClauses before adding:', contractClauses.value)
    
    // Create new reactive objects for each clause
    const reactiveClauses = ocrClauses.map(clause => reactive({ ...clause }))
    contractClauses.value = [...contractClauses.value, ...reactiveClauses]
    
    console.log('✅ Added OCR subcontract clauses:', ocrClauses.length)
    console.log('🔍 Updated contractClauses after adding:', contractClauses.value)
    console.log('🔍 Total clauses now:', contractClauses.value.length)
  }

  // Force reactivity updates
  contractTerms.value = [...contractTerms.value]
  contractClauses.value = [...contractClauses.value]
  
  console.log('🔄 Forced reactivity update for terms and clauses')
  console.log('🔍 Final contractTerms:', contractTerms.value)
  console.log('🔍 Final contractClauses:', contractClauses.value)

  // Force form re-render to ensure all data is displayed
  formKey.value++
  console.log('🔄 Form key updated to force re-render:', formKey.value)
  
  // Force update all form fields to ensure they display the new values
  setTimeout(async () => {
    console.log('🔄 Force updating form fields...')
    
    // Update input fields
    const formFields = [
      'title', 'contract_number', 'value', 'liability_cap', 'start_date', 'end_date',
      'notice_period_days', 'governing_law', 'contract_risk_score', 'description'
    ]
    
    formFields.forEach(fieldId => {
      const input = document.getElementById(fieldId)
      if (input && formData.value[fieldId] !== undefined && formData.value[fieldId] !== null) {
        input.value = formData.value[fieldId] || ''
        input.dispatchEvent(new Event('input', { bubbles: true }))
        console.log(`🔧 Updated ${fieldId} field:`, input.value)
      }
    })
    
    // Force update terms and clauses display
    console.log('🔄 Force updating terms and clauses display...')
    
    // Force reactivity update for terms and clauses
    contractTerms.value = [...contractTerms.value]
    contractClauses.value = [...contractClauses.value]
    
    // Force form re-render
    formKey.value++
    
    // Force another re-render to ensure all data is displayed
    setTimeout(() => {
      formKey.value++
      console.log('🔄 Final form re-render completed:', formKey.value)
    }, 50)
    
    console.log('✅ Form fields force updated')
  }, 100)
  
  // Switch to the terms tab to show the newly added terms
  if (ocrTerms.length > 0) {
    activeTab.value = 'terms'
    console.log('🔄 Switched to terms tab to show OCR terms')
  }
  
  showOCR.value = false
  
  // Show success message to user
  const totalFieldsApplied = Object.keys(ocrData).filter(key => ocrData[key] && ocrData[key] !== "").length
  const message = `✅ OCR data applied successfully!\n\n` +
    `📋 Form fields populated: ${totalFieldsApplied}\n` +
    `📄 Subcontract terms added: ${ocrTerms.length}\n` +
    `📑 Subcontract clauses added: ${ocrClauses.length}\n\n` +
    `Please review the data in the form tabs and make any necessary adjustments.`
  
  PopupService.success(message, 'OCR Data Applied Successfully')
  
  console.log('✅ OCR data applied successfully:', ocrData)
  console.log('✅ Updated form data:', formData.value)
  console.log('✅ Total subcontract terms:', contractTerms.value.length)
  console.log('✅ Total subcontract clauses:', contractClauses.value.length)
  
  // Debug: Log all terms and clauses for verification
  console.log('🔍 All subcontract terms:', contractTerms.value.map(t => ({
    id: t.term_id,
    title: t.term_title,
    text: t.term_text?.substring(0, 50) + '...'
  })))
  
  console.log('🔍 All subcontract clauses:', contractClauses.value.map(c => ({
    id: c.clause_id,
    name: c.clause_name,
    type: c.clause_type,
    text: c.clause_text?.substring(0, 50) + '...'
  })))
}

const applyOCRDataWithClear = () => {
  console.log('🔄 Clearing existing data and applying OCR data...')
  
  // Clear existing terms and clauses
  contractTerms.value = []
  contractClauses.value = []
  
  console.log('🧹 Cleared existing terms and clauses')
  
  // Apply OCR data
  applyOCRData()
}

const handleSaveDraft = () => {
        PopupService.success('Subcontract has been saved as draft successfully.', 'Subcontract Draft Saved')
  if (id) {
    navigate(`/contracts/${id}/edit-advanced`)
  } else {
    navigate('/contracts')
  }
}

// Trigger risk analysis in the background (non-blocking)
const triggerRiskAnalysis = async (contractId) => {
  try {
    console.log(`🔄 Triggering risk analysis for contract ${contractId} in background...`)
    
    // Show notification that risk analysis is being triggered
    showRiskAnalysisTriggered.value = true
    
    // Call the trigger endpoint using the contractsApi service (which includes auth headers)
    contractsApi.triggerContractRiskAnalysis(contractId)
      .then(data => {
        if (data.success) {
          console.log(`✅ Risk analysis triggered successfully for contract ${contractId}:`, data.message)
          // Hide the triggered notification and show the running notification
          showRiskAnalysisTriggered.value = false
          showRiskAnalysisNotification.value = true
        } else {
          console.warn(`⚠️ Failed to trigger risk analysis for contract ${contractId}:`, data.message)
          showRiskAnalysisTriggered.value = false
        }
      })
      .catch(error => {
        console.error(`❌ Error triggering risk analysis for contract ${contractId}:`, error)
        console.error(`❌ Error details:`, error.message)
        showRiskAnalysisTriggered.value = false
      })
    
    // Don't wait for the response - this is fire-and-forget
  } catch (error) {
    console.error(`❌ Error in triggerRiskAnalysis for contract ${contractId}:`, error)
    showRiskAnalysisTriggered.value = false
  }
}

// Normalize JSON-like fields coming from textareas or objects
const normalizeJsonField = (value, wrapKey) => {
  if (value === undefined || value === null) return null;
  // If it's a string coming from textarea
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) return null
    // Try to parse as JSON first
    try {
      const parsed = JSON.parse(trimmed)
      return parsed
    } catch (e) {
      // Fallback: wrap raw text into an object
      return { [wrapKey]: trimmed, type: 'text' }
    }
  }
  // If it's already an object or array
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      return value.length > 0 ? value : null
    }
    return Object.keys(value).length > 0 ? value : null
  }
  // Any other primitive -> null
  return null
}

// Map human-readable contract type labels to backend enum codes
const normalizeContractType = (value) => {
  if (!value) return ''
  const v = String(value).toUpperCase().replace(/\s+/g, '_')
  const map = {
    'SERVICE_AGREEMENT': 'SERVICE_AGREEMENT',
    'SOW': 'SOW',
    'STATEMENT_OF_WORK_(SOW)': 'SOW',
    'PURCHASE_ORDER': 'PURCHASE_ORDER',
    'LICENSE': 'LICENSE',
    'NDA': 'NDA',
    'NON-DISCLOSURE_AGREEMENT_(NDA)': 'NDA'
  }
  return map[v] || v
}

// Ensure JSON sent to backend is an object, never null
const safeJson = (value, wrapKey) => {
  const parsed = normalizeJsonField(value, wrapKey)
  return parsed === null ? {} : parsed
}

const handleSubmitForReview = async () => {
  try {
    // Clear any old session storage data first to ensure fresh preview
    console.log('🧹 Clearing old session storage before creating new preview')
    sessionStorage.removeItem('subcontractPreviewData')
    sessionStorage.removeItem('subcontractData')
    
    // Debug: Log current form data values
    console.log('🔍 Validating subcontract form data:')
    console.log('  - title:', formData.value.title, 'type:', typeof formData.value.title)
    console.log('  - type:', formData.value.type, 'type:', typeof formData.value.type)
    console.log('  - start_date:', formData.value.start_date, 'type:', typeof formData.value.start_date)
    console.log('  - end_date:', formData.value.end_date, 'type:', typeof formData.value.end_date)
    console.log('  - Full formData:', formData.value)
    
    // Validate required fields
    if (!formData.value.title || !formData.value.type || !formData.value.start_date || !formData.value.end_date) {
      console.log('❌ Validation failed - missing required fields')
      successMessage.value = ''
      errors.value.general = 'Please fill in all required fields (Title, Type, Start Date, End Date)'
      return
    }
    
    // Validate terms have required fields
    const invalidTerms = contractTerms.value.filter(term => !term.term_category || !term.term_text)
    if (invalidTerms.length > 0) {
      console.log('❌ Validation failed - terms missing required fields')
      successMessage.value = ''
      errors.value.general = `Please fill in Term Category and Term Text for all terms. ${invalidTerms.length} term(s) are incomplete.`
      return
    }
    
    // Validate vendor_id before storing subcontract data
    let vendorIdForPreview = parseInt(formData.value.vendor_id) || null
    
    // If vendor_id is null, try to get it from main contract data
    if (!vendorIdForPreview && mainContractData.value) {
      if (mainContractData.value.vendor && mainContractData.value.vendor.vendor_id) {
        vendorIdForPreview = parseInt(mainContractData.value.vendor.vendor_id)
        console.log('📝 Using vendor_id from main contract for preview:', vendorIdForPreview)
      } else if (mainContractData.value.vendor_id) {
        vendorIdForPreview = parseInt(mainContractData.value.vendor_id)
        console.log('📝 Using vendor_id from main contract vendor_id field for preview:', vendorIdForPreview)
      }
    }
    
    // Warn if vendor_id is still null (but allow preview)
    if (!vendorIdForPreview) {
      console.warn('⚠️ Warning: vendor_id is null - subcontract will require vendor information from parent contract')
    }

    // Optimize questionnaire loading: Only load what's needed
    let termsWithQuestionnaires = []
    
    if (contractTerms.value.length > 0) {
      // Check if any terms have selected templates (these need template questions)
      const termsWithTemplates = contractTerms.value.filter(term => {
        const termIdStr = String(term.term_id || '')
        return selectedTemplates.value[termIdStr]
      })
      
      // Check if any terms need questionnaires from allTermQuestionnaires
      const termsNeedingQuestionnaires = contractTerms.value.filter(term => {
        const termIdStr = String(term.term_id || '')
        // If template is selected, we'll load template questions (already cached or will be loaded)
        if (selectedTemplates.value[termIdStr]) return false
        // Otherwise, check if we need to load questionnaires
        return term.term_category || term.term_id
      })
      
      // Only load questionnaires if needed and not already loaded
      if (termsNeedingQuestionnaires.length > 0 && allTermQuestionnaires.value.length === 0) {
        console.log('📋 Loading questionnaires for terms without templates...')
        await loadTermQuestionnaires()
      }
      
      // Load template questions in parallel for terms with selected templates
      if (termsWithTemplates.length > 0) {
        console.log(`📋 Loading template questions for ${termsWithTemplates.length} terms with templates...`)
        const templateLoadPromises = termsWithTemplates.map(async (term) => {
          const termIdStr = String(term.term_id || '')
          const templateId = selectedTemplates.value[termIdStr]
          if (!templateId) return null
          
          // Check cache first
          if (templateQuestionsCache.value[templateId]) {
            return { term, questionnaires: templateQuestionsCache.value[templateId] }
          }
          
          try {
            const response = await apiService.getTemplateQuestions(templateId, null, null)
            const questions = response.questions || []
            const mappedQuestions = questions.map(q => ({
              question_id: q.question_id,
              question_text: q.question_text || '',
              question_type: mapAnswerTypeToQuestionType(q.answer_type || 'TEXT'),
              is_required: q.is_required || false,
              scoring_weightings: q.weightage || 10.0,
              question_category: q.question_category || 'Contract',
              options: q.options || [],
              help_text: q.help_text || '',
              metric_name: q.metric_name || null,
              allow_document_upload: q.allow_document_upload || false,
              template_id: templateId
            }))
            // Cache the questions
            templateQuestionsCache.value[templateId] = mappedQuestions
            return { term, questionnaires: mappedQuestions }
          } catch (error) {
            console.error(`Error loading template questions for term ${term.term_id}:`, error)
            return { term, questionnaires: [] }
          }
        })
        
        const templateResults = await Promise.all(templateLoadPromises)
        templateResults.forEach(result => {
          if (result) {
            const termPlain = JSON.parse(JSON.stringify(result.term))
            termsWithQuestionnaires.push({
              ...termPlain,
              questionnaires: result.questionnaires
            })
          }
        })
      }
      
      // Process remaining terms (those without templates) - use already loaded questionnaires
      const processedTermIds = new Set(termsWithQuestionnaires.map(t => String(t.term_id || '')))
      for (const term of contractTerms.value) {
        const termIdStr = String(term.term_id || '')
        if (processedTermIds.has(termIdStr)) continue
        
        const questionnaires = await getQuestionnairesForTerm(term.term_id, term.term_category, term.term_title)
        const termPlain = JSON.parse(JSON.stringify(term))
        termsWithQuestionnaires.push({
          ...termPlain,
          questionnaires
        })
      }
    }
    
    // Store subcontract data in session storage for the main contract page
    const subcontractData = {
      contract_title: formData.value.title,
      contract_number: formData.value.contract_number || `SUB-${Date.now()}`,
      contract_type: formData.value.type,
      contract_category: formData.value.contract_category || 'services',
      vendor_id: vendorIdForPreview,
      contract_value: parseFloat(formData.value.value) || 0,
      currency: formData.value.currency,
      liability_cap: parseFloat(formData.value.liability_cap) || null,
      start_date: formData.value.start_date,
      end_date: formData.value.end_date,
      renewal_terms: formData.value.renewal_terms,
      auto_renewal: formData.value.auto_renewal || false,
      notice_period_days: formData.value.notice_period_days || 30,
      contract_owner: formData.value.contract_owner,
      legal_reviewer: formData.value.legal_reviewer,
      assigned_to: formData.value.assigned_to,
      priority: formData.value.priority || 'medium',
      compliance_status: formData.value.compliance_status || 'under_review',
      dispute_resolution_method: formData.value.dispute_resolution_method,
      governing_law: formData.value.governing_law,
      contract_risk_score: formData.value.contract_risk_score,
      termination_clause_type: formData.value.termination_clause || 'convenience',
      insurance_requirements: normalizeJsonField(formData.value.insurance_requirements, 'requirements'),
      data_protection_clauses: normalizeJsonField(formData.value.data_protection_clauses, 'clauses'),
      custom_fields: normalizeJsonField(formData.value.custom_fields, 'fields'),
      compliance_framework: (formData.value.compliance_frameworks && formData.value.compliance_frameworks.length > 0) ? formData.value.compliance_frameworks[0] : (formData.value.compliance_framework || ''),
      file_path: formData.value.file_path || '',  // S3 URL for uploaded subcontract document
      permission_required: Boolean(formData.value.permission_required)  // Whether parent contract can view this subcontract
      // Note: terms and clauses are saved separately via saveContractTerms() and saveContractClauses() to avoid duplication
    }
    
    console.log('💾 Storing subcontract data in session storage:', subcontractData)
    sessionStorage.setItem('subcontractData', JSON.stringify(subcontractData))
    
    // Store preview data for restoration when returning from preview
    const previewData = {
      formData: formData.value,
      contractTerms: contractTerms.value,
      contractClauses: contractClauses.value,
      selectedTemplates: selectedTemplates.value,
      timestamp: Date.now() // Add timestamp for debugging
    }
    
    console.log('💾 Storing FRESH subcontract preview data:', previewData)
    console.log('🔍 Preview data details:')
    console.log('  - title:', previewData.formData.title)
    console.log('  - contract_number:', previewData.formData.contract_number)
    console.log('  - value:', previewData.formData.value)
    console.log('  - liability_cap:', previewData.formData.liability_cap)
    console.log('  - start_date:', previewData.formData.start_date)
    console.log('  - end_date:', previewData.formData.end_date)
    console.log('  - terms count:', previewData.contractTerms.length)
    console.log('  - clauses count:', previewData.contractClauses.length)
    sessionStorage.setItem('subcontractPreviewData', JSON.stringify(previewData))
    
    // Load main contract data for preview
    await loadMainContractForPreview()
    
    // Update preview timestamp to force refresh
    previewTimestamp.value = Date.now()
    console.log('🔄 Preview timestamp updated:', previewTimestamp.value)
    
    showPreview.value = true
    console.log('✅ Preview dialog opened with fresh data')
  } catch (error) {
    console.error('Error preparing subcontract data:', error)
    successMessage.value = ''
    errors.value.general = error.message || 'Failed to prepare subcontract data'
  }
}

const handleFinalSubmit = async () => {
  try {
    showPreview.value = false
    isSubmitting.value = true
    
    // Debug: Log current form data values
    console.log('🔍 Final submit - validating subcontract form data:')
    console.log('  - title:', formData.value.title, 'type:', typeof formData.value.title)
    console.log('  - type:', formData.value.type, 'type:', typeof formData.value.type)
    console.log('  - start_date:', formData.value.start_date, 'type:', typeof formData.value.start_date)
    console.log('  - end_date:', formData.value.end_date, 'type:', typeof formData.value.end_date)
    console.log('  - Full formData:', formData.value)
    
    // Validate required fields
    if (!formData.value.title || !formData.value.type || !formData.value.start_date || !formData.value.end_date) {
      console.log('❌ Final submit validation failed - missing required fields')
      successMessage.value = ''
      errors.value.general = 'Please fill in all required fields (Title, Type, Start Date, End Date)'
      return
    }
    
    // Validate terms have required fields
    const invalidTerms = contractTerms.value.filter(term => !term.term_category || !term.term_text)
    if (invalidTerms.length > 0) {
      console.log('❌ Final submit validation failed - terms missing required fields')
      successMessage.value = ''
      errors.value.general = `Please fill in Term Category and Term Text for all terms. ${invalidTerms.length} term(s) are incomplete.`
      return
    }
    
    // Debug form data before preparing subcontract data
    console.log('🔍 Form data validation before submission:')
    console.log('  - title:', formData.value.title, 'empty?', !formData.value.title)
    console.log('  - type:', formData.value.type, 'empty?', !formData.value.type)
    console.log('  - start_date:', formData.value.start_date, 'empty?', !formData.value.start_date)
    console.log('  - end_date:', formData.value.end_date, 'empty?', !formData.value.end_date)
    console.log('  - Full formData:', formData.value)
    
    // Additional validation for required fields
    if (!formData.value.title || !formData.value.type) {
      console.error('❌ Missing required fields:')
      console.error('  - title missing:', !formData.value.title)
      console.error('  - type missing:', !formData.value.type)
      successMessage.value = ''
      errors.value.general = 'Please fill in all required fields (Title and Type) before submitting.'
      return
    }
    
    // Validate vendor_id before preparing subcontract data
    let vendorId = parseInt(formData.value.vendor_id) || null
    
    // If vendor_id is null, try to get it from main contract data
    if (!vendorId && mainContractData.value) {
      if (mainContractData.value.vendor && mainContractData.value.vendor.vendor_id) {
        vendorId = parseInt(mainContractData.value.vendor.vendor_id)
        console.log('📝 Using vendor_id from main contract:', vendorId)
      } else if (mainContractData.value.vendor_id) {
        vendorId = parseInt(mainContractData.value.vendor_id)
        console.log('📝 Using vendor_id from main contract vendor_id field:', vendorId)
      }
    }
    
    // Final validation: vendor_id must not be null
    if (!vendorId) {
      console.error('❌ vendor_id is required but is null or invalid')
      successMessage.value = ''
      errors.value.general = 'Vendor information is required. Please ensure the parent contract has a valid vendor assigned.'
      return
    }
    
    console.log('✅ Final vendor_id for subcontract:', vendorId)
    
    // Optimize questionnaire loading: Only load what's needed
    let termsWithQuestionnaires = []
    
    if (contractTerms.value.length > 0) {
      // Check if any terms have selected templates (these need template questions)
      const termsWithTemplates = contractTerms.value.filter(term => {
        const termIdStr = String(term.term_id || '')
        return selectedTemplates.value[termIdStr]
      })
      
      // Check if any terms need questionnaires from allTermQuestionnaires
      const termsNeedingQuestionnaires = contractTerms.value.filter(term => {
        const termIdStr = String(term.term_id || '')
        // If template is selected, we'll load template questions (already cached or will be loaded)
        if (selectedTemplates.value[termIdStr]) return false
        // Otherwise, check if we need to load questionnaires
        return term.term_category || term.term_id
      })
      
      // Only load questionnaires if needed and not already loaded
      if (termsNeedingQuestionnaires.length > 0 && allTermQuestionnaires.value.length === 0) {
        console.log('📋 Loading questionnaires for terms without templates...')
        await loadTermQuestionnaires()
      }
      
      // Load template questions in parallel for terms with selected templates
      if (termsWithTemplates.length > 0) {
        console.log(`📋 Loading template questions for ${termsWithTemplates.length} terms with templates...`)
        const templateLoadPromises = termsWithTemplates.map(async (term) => {
          const termIdStr = String(term.term_id || '')
          const templateId = selectedTemplates.value[termIdStr]
          if (!templateId) return null
          
          // Check cache first
          if (templateQuestionsCache.value[templateId]) {
            return { term, questionnaires: templateQuestionsCache.value[templateId] }
          }
          
          try {
            const response = await apiService.getTemplateQuestions(templateId, null, null)
            const questions = response.questions || []
            const mappedQuestions = questions.map(q => ({
              question_id: q.question_id,
              question_text: q.question_text || '',
              question_type: mapAnswerTypeToQuestionType(q.answer_type || 'TEXT'),
              is_required: q.is_required || false,
              scoring_weightings: q.weightage || 10.0,
              question_category: q.question_category || 'Contract',
              options: q.options || [],
              help_text: q.help_text || '',
              metric_name: q.metric_name || null,
              allow_document_upload: q.allow_document_upload || false,
              template_id: templateId
            }))
            // Cache the questions
            templateQuestionsCache.value[templateId] = mappedQuestions
            return { term, questionnaires: mappedQuestions }
          } catch (error) {
            console.error(`Error loading template questions for term ${term.term_id}:`, error)
            return { term, questionnaires: [] }
          }
        })
        
        const templateResults = await Promise.all(templateLoadPromises)
        templateResults.forEach(result => {
          if (result) {
            const termPlain = JSON.parse(JSON.stringify(result.term))
            termsWithQuestionnaires.push({
              ...termPlain,
              questionnaires: result.questionnaires
            })
          }
        })
      }
      
      // Process remaining terms (those without templates) - use already loaded questionnaires
      const processedTermIds = new Set(termsWithQuestionnaires.map(t => String(t.term_id || '')))
      for (const term of contractTerms.value) {
        const termIdStr = String(term.term_id || '')
        if (processedTermIds.has(termIdStr)) continue
        
        const questionnaires = await getQuestionnairesForTerm(term.term_id, term.term_category, term.term_title)
        const termPlain = JSON.parse(JSON.stringify(term))
        termsWithQuestionnaires.push({
          ...termPlain,
          questionnaires
        })
      }
    }
    
    // Prepare subcontract data
    const subcontractData = {
      contract_title: formData.value.title,
      contract_number: formData.value.contract_number || `SUB-${Date.now()}`,
      contract_type: normalizeContractType(formData.value.type),
      contract_category: formData.value.contract_category || 'services',
      vendor_id: vendorId,
      contract_value: parseFloat(formData.value.value) || 0,
      currency: formData.value.currency,
      liability_cap: parseFloat(formData.value.liability_cap) || null,
      start_date: formData.value.start_date,
      end_date: formData.value.end_date,
      renewal_terms: formData.value.renewal_terms,
      auto_renewal: Boolean(formData.value.auto_renewal),
      notice_period_days: parseInt(formData.value.notice_period_days) || 30,
      contract_owner: parseInt(formData.value.contract_owner) || null,
      legal_reviewer: parseInt(formData.value.legal_reviewer) || null,
      assigned_to: parseInt(formData.value.assigned_to) || null,
      priority: formData.value.priority || 'medium',
      compliance_status: formData.value.compliance_status || 'under_review',
      dispute_resolution_method: formData.value.dispute_resolution,
      governing_law: formData.value.governing_law,
      contract_risk_score: parseFloat(formData.value.contract_risk_score) || null,
      termination_clause_type: formData.value.termination_clause || 'convenience',
      insurance_requirements: safeJson(formData.value.insurance_requirements, 'requirements'),
      data_protection_clauses: safeJson(formData.value.data_protection_clauses, 'clauses'),
      custom_fields: safeJson(formData.value.custom_fields, 'fields'),
      compliance_framework: (formData.value.compliance_frameworks && formData.value.compliance_frameworks.length > 0) ? formData.value.compliance_frameworks[0] : (formData.value.compliance_framework || ''),
      file_path: formData.value.file_path || '',  // S3 URL for uploaded subcontract document
      permission_required: Boolean(formData.value.permission_required)  // Whether parent contract can view this subcontract
      // Note: terms and clauses are saved separately via saveContractTerms() and saveContractClauses() to avoid duplication
    }
    
    // Debug the prepared subcontract data
    console.log('🔍 Prepared subcontract data:')
    console.log('  - contract_title:', subcontractData.contract_title)
    console.log('  - contract_type:', subcontractData.contract_type)
    console.log('  - contract_number:', subcontractData.contract_number)
    console.log('  - start_date:', subcontractData.start_date)
    console.log('  - end_date:', subcontractData.end_date)
    
    // Prepare main contract data
    const mainContractDataToSubmit = {
      ...mainContractData.value,
      contract_kind: 'MAIN',
      status: 'PENDING_ASSIGNMENT',
      workflow_stage: 'under_review'
    }
    
    // Prepare subcontract data with parent relationship
    const subcontractFormData = {
      ...subcontractData,
      contract_kind: 'SUBCONTRACT',
      parent_contract_id: mainContractDataToSubmit.contract_id,
      main_contract_id: mainContractDataToSubmit.contract_id,
      status: 'PENDING_ASSIGNMENT',
      workflow_stage: 'under_review'
    }
    
    console.log('📤 Creating both contracts together:', {
      mainContract: mainContractDataToSubmit,
      subcontract: subcontractFormData
    })
    
    // Debug terms and clauses data
    console.log('🔍 Subcontract terms data:', subcontractFormData.terms)
    console.log('🔍 Subcontract clauses data:', subcontractFormData.clauses)
    console.log('🔍 Terms count:', subcontractFormData.terms?.length || 0)
    console.log('🔍 Clauses count:', subcontractFormData.clauses?.length || 0)
    
    // Debug JSON fields specifically
    console.log('🔍 Subcontract JSON fields debug:')
    console.log('  - insurance_requirements:', subcontractFormData.insurance_requirements, 'type:', typeof subcontractFormData.insurance_requirements)
    console.log('  - data_protection_clauses:', subcontractFormData.data_protection_clauses, 'type:', typeof subcontractFormData.data_protection_clauses)
    console.log('  - custom_fields:', subcontractFormData.custom_fields, 'type:', typeof subcontractFormData.custom_fields)
    
    // Use the imported API service
    
    let response
    
    // Check if we're creating a subcontract for an existing parent contract
    if (id && mainContractData.value && mainContractData.value.contract_id) {
      console.log('📝 Creating subcontract with versioning for existing parent contract:', mainContractData.value.contract_id)
      console.log('🔄 Version type selected:', versionType.value)
      
      // Create subcontract with parent contract versioning
      const subcontractWithVersioning = {
        ...subcontractFormData,
        version_type: versionType.value
      }
      
      // Use the new versioning endpoint
      response = await contractsApi.createSubcontractWithVersioning(mainContractData.value.contract_id, subcontractWithVersioning)
    
    if (response.success) {
        // Get the new subcontract's contract ID from the response
        const subcontractId = response.data?.subcontract?.contract_id || response.data?.subcontract?.id || response.data?.contract_id || response.data?.id || response.contract_id
        const newParentContractId = response.data?.parent_contract?.contract_id || response.data?.parent_contract?.id
        
        console.log('🔍 Subcontract creation with versioning response:', response)
        console.log('🔍 Response data structure:', response.data)
        console.log('🔍 Subcontract contract ID:', subcontractId)
        console.log('🔍 New parent contract ID:', newParentContractId)
        console.log('🔍 Original parent contract ID:', mainContractData.value?.contract_id)
        
        // Save terms and clauses if any exist
        if (contractTerms.value.length > 0) {
          await saveContractTerms(subcontractId)
        }
        
        if (contractClauses.value.length > 0) {
          await saveContractClauses(subcontractId)
        }
        
        // Clear subcontract data from session storage
        sessionStorage.removeItem('subcontractData')
        
        // Show success message and risk analysis notification
        successMessage.value = `Subcontract Created Successfully! Parent contract has been versioned (${versionType.value} version) and both contracts have been set to PENDING_ASSIGNMENT status.`
        showRiskAnalysisNotification.value = true
        
        // Trigger risk analysis for both contracts in the background (non-blocking)
        if (newParentContractId) {
          console.log(`🔄 Triggering risk analysis for NEW PARENT CONTRACT VERSION with ID: ${newParentContractId}`)
          triggerRiskAnalysis(newParentContractId)
        }
        
        // Trigger risk analysis for the NEW SUBCONTRACT (not the parent contract)
        if (subcontractId && subcontractId !== mainContractData.value?.contract_id) {
          console.log(`🔄 Triggering risk analysis for NEW SUBCONTRACT with ID: ${subcontractId}`)
          triggerRiskAnalysis(subcontractId)
        } else {
          console.error('❌ CRITICAL: Subcontract created but no valid subcontract ID found!')
          console.error('❌ Response data:', response.data)
          console.error('❌ Full response:', response)
          // This should not happen - if it does, there's a backend issue
          throw new Error('Subcontract created but no valid subcontract ID returned from server')
        }
        
        // Navigate after a short delay
        setTimeout(() => {
          navigate('/contracts')
        }, 2000)
      } else {
        throw new Error(response.message || 'Failed to create subcontract')
      }
    } else {
      // Create both contracts together (new parent + subcontract)
      console.log('📝 Creating new parent contract and subcontract together')
      response = await contractsApi.createContractWithSubcontract(mainContractDataToSubmit, subcontractFormData)
    
    if (response.success) {
      console.log('✅ Both contracts created successfully:', response.data)
      
      // Get contract IDs from response
      const mainContractId = response.data?.main_contract?.contract_id || response.data?.main_contract?.id
      const subcontractId = response.data?.subcontract?.contract_id || response.data?.subcontract?.id
      
      console.log('🔍 Both contracts creation response:', response)
      console.log('🔍 Response data structure:', response.data)
      console.log('🔍 Main contract ID:', mainContractId)
      console.log('🔍 Subcontract ID:', subcontractId)
      
      // Save terms and clauses for the subcontract if any exist
      // Note: Main contract keeps its existing terms/clauses from mainContractData.value
      if (contractTerms.value.length > 0) {
        console.log('📝 Saving contract terms for subcontract...')
        console.log('🔍 Terms to save:', contractTerms.value.length, 'terms')
        if (subcontractId) {
          await saveContractTerms(subcontractId)
          console.log('✅ Contract terms saved for subcontract')
        } else {
          console.error('❌ No subcontract ID available for saving terms')
        }
      } else {
        console.log('ℹ️ No contract terms to save')
      }
      
      if (contractClauses.value.length > 0) {
        console.log('📝 Saving contract clauses for subcontract...')
        console.log('🔍 Clauses to save:', contractClauses.value.length, 'clauses')
        if (subcontractId) {
          await saveContractClauses(subcontractId)
          console.log('✅ Contract clauses saved for subcontract')
        } else {
          console.error('❌ No subcontract ID available for saving clauses')
        }
      } else {
        console.log('ℹ️ No contract clauses to save')
      }
      
      // Clear subcontract data from session storage
      sessionStorage.removeItem('subcontractData')
      
      // Show success message and risk analysis notification
      successMessage.value = 'Contract and Subcontract Created Successfully! Both contracts have been created and submitted for review.'
      showRiskAnalysisNotification.value = true
      
      // Trigger risk analysis for both contracts in the background (non-blocking)
      if (mainContractId) {
        console.log(`🔄 Triggering risk analysis for NEW MAIN CONTRACT with ID: ${mainContractId}`)
        triggerRiskAnalysis(mainContractId)
      } else {
        console.error('❌ CRITICAL: Main contract created but no valid main contract ID found!')
      }
      
      if (subcontractId) {
        console.log(`🔄 Triggering risk analysis for NEW SUBCONTRACT with ID: ${subcontractId}`)
        triggerRiskAnalysis(subcontractId)
      } else {
        console.error('❌ CRITICAL: Subcontract created but no valid subcontract ID found!')
      }
      
      // Navigate after a short delay
      setTimeout(() => {
        navigate('/contracts')
      }, 2000)
    } else {
      throw new Error(response.message || 'Failed to create contract and subcontract')
      }
    }
    
  } catch (error) {
    console.error('Error creating contract and subcontract:', error)
    successMessage.value = ''
    errors.value.general = error.message || 'Failed to create contract and subcontract'
  } finally {
    isSubmitting.value = false
  }
}

const addNewTerm = () => {
  const newTerm = {
    term_id: `term_${Date.now()}`,
    term_category: '',
    term_title: '',
    term_text: '',
    risk_level: 'Low', // Default value
    compliance_status: 'Pending', // Default value
    is_standard: false,
    approval_status: 'Pending', // Default value
    approved_by: '',
    approved_at: '',
    version_number: '1.0', // Default value
    parent_term_id: '',
    created_by: formData.value.contract_owner || ''
  }
  contractTerms.value.push(newTerm)
}

const removeTerm = (index) => {
  contractTerms.value.splice(index, 1)
}

const addNewClause = () => {
  const newClause = {
    clause_id: `clause_${Date.now()}`,
    clause_name: '',
    clause_type: 'standard',
    clause_text: '',
    risk_level: 'low', // Default value
    legal_category: '',
    version_number: '1', // Default value
    is_standard: false,
    created_by: formData.value.contract_owner || ''
  }
  contractClauses.value.push(newClause)
}

const removeClause = (clauseId) => {
  contractClauses.value = contractClauses.value.filter(c => c.clause_id !== clauseId)
}

// Questionnaire helpers
const loadTermQuestionnaires = async () => {
  try {
    // Only load questionnaires for terms that don't have selected templates
    // Terms with templates will use template questions instead
    const termsNeedingQuestionnaires = contractTerms.value.filter(term => {
      const termIdStr = String(term.term_id || '')
      // Skip if template is selected (will use template questions)
      if (selectedTemplates.value[termIdStr]) return false
      // Only load if term has category or term_id
      return term.term_category || term.term_id
    })
    
    if (termsNeedingQuestionnaires.length === 0) {
      console.log('✅ No terms need questionnaires (all have templates or no category/term_id)')
      return
    }
    
    const uniqueCategories = [...new Set(termsNeedingQuestionnaires.map(t => t.term_category).filter(Boolean))]
    const uniqueTermIds = [...new Set(termsNeedingQuestionnaires.map(t => t.term_id).filter(Boolean))]
    const loadPromises = []

    // Load by category (more efficient - one call per category)
    uniqueCategories.forEach(category => {
      loadPromises.push(
        apiService.getQuestionnairesByTermTitle(null, null, category)
          .then(response => {
            const questionnaires = response.questionnaires || response.results || response || []
            return questionnaires.map(q => ({
              ...q,
              term_category: category,
              _matched_term_category: category
            }))
          })
          .catch(error => {
            console.error(`Error loading questionnaires for category "${category}":`, error)
            return []
          })
      )
    })

    // Only load by term_id if we have term_ids that aren't covered by categories
    // This reduces redundant API calls
    const termIdsWithoutCategories = uniqueTermIds.filter(termId => {
      const term = contractTerms.value.find(t => String(t.term_id) === String(termId))
      return term && !term.term_category
    })
    
    termIdsWithoutCategories.forEach(termId => {
      loadPromises.push(
        apiService.getQuestionnairesByTermTitle(null, termId, null)
          .then(response => {
            const questionnaires = response.questionnaires || response.results || response || []
            return questionnaires.map(q => ({
              ...q,
              _matched_term_id: termId
            }))
          })
          .catch(error => {
            console.error(`Error loading questionnaires for term "${termId}":`, error)
            return []
          })
      )
    })

    if (loadPromises.length === 0) {
      console.log('✅ No questionnaire API calls needed')
      return
    }

    console.log(`📋 Loading questionnaires: ${uniqueCategories.length} categories, ${termIdsWithoutCategories.length} term_ids`)
    const results = await Promise.all(loadPromises)
    const combined = results.flat()
    const seen = new Set()
    allTermQuestionnaires.value = combined.filter(q => {
      if (seen.has(q.question_id)) return false
      seen.add(q.question_id)
      return true
    })
    console.log(`✅ Loaded ${allTermQuestionnaires.value.length} unique questionnaires`)
  } catch (error) {
    console.error('Error loading term questionnaires:', error)
  }
}

const hasQuestionnaires = (term) => {
  if (!term) return false
  const category = term.term_category
  const termId = term.term_id ? String(term.term_id) : ''
  return allTermQuestionnaires.value.some(q => {
    const qCategory = (q.term_category || q._matched_term_category || '').toLowerCase()
    const qTermId = q.term_id ? String(q.term_id) : ''
    if (category && qCategory === category.toLowerCase()) return true
    if (termId && (qTermId === termId || qTermId.includes(termId) || termId.includes(qTermId))) return true
    return false
  })
}

const getQuestionnaireCount = (term) => {
  if (!term) return 0
  const category = term.term_category
  const termId = term.term_id ? String(term.term_id) : ''
  return allTermQuestionnaires.value.filter(q => {
    const qCategory = (q.term_category || q._matched_term_category || '').toLowerCase()
    const qTermId = q.term_id ? String(q.term_id) : ''
    if (category && qCategory === category.toLowerCase()) return true
    if (termId && (qTermId === termId || qTermId.includes(termId) || termId.includes(qTermId))) return true
    return false
  }).length
}

const getTemplatesForTerm = (termId) => {
  if (!termId) return []
  const entry = allTermTemplates.value.find(t => t.term_id === String(termId))
  return entry?.templates || []
}

const hasLoadedTemplatesForTerm = (termId) => {
  if (!termId) return false
  return loadedTemplatesForTerms.value.has(String(termId))
}

const getSelectedTemplateForTerm = (termId) => {
  if (!termId) return null
  const termIdStr = String(termId)
  const templateId = selectedTemplates.value[termIdStr]
  if (!templateId) return null
  return getTemplatesForTerm(termIdStr).find(t => t.template_id === templateId) || null
}

const selectTemplateForTerm = (termId, template) => {
  const termIdStr = String(termId)
  selectedTemplates.value = {
    ...selectedTemplates.value,
    [termIdStr]: template.template_id
  }
}

const clearTemplateSelection = (termId) => {
  const termIdStr = String(termId || '')
  if (!termIdStr) return
  if (selectedTemplates.value[termIdStr]) {
    const updated = { ...selectedTemplates.value }
    delete updated[termIdStr]
    selectedTemplates.value = updated
  }
}

const resetTemplatesForTerm = (termId) => {
  const termIdStr = String(termId || '')
  if (!termIdStr) return

  const existingIndex = allTermTemplates.value.findIndex(t => t.term_id === termIdStr)
  if (existingIndex >= 0) {
    allTermTemplates.value.splice(existingIndex, 1)
  }

  if (selectedTemplates.value[termIdStr]) {
    const updated = { ...selectedTemplates.value }
    delete updated[termIdStr]
    selectedTemplates.value = updated
  }

  loadedTemplatesForTerms.value.delete(termIdStr)
  setTemplateSectionExpanded(termIdStr, false)
}

const mapAnswerTypeToQuestionType = (answerType) => {
  const typeMap = {
    'TEXT': 'text',
    'TEXTAREA': 'textarea',
    'NUMBER': 'number',
    'BOOLEAN': 'boolean',
    'YES_NO': 'yes/no',
    'MULTIPLE_CHOICE': 'multiple_choice',
    'CHECKBOX': 'checkbox',
    'RATING': 'rating',
    'SCALE': 'scale',
    'DATE': 'date'
  }
  return typeMap[answerType?.toUpperCase()] || 'text'
}

const mapQuestionTypeToAnswerType = (questionType) => {
  const typeMap = {
    'text': 'TEXT',
    'textarea': 'TEXTAREA',
    'number': 'NUMBER',
    'boolean': 'BOOLEAN',
    'yes/no': 'YES_NO',
    'multiple_choice': 'MULTIPLE_CHOICE',
    'checkbox': 'CHECKBOX',
    'rating': 'RATING',
    'scale': 'SCALE',
    'date': 'DATE'
  }
  return typeMap[questionType?.toLowerCase()] || 'TEXT'
}

const loadTemplatesForTerm = async (term) => {
  if (!term) return
  const termIdStr = String(term.term_id || '')
  try {
    const response = await apiService.getTemplatesByTerm(term.term_title, termIdStr, term.term_category)
    const templates = response.templates || response || []
    const existingIndex = allTermTemplates.value.findIndex(t => t.term_id === termIdStr)
    if (existingIndex >= 0) {
      allTermTemplates.value.splice(existingIndex, 1, { term_id: termIdStr, templates })
    } else {
      allTermTemplates.value.push({ term_id: termIdStr, templates })
    }
    loadedTemplatesForTerms.value.add(termIdStr)
  } catch (error) {
    console.error('Error loading templates:', error)
    PopupService.error(error.message || 'Failed to load templates.', 'Template Error')
  }
}

const viewTemplateQuestions = async (termId, templateId) => {
  try {
    const term = contractTerms.value.find(t => String(t.term_id) === String(termId))
    
    // Check cache first
    if (templateQuestionsCache.value[templateId]) {
      console.log(`✅ Using cached questions for template ${templateId}`)
      selectedQuestionnaires.value = templateQuestionsCache.value[templateId]
    } else {
      const response = await apiService.getTemplateQuestions(templateId, String(termId), term?.term_category)
      const questions = response.questions || []
      const mappedQuestions = questions.map(q => ({
        question_id: q.question_id,
        question_text: q.question_text || '',
        question_type: mapAnswerTypeToQuestionType(q.answer_type || 'TEXT'),
        is_required: q.is_required || false,
        scoring_weightings: q.weightage || 10.0,
        question_category: q.question_category || 'Contract',
        options: q.options || [],
        help_text: q.help_text || '',
        metric_name: q.metric_name || null,
        allow_document_upload: q.allow_document_upload || false
      }))
      // Cache the questions
      templateQuestionsCache.value[templateId] = mappedQuestions
      selectedQuestionnaires.value = mappedQuestions
    }
    
    selectedTermTitle.value = term?.term_title || 'Unknown Term'
    selectedTermId.value = termId
    showQuestionnairesModal.value = true
  } catch (error) {
    console.error('Error loading template questions:', error)
    PopupService.error(error.message || 'Failed to load template questions.', 'Template Error')
  }
}

const closeQuestionnairesModal = () => {
  showQuestionnairesModal.value = false
  selectedTermTitle.value = ''
  selectedTermId.value = null
  selectedQuestionnaires.value = []
}

const viewQuestionnaires = async (term) => {
  if (!term) return
  try {
    const response = await apiService.getQuestionnairesByTermTitle(
      term.term_category ? null : term.term_title,
      term.term_id,
      term.term_category
    )
    const questionnaires = response.questionnaires || response.results || response || []
    selectedQuestionnaires.value = questionnaires.map(q => ({
      question_id: q.question_id,
      question_text: q.question_text || '',
      question_type: q.question_type || 'text',
      is_required: q.is_required || false,
      scoring_weightings: q.scoring_weightings || 10.0,
      question_category: q.question_category || 'Contract',
      options: q.options || [],
      help_text: q.help_text || '',
      metric_name: q.metric_name || null,
      allow_document_upload: q.allow_document_upload || false
    }))
    selectedTermTitle.value = term.term_title || 'Unknown Term'
    selectedTermId.value = term.term_id
    showQuestionnairesModal.value = true
  } catch (error) {
    console.error('Error loading questionnaires:', error)
    PopupService.error(error.message || 'Failed to load questionnaires.', 'Questionnaires Error')
  }
}

const editQuestionnaires = (term, existingQuestionnaires = []) => {
  if (!term) return

  sessionStorage.setItem('subcontract_advanced_draft', JSON.stringify({
    formData: formData.value,
    contractTerms: contractTerms.value,
    contractClauses: contractClauses.value,
    selectedTemplates: selectedTemplates.value
  }))

  if (existingQuestionnaires.length > 0) {
    const questionsForTemplate = existingQuestionnaires.map(q => ({
      question_text: q.question_text || '',
      help_text: q.help_text || '',
      question_category: q.question_category || '',
      answer_type: mapQuestionTypeToAnswerType(q.question_type || 'text'),
      is_required: q.is_required || false,
      weightage: q.scoring_weightings ?? 10.0,
      term_id: term.term_id,
      allow_document_upload: q.allow_document_upload || false,
      options: Array.isArray(q.options) ? q.options : [],
      _optionsString: Array.isArray(q.options) ? q.options.join(', ') : '',
      metric_name: q.metric_name || null
    }))
    sessionStorage.setItem('questionnaire_edit_data', JSON.stringify({
      questions: questionsForTemplate,
      term_id: term.term_id,
      term_title: term.term_title,
      term_category: term.term_category
    }))
  }

  closeQuestionnairesModal()
  router.push({
    path: '/questionnaire-templates',
    query: {
      module_type: 'CONTRACT',
      term_id: term.term_id,
      term_title: term.term_title,
      term_category: term.term_category,
      return_to: 'contract-subcontract-advanced',
      contract_id: id,
      edit_mode: existingQuestionnaires.length > 0 ? 'true' : 'false'
    }
  })
}

const createQuestionnaires = (term) => {
  if (!term) return

  PopupService.confirm(
    `Create questionnaires for "${term.term_title || 'Term'}"? You will be redirected to the Questionnaire Templates page.`,
    'Create Questionnaires',
    () => {
      sessionStorage.setItem('subcontract_advanced_draft', JSON.stringify({
        formData: formData.value,
        contractTerms: contractTerms.value,
        contractClauses: contractClauses.value,
        selectedTemplates: selectedTemplates.value
      }))

      router.push({
        path: '/questionnaire-templates',
        query: {
          module_type: 'CONTRACT',
          term_id: term.term_id,
          term_title: term.term_title,
          term_category: term.term_category,
          return_to: 'contract-subcontract-advanced',
          contract_id: id
        }
      })
    }
  )
}

const getQuestionnairesForTerm = async (termId, termCategory, termTitle) => {
  const termIdStr = String(termId || '')
  const selectedTemplateId = selectedTemplates.value[termIdStr]

  // If a template is selected, use cached questions or load from API
  if (selectedTemplateId) {
    // Check cache first
    if (templateQuestionsCache.value[selectedTemplateId]) {
      console.log(`✅ Using cached questions for template ${selectedTemplateId}`)
      return templateQuestionsCache.value[selectedTemplateId]
    }
    
    try {
      const response = await apiService.getTemplateQuestions(selectedTemplateId, null, null)
      const questions = response.questions || []
      const mappedQuestions = questions.map(q => ({
        question_id: q.question_id,
        question_text: q.question_text || '',
        question_type: mapAnswerTypeToQuestionType(q.answer_type || 'TEXT'),
        is_required: q.is_required || false,
        scoring_weightings: q.weightage || 10.0,
        question_category: q.question_category || 'Contract',
        options: q.options || [],
        help_text: q.help_text || '',
        metric_name: q.metric_name || null,
        allow_document_upload: q.allow_document_upload || false,
        template_id: selectedTemplateId
      }))
      // Cache the questions
      templateQuestionsCache.value[selectedTemplateId] = mappedQuestions
      return mappedQuestions
    } catch (error) {
      console.error(`Error loading questions from template ${selectedTemplateId}:`, error)
      return []
    }
  }

  // If no template selected, use questionnaires from allTermQuestionnaires (already loaded)
  if (!allTermQuestionnaires.value.length) return []
  const termCategoryLower = termCategory ? termCategory.toLowerCase() : ''
  const termIdLower = termIdStr.toLowerCase()
  return allTermQuestionnaires.value.filter(q => {
    const qCategory = (q.term_category || q._matched_term_category || '').toLowerCase()
    const qTermId = String(q.term_id || '').toLowerCase()
    if (termCategoryLower && qCategory === termCategoryLower) return true
    if (termIdLower && (qTermId === termIdLower || qTermId.includes(termIdLower) || termIdLower.includes(qTermId))) return true
    return false
  }).map(q => ({
    question_id: q.question_id,
    question_text: q.question_text || '',
    question_type: q.question_type || 'text',
    is_required: q.is_required || false,
    scoring_weightings: q.scoring_weightings || 10.0,
    question_category: q.question_category || 'Contract',
    options: q.options || [],
    help_text: q.help_text || '',
    metric_name: q.metric_name || null,
    allow_document_upload: q.allow_document_upload || false
  }))
}

const addNewRenewalClause = () => {
  const newClause = {
    clause_id: `clause_${Date.now()}`,
    clause_name: 'Renewal Terms',
    clause_type: 'renewal',
    clause_text: '',
    risk_level: 'low', // Default value
    legal_category: 'Contract Renewal',
    version_number: '1', // Default value
    is_standard: false,
    created_by: formData.value.contract_owner || '',
    notice_period_days: 30,
    auto_renew: false,
    renewal_terms: ''
  }
  contractClauses.value.push(newClause)
}

const addNewTerminationClause = () => {
  const newClause = {
    clause_id: `clause_${Date.now()}`,
    clause_name: 'Termination Terms',
    clause_type: 'termination',
    clause_text: '',
    risk_level: 'medium', // Default value
    legal_category: 'Contract Termination',
    version_number: '1', // Default value
    is_standard: false,
    created_by: formData.value.contract_owner || '',
    termination_notice_period: 30,
    early_termination_fee: 0,
    termination_conditions: ''
  }
  contractClauses.value.push(newClause)
}

// Watchers for term category changes and tab navigation
watch(
  () => contractTerms.value.map(t => t.term_category),
  (newCategories, oldCategories) => {
    if (!Array.isArray(newCategories)) return
    newCategories.forEach((category, index) => {
      const term = contractTerms.value[index]
      if (!term?.term_id) return

      const prevCategory = Array.isArray(oldCategories) ? oldCategories[index] : undefined
      if (prevCategory !== undefined && prevCategory !== category) {
        resetTemplatesForTerm(term.term_id)
      }

      if (category && !hasLoadedTemplatesForTerm(term.term_id)) {
        loadTemplatesForTerm(term)
      }
    })
    if (contractTerms.value.length > 0) {
      loadTermQuestionnaires()
    }
  },
  { deep: true }
)

watch(activeTab, (newTab) => {
  if (newTab === 'terms' && contractTerms.value.length > 0) {
    loadTermQuestionnaires()
    contractTerms.value.forEach(term => {
      if (term.term_category && term.term_id && !hasLoadedTemplatesForTerm(term.term_id)) {
        loadTemplatesForTerm(term)
      }
    })
  }
})

// Methods for saving contract terms and clauses
const saveContractTerms = async (contractId) => {
  try {
    console.log('🔍 Saving contract terms for contract ID:', contractId)
    
    if (!contractTerms.value || !Array.isArray(contractTerms.value)) {
      console.log('⚠️ No contract terms to save or contractTerms is not an array')
      return
    }
    
    console.log('🔍 Number of terms to save:', contractTerms.value.length)
    console.log('🔍 Full contractTerms array:', JSON.stringify(contractTerms.value, null, 2))
    
    for (const [index, term] of contractTerms.value.entries()) {
      try {
        if (!term) {
          console.warn(`⚠️ Term ${index + 1} is undefined, skipping`)
          continue
        }
        
        console.log(`🔍 Processing term ${index + 1}:`, {
          term_id: term.term_id || 'undefined',
          term_category: term.term_category || '',
          term_title: term.term_title || '',
          term_text: term.term_text || '',
          term_text_length: term.term_text ? term.term_text.length : 0,
          term_text_type: typeof term.term_text,
          risk_level: term.risk_level || 'Low',
          compliance_status: term.compliance_status || 'Pending'
        })
      
        const termData = {
          term_id: term.term_id || `term_${Date.now()}_${index}`,
          term_category: term.term_category || '',
          term_title: term.term_title || '',
          term_text: term.term_text || '',
          risk_level: 'Low', // Default value
          compliance_status: 'Pending', // Default value
          is_standard: Boolean(term.is_standard), // Ensure proper boolean for Django
          approval_status: 'Pending', // Default value
          version_number: '1.0', // Default value
          parent_term_id: term.parent_term_id || ''
        }
        const questionnaires = await getQuestionnairesForTerm(term.term_id, term.term_category, term.term_title)
        if (questionnaires.length > 0) {
          termData.questionnaires = questionnaires
        }
        
        // Validate term_text before sending
        if (!termData.term_text || termData.term_text.trim() === '') {
          console.error('❌ Term text is empty for term:', termData.term_id)
          throw new Error(`Term text is required for term: ${termData.term_title || termData.term_id}`)
        }
        
        console.log('📤 Sending term data to API:', termData)
        console.log('🔍 Term is_standard value:', termData.is_standard, 'Type:', typeof termData.is_standard)
        
        await contractsApi.createContractTerms(contractId, termData)
        console.log('✅ Term saved successfully:', termData.term_id)
      } catch (error) {
        console.error('❌ Error saving contract term:', error)
        throw error
      }
    }
  } catch (error) {
    console.error('❌ Error in saveContractTerms:', error)
    throw error
  }
}

const saveContractClauses = async (contractId) => {
  try {
    console.log('🔍 Saving contract clauses for contract ID:', contractId)
    
    if (!contractClauses.value || !Array.isArray(contractClauses.value)) {
      console.log('⚠️ No contract clauses to save or contractClauses is not an array')
      return
    }
    
    console.log('🔍 Number of clauses to save:', contractClauses.value.length)
    console.log('🔍 Full contractClauses array:', JSON.stringify(contractClauses.value, null, 2))
    
    for (const [index, clause] of contractClauses.value.entries()) {
      try {
        if (!clause) {
          console.warn(`⚠️ Clause ${index + 1} is undefined, skipping`)
          continue
        }
        
        console.log(`🔍 Processing clause ${index + 1}:`, {
          clause_id: clause.clause_id || 'undefined',
          clause_name: clause.clause_name || '',
          clause_text: clause.clause_text || '',
          clause_text_length: clause.clause_text ? clause.clause_text.length : 0,
          clause_text_type: typeof clause.clause_text,
          clause_name_empty: !clause.clause_name || clause.clause_name.trim() === '',
          clause_text_empty: !clause.clause_text || clause.clause_text.trim() === ''
        })
        
        const clauseData = {
          clause_id: clause.clause_id || `clause_${Date.now()}`,
          clause_name: clause.clause_name || '',
          clause_type: clause.clause_type || 'standard',
          clause_text: clause.clause_text || '',
          risk_level: 'low', // Default value
          legal_category: clause.legal_category || '',
          version_number: '1', // Default value
          is_standard: Boolean(clause.is_standard), // Ensure proper boolean for Django
          notice_period_days: clause.notice_period_days || null,
          auto_renew: Boolean(clause.auto_renew), // Ensure proper boolean for Django
          renewal_terms: clause.renewal_terms || '',
          termination_notice_period: clause.termination_notice_period || null,
          early_termination_fee: clause.early_termination_fee || null,
          termination_conditions: clause.termination_conditions || ''
        }
        
        // Validate clause_name and clause_text before sending
        if (!clauseData.clause_name || clauseData.clause_name.trim() === '') {
          console.error('❌ Clause name is empty for clause:', clauseData.clause_id)
          throw new Error(`Clause name is required for clause: ${clauseData.clause_id}`)
        }
        
        if (!clauseData.clause_text || clauseData.clause_text.trim() === '') {
          console.error('❌ Clause text is empty for clause:', clauseData.clause_id)
          throw new Error(`Clause text is required for clause: ${clauseData.clause_name || clauseData.clause_id}`)
        }
        
        console.log('📤 Sending clause data to API:', clauseData)
        console.log('🔍 Clause is_standard value:', clauseData.is_standard, 'Type:', typeof clauseData.is_standard)
        console.log('🔍 Clause auto_renew value:', clauseData.auto_renew, 'Type:', typeof clauseData.auto_renew)
        
        await contractsApi.createContractClauses(contractId, clauseData)
        console.log('✅ Clause saved successfully:', clauseData.clause_id)
      } catch (error) {
        console.error('❌ Error saving contract clause:', error)
        throw error
      }
    }
  } catch (error) {
    console.error('❌ Error in saveContractClauses:', error)
    throw error
  }
}

// Main contract data for preview
const mainContractData = ref(null)

// Load main contract data to populate vendor and stakeholder information
const loadMainContractData = async () => {
  // Get the parent contract ID from multiple sources
  const parentContractId = route.query.parent_contract_id || route.params.id || formData.value.parent_contract_id
  
  console.log('🔍 Loading main contract data:')
  console.log('  - route.params.id:', route.params.id)
  console.log('  - route.query.parent_contract_id:', route.query.parent_contract_id)
  console.log('  - formData.parent_contract_id:', formData.value.parent_contract_id)
  console.log('  - Using parentContractId:', parentContractId)
  
  if (parentContractId) {
    try {
      // Use the imported API service
      
      // Fetch main contract data using the correct parent contract ID
      const response = await contractsApi.getContract(parentContractId)
      const mainContract = response.data
      
      // Store main contract data for preview
      mainContractData.value = mainContract
      
      // Populate vendor information from main contract
      if (mainContract.vendor) {
        formData.value.vendor_name = mainContract.vendor.vendor_name || ''
        formData.value.vendor_id = parseInt(mainContract.vendor.vendor_id) || null
      }
      
      // Populate stakeholder information from main contract
      formData.value.contract_owner = parseInt(mainContract.contract_owner) || null
      formData.value.legal_reviewer = parseInt(mainContract.legal_reviewer) || null
      formData.value.assigned_to = parseInt(mainContract.assigned_to) || null
      
      // Populate other relevant fields
      formData.value.currency = mainContract.currency || 'USD'
      formData.value.contract_category = mainContract.contract_category || 'services'
      formData.value.termination_clause = mainContract.termination_clause_type || 'convenience'
      formData.value.dispute_resolution = mainContract.dispute_resolution_method || ''
      formData.value.governing_law = mainContract.governing_law || ''
      formData.value.contract_risk_score = mainContract.contract_risk_score || ''
      
      // Populate JSON fields from main contract
      formData.value.insurance_requirements = mainContract.insurance_requirements || {}
      formData.value.data_protection_clauses = mainContract.data_protection_clauses || {}
      formData.value.custom_fields = mainContract.custom_fields || {}
      
      console.log('✅ Main contract data loaded and populated')
      console.log('🔍 JSON fields from main contract:', {
        insurance_requirements: formData.value.insurance_requirements,
        data_protection_clauses: formData.value.data_protection_clauses,
        custom_fields: formData.value.custom_fields
      })
      } catch (error) {
      console.error('Error loading main contract data:', error)
    }
  }
}

// Load main contract data for preview
const loadMainContractForPreview = async () => {
  // Get the parent contract ID from multiple sources
  const parentContractId = route.query.parent_contract_id || route.params.id || formData.value.parent_contract_id
  
  if (parentContractId) {
    try {
      // Use the imported API service
      
      // Fetch main contract data using the correct parent contract ID
      const response = await contractsApi.getContract(parentContractId)
      mainContractData.value = response.data
      
      console.log('✅ Main contract data loaded for preview')
      } catch (error) {
      console.error('Error loading main contract data for preview:', error)
      }
  }
}

// Check for OCR data from OCR page and restore from preview
onMounted(async () => {
  console.log('🚀 CreateSubcontract onMounted - Contract ID:', id)
  console.log('🚀 CreateSubcontract onMounted - Route query:', route.query)
  
  // Set the parent contract ID properly from route parameters or query
  const parentContractId = route.query.parent_contract_id || route.params.id
  if (parentContractId && !formData.value.parent_contract_id) {
    formData.value.parent_contract_id = parentContractId
    console.log('🔧 Set parent_contract_id from route:', parentContractId)
  }
  
  // Fetch vendors list for dropdown
  await fetchVendors()
  
  // Load main contract data first
  await loadMainContractData()
  
  // Fetch users and legal reviewers for stakeholders tab
  try {
    console.log('📋 Fetching users and legal reviewers...')

    // Fetch all data in parallel for better performance
    const [usersResponse, legalReviewersResponse] = await Promise.all([
      contractsApi.getUsers(),
      contractsApi.getLegalReviewers()
    ])

    if (usersResponse.success) {
      users.value = usersResponse.data
      console.log('✅ Users loaded:', users.value.length, 'users')
    } else {
      console.warn('⚠️ Failed to load users:', usersResponse.message)
      users.value = []
    }

    if (legalReviewersResponse.success) {
      legalReviewers.value = legalReviewersResponse.data
      console.log('✅ Legal reviewers loaded:', legalReviewers.value.length, 'reviewers')
    } else {
      console.warn('⚠️ Failed to load legal reviewers:', legalReviewersResponse.message)
      legalReviewers.value = []
    }
  } catch (error) {
    console.error('❌ Error fetching users/legal reviewers:', error)
    users.value = []
    legalReviewers.value = []
  }
  
  // Check if we're returning from preview page and restore form data
  // Only restore if we're explicitly returning from preview (not creating a new subcontract)
  const draftDataRaw = sessionStorage.getItem('subcontract_advanced_draft')
  if (draftDataRaw) {
    try {
      const draftData = JSON.parse(draftDataRaw)
      if (draftData.formData) {
        formData.value = { ...formData.value, ...draftData.formData }
      }
      if (Array.isArray(draftData.contractTerms)) {
        contractTerms.value = draftData.contractTerms.map(term => reactive({ ...term }))
      }
      if (Array.isArray(draftData.contractClauses)) {
        contractClauses.value = draftData.contractClauses.map(clause => reactive({ ...clause }))
      }
      if (draftData.selectedTemplates) {
        selectedTemplates.value = { ...draftData.selectedTemplates }
      }

      await nextTick()
      contractTerms.value = [...contractTerms.value]
      contractClauses.value = [...contractClauses.value]
      sessionStorage.removeItem('subcontract_advanced_draft')

      if (contractTerms.value.length > 0) {
        loadTermQuestionnaires()
        contractTerms.value.forEach(term => {
          if (term.term_category && term.term_id) {
            loadTemplatesForTerm(term)
          }
        })
      }
    } catch (error) {
      console.error('Error restoring subcontract draft data:', error)
    }
  }

  const previewData = sessionStorage.getItem('subcontractPreviewData')
  const isReturningFromPreview = route.query.returnFromPreview === 'true' || route.query.restore === 'true'
  
  console.log('🔍 Preview data exists:', !!previewData)
  console.log('🔍 Is returning from preview:', isReturningFromPreview)
  console.log('🔍 Route query:', route.query)
  
  if (previewData && isReturningFromPreview) {
    try {
      const parsedData = JSON.parse(previewData)
      console.log('🔄 Restoring subcontract form data from preview:', parsedData)
      
      // Restore form data
      if (parsedData.formData) {
        console.log('🔍 Original form data before restoration:', formData.value)
        console.log('🔍 Preview data to restore:', parsedData.formData)
        
        // Restore each field individually to ensure reactivity
        const subcontractData = parsedData.formData
        Object.keys(subcontractData).forEach(key => {
          if (subcontractData[key] !== undefined && subcontractData[key] !== null) {
            formData.value[key] = subcontractData[key]
            console.log(`✅ Restored ${key}:`, subcontractData[key])
          }
        })
        
        console.log('✅ Form data restored:', formData.value)
        
        // Force reactivity update by creating a completely new reactive object
        const newFormData = { ...formData.value }
        formData.value = newFormData
        console.log('🔄 Form data after reactivity update:', formData.value)
        
        // Force a DOM update by using nextTick
        await nextTick()
        console.log('🔄 DOM should be updated now')
        
        // Force form re-render by updating the key
        formKey.value++
        console.log('🔄 Form key updated to force re-render:', formKey.value)
        
        // Force update all form fields by triggering input events
        setTimeout(() => {
          // List of all form field IDs that need to be updated
          const formFields = [
            'title', 'contract_number', 'value', 'liability_cap', 'start_date', 'end_date',
            'notice_period_days', 'governing_law', 'description'
          ]
          
          // Update each form field
          formFields.forEach(fieldId => {
            const input = document.getElementById(fieldId)
            if (input && formData.value[fieldId] !== undefined && formData.value[fieldId] !== null) {
              input.value = formData.value[fieldId] || ''
              input.dispatchEvent(new Event('input', { bubbles: true }))
              console.log(`🔧 Manually set ${fieldId} input value:`, input.value)
            }
          })
          
          // Update textarea fields
          const textareaFields = ['description', 'renewal_terms']
          textareaFields.forEach(fieldId => {
            const textarea = document.getElementById(fieldId)
            if (textarea && formData.value[fieldId] !== undefined && formData.value[fieldId] !== null) {
              textarea.value = formData.value[fieldId] || ''
              textarea.dispatchEvent(new Event('input', { bubbles: true }))
              console.log(`🔧 Manually set ${fieldId} textarea value:`, textarea.value)
            }
          })
          
          console.log('🔍 Form field values after restoration:')
          console.log('  - title:', formData.value.title)
          console.log('  - contract_number:', formData.value.contract_number)
          console.log('  - value:', formData.value.value)
          console.log('  - start_date:', formData.value.start_date)
          console.log('  - end_date:', formData.value.end_date)
        }, 200)
      }
      
      // Restore contract terms - ensure each term is reactive
      if (parsedData.contractTerms && Array.isArray(parsedData.contractTerms)) {
        contractTerms.value = parsedData.contractTerms.map(term => reactive({ ...term })) // Make each term reactive
        console.log('✅ Contract terms restored:', contractTerms.value)
        console.log('✅ Contract terms count:', contractTerms.value.length)
        console.log('✅ First term details:', contractTerms.value[0])
        } else {
        console.log('⚠️ No contract terms found in preview data')
      }
      
      // Restore contract clauses - ensure each clause is reactive
      if (parsedData.contractClauses && Array.isArray(parsedData.contractClauses)) {
        contractClauses.value = parsedData.contractClauses.map(clause => reactive({ ...clause })) // Make each clause reactive
        console.log('✅ Contract clauses restored:', contractClauses.value)
        console.log('✅ Contract clauses count:', contractClauses.value.length)
        console.log('✅ First clause details:', contractClauses.value[0])
      } else {
        console.log('⚠️ No contract clauses found in preview data')
      }
      
      if (parsedData.selectedTemplates) {
        selectedTemplates.value = { ...parsedData.selectedTemplates }
      }
      
      // Force reactivity update for terms and clauses
      contractTerms.value = [...contractTerms.value]
      contractClauses.value = [...contractClauses.value]
      
      // Force form re-render to ensure terms and clauses are displayed
      formKey.value++
      console.log('🔄 Form key updated after terms/clauses restoration:', formKey.value)
      
      // Ensure the form is properly rendered by waiting for next tick
        await nextTick()
      console.log('🔄 DOM updated after terms/clauses restoration')
      
      // Additional debugging to verify the data is properly set
      console.log('🔍 After restoration - contractTerms.value:', contractTerms.value)
      console.log('🔍 After restoration - contractClauses.value:', contractClauses.value)
      console.log('🔍 After restoration - contractTerms.length:', contractTerms.value.length)
      console.log('🔍 After restoration - contractClauses.length:', contractClauses.value.length)
      
      // Force another reactivity update after nextTick
        setTimeout(() => {
        contractTerms.value = [...contractTerms.value]
        contractClauses.value = [...contractClauses.value]
        console.log('🔄 Final reactivity update completed')
        }, 100)
      
      // Clear the preview data from session storage
      sessionStorage.removeItem('subcontractPreviewData')
      
      console.log('✅ All subcontract form data restored successfully')
      console.log('🔍 Final contractTerms length:', contractTerms.value.length)
      console.log('🔍 Final contractClauses length:', contractClauses.value.length)
    } catch (error) {
      console.error('Error restoring subcontract form data from preview:', error)
    }
  } else if (previewData && !isReturningFromPreview) {
    // Clear stale preview data when creating a new subcontract
    console.log('🧹 Clearing stale preview data - creating new subcontract')
    sessionStorage.removeItem('subcontractPreviewData')
    
    // Reset form to clean state
    console.log('🔄 Resetting form to clean state for new subcontract')
    
    // Reset form data to defaults (keep only essential fields from parent contract)
    const cleanFormData = {
      title: '',
      contract_number: '',
      vendor_id: formData.value.vendor_id, // Keep vendor from parent
      vendor_name: formData.value.vendor_name, // Keep vendor from parent
      type: '',
      value: '',
      currency: formData.value.currency || 'USD', // Keep currency from parent
      start_date: '',
      end_date: '',
      contract_owner: formData.value.contract_owner, // Keep contract_owner from parent
      legal_reviewer: formData.value.legal_reviewer, // Keep legal reviewer from parent
      auto_renew: false,
      notice_period_days: 30,
      risk_level: '',
      compliance_frameworks: [],
      description: '',
      parent_contract_id: parentContractId || '',
      contract_category: '',
      business_owner: '',
      procurement_contact: '',
      auto_renewal_flag: false,
      renewal_notice_period: 30,
      termination_clause: '',
      liability_cap: '',
      insurance_requirements: {},
      data_protection_clauses: {},
      dispute_resolution: '',
      governing_law: '',
      esignature_required: false,
      contract_risk_score: '',
      workflow_stage: 'under_review',
      priority: 'medium',
      assigned_to: '',
      custom_fields: {},
      compliance_status: 'under_review',
      renewal_terms: '',
      auto_renewal: false,
      status: 'PENDING_ASSIGNMENT'
    }
    
    formData.value = cleanFormData
    contractTerms.value = []
    contractClauses.value = []
    selectedTemplates.value = {}
    
    // Force form re-render
    formKey.value++
    
    console.log('✅ Form reset to clean state for new subcontract')
  }
  
  // Check for OCR data from OCR page
  const ocrData = localStorage.getItem('ocrContractData')
  if (ocrData) {
    try {
      const parsedData = JSON.parse(ocrData)
      
      // Set form data
      formData.value = { ...formData.value, ...parsedData }
      
      // Set contract terms if available
      if (parsedData.contractTerms && parsedData.contractTerms.length > 0) {
        contractTerms.value = parsedData.contractTerms.map(term => reactive({ ...term }))
      }
      
      // Set contract clauses if available
      if (parsedData.contractClauses && parsedData.contractClauses.length > 0) {
        contractClauses.value = parsedData.contractClauses.map(clause => reactive({ ...clause }))
      }
      
      // Clear the OCR data from localStorage
      localStorage.removeItem('ocrContractData')
      
      // Show success message
      PopupService.success('Subcontract fields, terms, and clauses have been populated with extracted data from OCR.', 'OCR Data Applied')
    } catch (error) {
      console.error('Error parsing OCR data:', error)
    }
  } else {
    // If no OCR data and not returning from preview, ensure we have a clean form
    console.log('🔍 No OCR data found - ensuring clean form state')
  }
})
</script>
