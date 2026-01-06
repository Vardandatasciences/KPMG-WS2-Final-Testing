<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button @click="navigate(`/contracts/${contractId}/edit-advanced`)" class="p-2 hover:bg-muted rounded-md">
          <ArrowLeft class="w-4 h-4" />
        </button>
        <div>
          <h1 class="text-3xl font-bold text-foreground">Create Contract Amendment</h1>
          <p class="text-muted-foreground">Create a new amendment for contract #{{ contractId }}</p>
          <p class="text-sm text-blue-600 mt-1">Form is pre-populated with existing contract data</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button @click="navigate(`/contracts/${contractId}/edit-advanced`)" class="inline-flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-muted">
          <ArrowLeft class="w-4 h-4" />
          Back to Contract
        </button>
      </div>
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
      <div class="flex items-center justify-between">
      <div class="flex items-center gap-2 text-green-800">
        <CheckCircle class="w-5 h-5" />
        <span>{{ successMessage }}</span>
        </div>
        <button 
          @click="showComparisonDialog = true" 
          class="inline-flex items-center gap-2 px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
        >
          <Search class="w-4 h-4" />
          View Changes
        </button>
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
        <CheckCircle class="w-5 h-5" />
        <span class="text-sm">Risk analysis has been triggered and will run in the background.</span>
        <button @click="showRiskAnalysisTriggered = false" class="ml-auto p-1 hover:bg-green-100 rounded">
          <X class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
      <h3 class="mt-2 text-sm font-semibold text-foreground">Loading contract data...</h3>
      <p class="mt-1 text-sm text-muted-foreground">Pre-populating form with existing contract information</p>
    </div>

      <!-- Main Content -->
    <div v-else>
      <!-- OCR Upload Section -->
      <div class="border rounded-lg bg-card p-6">
        <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <Upload class="w-5 h-5" />
          OCR Document Upload & Processing
        </h3>
        
        <!-- OCR Error Message -->
        <div v-if="errors.ocr" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div class="flex items-center gap-2 text-red-800">
            <AlertTriangle class="w-5 h-5" />
            <span>{{ errors.ocr }}</span>
          </div>
        </div>
        
        <!-- Upload Step -->
        <div v-if="uploadStep === 'upload'" 
          @dragover="handleDragOver" 
          @dragenter="handleDragEnter"
          @dragleave="handleDragLeave"
          @drop="handleFileDrop"
          class="border-2 border-dashed rounded-lg p-8 text-center transition-colors"
          :class="isDragOver ? 'border-blue-500 bg-blue-50' : 'border-muted-foreground/25'"
        >
          <FileText class="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 class="text-lg font-semibold mb-2">Upload Amendment Document</h3>
          <p class="text-muted-foreground mb-4">Drag and drop or click to upload PDF, PNG, JPG, or TIFF files (max 10MB)</p>
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

        <!-- Processing Step -->
        <div v-if="uploadStep === 'processing'" class="space-y-4">
          <div class="flex items-center justify-center py-8">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
          <div class="text-center">
            <h3 class="text-lg font-semibold mb-2">Processing Document...</h3>
            <p class="text-muted-foreground mb-4">Extracting amendment data using OCR</p>
            <div class="w-full bg-muted rounded-full h-2">
              <div class="bg-primary h-2 rounded-full transition-all duration-300" :style="{ width: `${uploadProgress}%` }"></div>
            </div>
            <p class="text-sm text-muted-foreground mt-2">{{ uploadProgress }}%</p>
          </div>
        </div>

        <!-- Review Step -->
        <div v-if="uploadStep === 'review'" class="space-y-4">
          <!-- S3 Upload Status -->
          <div v-if="s3UploadInfo" class="p-4 border rounded-lg" :class="s3UploadInfo.success ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'">
            <div class="flex items-center gap-2">
              <CheckCircle v-if="s3UploadInfo.success" class="w-5 h-5 text-green-600" />
              <AlertTriangle v-else class="w-5 h-5 text-yellow-600" />
              <div>
                <h4 class="font-medium" :class="s3UploadInfo.success ? 'text-green-800' : 'text-yellow-800'">
                  {{ s3UploadInfo.success ? 'Document Uploaded Successfully' : 'Document Uploaded (S3 Storage Unavailable)' }}
                </h4>
                <p class="text-sm" :class="s3UploadInfo.success ? 'text-green-700' : 'text-yellow-700'">
                  {{ s3UploadInfo.success ? `File stored in S3: ${s3UploadInfo.file_info?.key || 'Unknown'}` : 'Document processed but not stored in S3. Extracted data is available.' }}
                </p>
              </div>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <h4 class="font-semibold">OCR Processing Complete</h4>
              <p class="text-sm text-muted-foreground">{{ ocrResults.length }} fields extracted from the document</p>
            </div>
            <button @click="resetUpload" class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted">
              <Upload class="w-4 h-4" />
              Upload Different File
            </button>
          </div>
        </div>
        
        <!-- OCR Review Section -->
        <div v-if="ocrResults.length > 0" class="mt-6 border-t pt-6">
          <h4 class="text-md font-semibold mb-4 flex items-center gap-2">
            <Eye class="w-4 h-4" />
            OCR Results Review
          </h4>
          <p class="text-sm text-muted-foreground mb-4">Review the extracted data and apply it to the form fields below.</p>
          
          <div class="space-y-3 max-h-96 overflow-y-auto">
            <div v-for="(result, index) in ocrResults" :key="index" class="border rounded-lg p-3">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-sm font-medium text-blue-600">{{ result.field }}</span>
                    <span class="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                      {{ result.confidence }}% confidence
                    </span>
                  </div>
                  
                  <!-- Different input types based on field -->
                  <input 
                    v-if="result.type === 'number'"
                    :value="result.value"
                    @input="updateOCRResult(index, $event.target.value)"
                    type="number"
                    class="w-full px-2 py-1 border border-input rounded text-sm"
                    :step="result.step || '0.01'"
                  />
                  <input 
                    v-else-if="result.type === 'date'"
                    :value="result.value"
                    @input="updateOCRResult(index, $event.target.value)"
                    type="date"
                    class="w-full px-2 py-1 border border-input rounded text-sm"
                  />
                  <select 
                    v-else-if="result.type === 'select'"
                    :value="result.value"
                    @change="updateOCRResult(index, $event.target.value)"
                    class="w-full px-2 py-1 border border-input rounded text-sm"
                  >
                    <option v-for="option in result.options" :key="option" :value="option">
                      {{ option }}
                    </option>
                  </select>
                  <textarea 
                    v-else-if="result.type === 'textarea'"
                    :value="result.value"
                    @input="updateOCRResult(index, $event.target.value)"
                    class="w-full px-2 py-1 border border-input rounded text-sm"
                    rows="2"
                  ></textarea>
                  <input 
                    v-else
                    :value="result.value"
                    @input="updateOCRResult(index, $event.target.value)"
                    type="text"
                    class="w-full px-2 py-1 border border-input rounded text-sm"
                  />
                  
                  <div v-if="result.needsReview" class="mt-1">
                    <span class="text-xs text-orange-600">⚠️ Needs manual review</span>
                  </div>
                </div>
                <div class="ml-2">
                  <button 
                    @click="removeOCRResult(index)"
                    class="text-red-500 hover:text-red-700 text-sm"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Apply to Form Buttons -->
          <div class="mt-4 flex gap-2">
            <button 
              @click="applyOCRData"
              class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <CheckCircle class="w-4 h-4" />
              Apply to Form
            </button>
            <button 
              @click="applyOCRDataWithClear"
              class="inline-flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700"
            >
              <AlertTriangle class="w-4 h-4" />
              Clear & Apply
            </button>
            <button 
              @click="clearOCRResults"
              class="inline-flex items-center gap-2 px-4 py-2 border border-input rounded-md hover:bg-muted"
            >
              <Trash2 class="w-4 h-4" />
              Clear Results
            </button>
          </div>
        </div>
          </div>

    <!-- Amendment Form Tabs -->
    <Tabs v-model="activeTab" class="space-y-6">
      <TabsList class="grid w-full grid-cols-10">
        <TabsTrigger value="basic">Primary Info</TabsTrigger>
        <TabsTrigger value="financial">Financial</TabsTrigger>
        <TabsTrigger value="dates">Dates & Terms</TabsTrigger>
        <TabsTrigger value="stakeholders">Stakeholders</TabsTrigger>
        <TabsTrigger value="terms">Contract Terms</TabsTrigger>
        <TabsTrigger value="clauses">Clauses</TabsTrigger>
        <TabsTrigger value="renewal">Renewal</TabsTrigger>
        <TabsTrigger value="termination">Termination</TabsTrigger>
        <TabsTrigger value="compliance">Compliance</TabsTrigger>
        <TabsTrigger value="legal">Legal</TabsTrigger>
      </TabsList>

      <!-- Basic Information Tab -->
      <TabsContent value="basic" class="space-y-6">
        <!-- Amendment Details -->
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4">Amendment Details</h4>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
              <label class="text-sm font-medium">Amendment Number *</label>
              <input v-model="amendmentForm.amendment_number" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="e.g., AMEND-001" />
              </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Amendment Date *</label>
              <input v-model="amendmentForm.amendment_date" type="date" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Effective Date *</label>
              <input v-model="amendmentForm.effective_date" type="date" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Amendment Type</label>
              <select v-model="amendmentForm.amendment_type" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select type</option>
                <option value="financial">Financial</option>
                <option value="scope">Scope Change</option>
                <option value="timeline">Timeline</option>
                <option value="terms">Terms & Conditions</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div class="space-y-2 mt-4">
            <label class="text-sm font-medium">Amendment Reason *</label>
            <textarea v-model="amendmentForm.amendment_reason" rows="3" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="Describe the reason for this amendment..."></textarea>
          </div>
          <div class="space-y-2 mt-4">
            <label class="text-sm font-medium">Changes Summary *</label>
            <textarea v-model="amendmentForm.changes_summary" rows="3" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="Summarize the key changes..."></textarea>
          </div>
        </div>

        <!-- Primary Contract Information -->
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4">Primary Contract Information</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">Contract Title *</label>
              <input v-model="formData.contract_title" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="e.g., Cloud Infrastructure Services Agreement" />
            </div>
              <div class="space-y-2">
              <label class="text-sm font-medium">Contract Number</label>
              <input v-model="formData.contract_number" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="e.g., CNT-2024-001" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Contract Type *</label>
              <select v-model="formData.contract_type" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select contract type</option>
                <option value="MASTER_AGREEMENT">Master Agreement</option>
                <option value="SOW">Statement of Work</option>
                <option value="PURCHASE_ORDER">Purchase Order</option>
                <option value="SERVICE_AGREEMENT">Service Agreement</option>
                <option value="LICENSE">License</option>
                <option value="NDA">Non-Disclosure Agreement</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Priority *</label>
              <select v-model="formData.priority" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select priority</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Contract Category</label>
              <select v-model="formData.contract_category" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select category</option>
                <option value="goods">Goods</option>
                <option value="services">Services</option>
                <option value="technology">Technology</option>
                <option value="consulting">Consulting</option>
                <option value="others">Others</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Vendor Information -->
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4">Vendor Information</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">Vendor *</label>
              <select v-model="formData.vendor_id" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select vendor</option>
                <option v-for="vendor in vendors" :key="vendor.vendor_id" :value="vendor.vendor_id">
                  {{ vendor.company_name }}
                </option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Selected Vendor</label>
              <input :value="formData.vendor_name" class="w-full px-3 py-2 border border-input rounded-md bg-muted text-foreground" readonly />
            </div>
          </div>
        </div>
      </TabsContent>

      <!-- Financial Tab -->
      <TabsContent value="financial" class="space-y-6">
        <!-- Financial Impact -->
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4">Amendment Financial Impact</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">Financial Impact</label>
              <input v-model="amendmentForm.financial_impact" type="number" step="0.01" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="0.00" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Impact Type</label>
              <select v-model="amendmentForm.impact_type" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select impact type</option>
                <option value="increase">Increase</option>
                <option value="decrease">Decrease</option>
                <option value="no_change">No Change</option>
              </select>
          </div>
        </div>
      </div>

        <!-- Contract Financial Details -->
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4">Contract Financial Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">Contract Value *</label>
              <input v-model="formData.contract_value" type="number" step="0.01" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="250000" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Currency</label>
              <select v-model="formData.currency" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="USD">USD - US Dollar</option>
                <option value="EUR">EUR - Euro</option>
                <option value="GBP">GBP - British Pound</option>
                <option value="CAD">CAD - Canadian Dollar</option>
                <option value="AUD">AUD - Australian Dollar</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Liability Cap</label>
              <input v-model="formData.liability_cap" type="number" step="0.01" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="e.g., 1000000" />
            </div>
          </div>
        </div>
      </TabsContent>

      <!-- Dates & Terms Tab -->
      <TabsContent value="dates" class="space-y-6">
        <!-- Contract Dates -->
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4">Contract Dates & Terms</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">Start Date *</label>
              <input v-model="formData.start_date" type="date" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">End Date *</label>
              <input v-model="formData.end_date" type="date" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Notice Period (Days)</label>
              <input v-model="formData.notice_period_days" type="number" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="30" />
            </div>
          </div>
          <div class="flex items-center space-x-2 mt-4">
            <input type="checkbox" v-model="formData.auto_renewal" class="rounded" />
            <label class="text-sm font-medium">Enable automatic renewal</label>
          </div>
          <div class="space-y-2 mt-4">
            <label class="text-sm font-medium">Renewal Terms</label>
            <textarea v-model="formData.renewal_terms" rows="3" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="Enter detailed renewal terms and conditions..."></textarea>
          </div>
        </div>
      </TabsContent>

      <!-- Stakeholders Tab -->
      <TabsContent value="stakeholders" class="space-y-6">
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4">Stakeholders & Responsibilities</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">Contract Owner *</label>
              <select v-model="formData.contract_owner" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select contract owner</option>
                <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                  {{ user.display_name }} ({{ user.role }})
                </option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Legal Reviewer</label>
              <select v-model="formData.legal_reviewer" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select legal reviewer</option>
                <option v-for="reviewer in legalReviewers" :key="reviewer.user_id" :value="reviewer.user_id">
                  {{ reviewer.display_name }} ({{ reviewer.role }})
                </option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Assigned To</label>
              <select v-model="formData.assigned_to" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select assigned person</option>
                <option v-for="user in users" :key="user.user_id" :value="user.user_id">
                  {{ user.display_name }} ({{ user.role }})
                </option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Status</label>
              <select v-model="formData.status" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="DRAFT">Draft</option>
                <option value="ACTIVE">Active</option>
                <option value="UNDER_REVIEW">Under Review</option>
                <option value="EXPIRED">Expired</option>
              </select>
            </div>
          </div>
        </div>
      </TabsContent>

      <!-- Contract Terms Tab -->
      <TabsContent value="terms" class="space-y-6">
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4 flex items-center gap-2">
            <FileCheck class="w-5 h-5" />
            Contract Terms
          </h4>
          <p class="text-sm text-muted-foreground mb-4">Define and manage contract terms with risk assessment. You can delete existing terms or add new ones.</p>
          <div class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium">Terms List</h3>
              <div class="flex gap-2">
                <button 
                  @click="testApiCalls"
                  class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted"
                >
                  <Search class="w-4 h-4" />
                  Test API
                </button>
                <button 
                  @click="debugTerms"
                  class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted"
                >
                  <Search class="w-4 h-4" />
                  Debug Terms
                </button>
                <button 
                  @click="addNewTerm"
                  class="inline-flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                  <Plus class="w-4 h-4" />
                  Add Term
                </button>
              </div>
            </div>
            
            <div class="space-y-4">
              <div v-for="(term, index) in contractTerms" :key="term?.term_id || `term-${index}`" class="border rounded p-4">
                <div class="space-y-4">
                  <div class="flex items-center justify-between">
                    <h4 class="font-medium">Term #{{ index + 1 }}</h4>
                    <button
                      @click="removeTerm(index)"
                      class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted text-red-600"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
          </div>
                  
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                      <label class="text-sm font-medium">Term Category</label>
                      <select 
                        v-model="term.term_category"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      >
                        <option value="">Select category</option>
                        <option value="Payment">Payment</option>
                        <option value="Delivery">Delivery</option>
                        <option value="Performance">Performance</option>
                        <option value="Liability">Liability</option>
                        <option value="Termination">Termination</option>
                        <option value="Intellectual Property">Intellectual Property</option>
                        <option value="Confidentiality">Confidentiality</option>
                      </select>
                    </div>
                    
                    <div class="space-y-2">
                      <label class="text-sm font-medium">Term Title</label>
                <input
                        v-model="term.term_title"
                  class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        placeholder="e.g., Payment Schedule"
                />
              </div>

              <div class="space-y-2">
                      <label class="text-sm font-medium">Risk Level</label>
                      <select 
                        v-model="term.risk_level"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      >
                        <option value="">Select risk level</option>
                        <option value="Low">Low</option>
                        <option value="Medium">Medium</option>
                        <option value="High">High</option>
                        <option value="Urgent">Urgent</option>
                </select>
              </div>

                    <div class="space-y-2">
                      <label class="text-sm font-medium">Compliance Status</label>
                      <select 
                        v-model="term.compliance_status"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      >
                        <option value="">Select status</option>
                        <option value="Pending">Pending</option>
                        <option value="Compliant">Compliant</option>
                        <option value="Non-Compliant">Non-Compliant</option>
                        <option value="Under Review">Under Review</option>
                        <option value="pending_review">Pending Review</option>
                      </select>
            </div>

            <div class="space-y-2">
                      <label class="text-sm font-medium">Version Number</label>
                <input
                        v-model="term.version_number"
                class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        placeholder="1.0"
                />
            </div>

            <div class="space-y-2">
                      <label class="text-sm font-medium">Approval Status</label>
                      <select 
                        v-model="term.approval_status"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      >
                        <option value="">Select status</option>
                        <option value="Pending">Pending</option>
                        <option value="Approved">Approved</option>
                        <option value="Rejected">Rejected</option>
                        <option value="Under Review">Under Review</option>
                </select>
              </div>
            </div>

            <div class="space-y-2">
                    <label class="text-sm font-medium">Term Text</label>
              <textarea
                      v-model="term.term_text"
                class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      placeholder="Enter the detailed term text..."
                rows="3"
                    />
                  </div>

                  <div class="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      :id="`standard_${index}`"
                      :checked="term?.is_standard || false"
                      @change="(event) => {
                        if (term) {
                          term.is_standard = event.target.checked;
                        }
                      }"
                      class="rounded"
                    />
                    <label :for="`standard_${index}`" class="text-sm font-medium">Standard Term</label>
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
      </TabsContent>

      <!-- Clauses Tab -->
      <TabsContent value="clauses" class="space-y-6">
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4 flex items-center gap-2">
            <FileText class="w-5 h-5" />
            Contract Clauses Library
          </h4>
          <p class="text-sm text-muted-foreground mb-4">Manage standardized contract clauses. You can delete existing clauses or add new ones.</p>
          <div class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium">Clauses List</h3>
              <div class="flex gap-2">
                <button 
                  @click="testApiCalls"
                  class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted"
                >
                  <Search class="w-4 h-4" />
                  Test API
                </button>
                <button 
                  @click="debugClauses"
                  class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted"
                >
                  <Search class="w-4 h-4" />
                  Debug Clauses
                </button>
                <button 
                  @click="addNewClause"
                  class="inline-flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                  <Plus class="w-4 h-4" />
                  Add Clause
                </button>
              </div>
            </div>
            
            <div class="space-y-4">
              <div v-for="(clause, index) in contractClauses" :key="clause?.clause_id || `clause-${index}`" class="border rounded p-4">
                <div class="space-y-4">
                  <div class="flex items-center justify-between">
                    <h4 class="font-medium">Clause #{{ index + 1 }}</h4>
                    <button
                      @click="removeClause(clause.clause_id)"
                      class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted text-red-600"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
                      <label class="text-sm font-medium">Clause Name *</label>
                      <input
                        v-model="clause.clause_name"
                class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        placeholder="e.g., Limitation of Liability"
                      />
            </div>

              <div class="space-y-2">
                      <label class="text-sm font-medium">Clause Type</label>
                      <select 
                        v-model="clause.clause_type"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      >
                        <option value="">Select type</option>
                        <option value="standard">Standard</option>
                        <option value="risk">Risk</option>
                        <option value="compliance">Compliance</option>
                        <option value="financial">Financial</option>
                        <option value="operational">Operational</option>
                        <option value="other">Other</option>
                      </select>
                    </div>

                    <div class="space-y-2">
                      <label class="text-sm font-medium">Risk Level</label>
                      <select 
                        v-model="clause.risk_level"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      >
                        <option value="">Select risk level</option>
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                        <option value="urgent">Urgent</option>
                      </select>
                    </div>

                    <div class="space-y-2">
                      <label class="text-sm font-medium">Legal Category</label>
                <input
                        v-model="clause.legal_category"
                  class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        placeholder="e.g., Commercial Law"
                />
              </div>

              <div class="space-y-2">
                      <label class="text-sm font-medium">Version Number</label>
                <input
                        v-model="clause.version_number"
                  class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        placeholder="1.0"
                />
              </div>
            </div>

            <div class="space-y-2">
                    <label class="text-sm font-medium">Clause Text *</label>
              <textarea
                      v-model="clause.clause_text"
                class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      placeholder="Enter the detailed clause text..."
                      rows="4"
                    />
                  </div>

                  <div class="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      :id="`standard_clause_${index}`"
                      :checked="clause.is_standard"
                      @change="(event) => {
                        if (clause) {
                          clause.is_standard = event.target.checked;
                        }
                      }"
                      class="rounded"
                    />
                    <label :for="`standard_clause_${index}`" class="text-sm font-medium">Standard Clause</label>
            </div>
          </div>
        </div>

              <div v-if="contractClauses.length === 0" class="text-center py-8 text-muted-foreground">
                No contract clauses added yet. Click "Add Clause" to get started.
          </div>
            </div>
          </div>
        </div>
      </TabsContent>

      <!-- Compliance Tab -->
      <TabsContent value="compliance" class="space-y-6">
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4">Compliance & Frameworks</h4>
          <div class="space-y-3">
            <div class="space-y-2">
              <label class="text-sm font-medium">Compliance Framework</label>
              <select v-model="formData.compliance_framework" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select compliance framework</option>
                <option value="SOC2">SOC2</option>
                <option value="GDPR">GDPR</option>
                <option value="CCPA">CCPA</option>
                <option value="ISO27001">ISO27001</option>
                <option value="PCI DSS">PCI DSS</option>
                <option value="HIPAA">HIPAA</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
        </div>
      </TabsContent>

      <!-- Legal Tab -->
      <TabsContent value="legal" class="space-y-6">
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4">Legal & Risk Management</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium">Contract Risk Score</label>
              <input v-model="formData.contract_risk_score" type="number" step="0.01" min="0" max="10" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="0.00 - 10.00" />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Dispute Resolution</label>
              <select v-model="formData.dispute_resolution_method" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select resolution method</option>
                <option value="negotiation">Negotiation</option>
                <option value="mediation">Mediation</option>
                <option value="arbitration">Arbitration</option>
                <option value="litigation">Litigation</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Governing Law</label>
              <input v-model="formData.governing_law" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" placeholder="e.g., California, USA" />
          </div>
            <div class="space-y-2">
              <label class="text-sm font-medium">Termination Clause</label>
              <select v-model="formData.termination_clause_type" class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground">
                <option value="">Select termination type</option>
                <option value="convenience">Convenience</option>
                <option value="cause">For Cause</option>
                <option value="both">Both</option>
                <option value="none">None</option>
              </select>
            </div>
          </div>
        </div>
      </TabsContent>

      <!-- Renewal Tab -->
      <TabsContent value="renewal" class="space-y-6">
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4 flex items-center gap-2">
            <Calendar class="w-5 h-5" />
            Renewal Clauses
          </h4>
          <p class="text-sm text-muted-foreground mb-4">Define contract renewal terms and conditions</p>
          <div class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium">Renewal Clauses</h3>
              <button 
                @click="addNewRenewalClause"
                class="inline-flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              >
                <Plus class="w-4 h-4" />
                Add Renewal Clause
              </button>
            </div>
            
            <div class="space-y-4">
              <div v-for="(clause, index) in (contractClauses || []).filter(c => c?.clause_type === 'renewal')" :key="clause?.clause_id || `renewal-${index}`" class="border rounded p-4">
                <div class="space-y-4">
                  <div class="flex items-center justify-between">
                    <h4 class="font-medium">Renewal Clause #{{ index + 1 }}</h4>
                    <button
                      @click="removeClause(clause.clause_id)"
                      class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted text-red-600"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                      <label class="text-sm font-medium">Notice Period (Days)</label>
                <input
                        type="number"
                        v-model="clause.notice_period_days"
                class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        placeholder="30"
                />
            </div>

            <div class="space-y-2">
                      <label class="text-sm font-medium">Risk Level</label>
                      <select 
                        v-model="clause.risk_level"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      >
                        <option value="">Select risk level</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                        <option value="critical">Critical</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
          </div>

                  <div class="space-y-2">
                    <label class="text-sm font-medium">Renewal Terms</label>
                    <textarea
                      v-model="clause.renewal_terms"
                  class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      placeholder="Enter the detailed renewal terms..."
                      rows="4"
                />
              </div>

                  <div class="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      :id="`auto_renew_${clause.clause_id}`"
                      :checked="clause?.auto_renew || false"
                      @change="(event) => {
                        if (clause) {
                          clause.auto_renew = event.target.checked;
                        }
                      }"
                      class="rounded"
                    />
                    <label :for="`auto_renew_${clause.clause_id}`" class="text-sm font-medium">Enable Auto-Renewal</label>
            </div>
        </div>
      </div>

              <div v-if="!contractClauses || !Array.isArray(contractClauses) || contractClauses.filter(c => c?.clause_type === 'renewal').length === 0" class="text-center py-8 text-muted-foreground">
                No renewal clauses added yet. Click "Add Renewal Clause" to get started.
          </div>
            </div>
          </div>
        </div>
      </TabsContent>

      <!-- Termination Tab -->
      <TabsContent value="termination" class="space-y-6">
        <div class="border rounded-lg p-6">
          <h4 class="text-lg font-medium mb-4 flex items-center gap-2">
            <FileText class="w-5 h-5" />
            Termination Clauses
          </h4>
          <p class="text-sm text-muted-foreground mb-4">Define contract termination conditions and penalties</p>
          <div class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium">Termination Clauses</h3>
              <button 
                @click="addNewTerminationClause"
                class="inline-flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              >
                <Plus class="w-4 h-4" />
                Add Termination Clause
              </button>
            </div>
            
            <div class="space-y-4">
              <div v-for="(clause, index) in (contractClauses || []).filter(c => c?.clause_type === 'termination')" :key="clause?.clause_id || `termination-${index}`" class="border rounded p-4">
                <div class="space-y-4">
                  <div class="flex items-center justify-between">
                    <h4 class="font-medium">Termination Clause #{{ index + 1 }}</h4>
                    <button
                      @click="removeClause(clause.clause_id)"
                      class="inline-flex items-center gap-2 px-3 py-2 border border-input rounded-md hover:bg-muted text-red-600"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
                      <label class="text-sm font-medium">Notice Period (Days)</label>
                      <input
                        type="number"
                        v-model="clause.termination_notice_period"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        placeholder="30"
                      />
              </div>

            <div class="space-y-2">
                      <label class="text-sm font-medium">Early Termination Fee</label>
                      <input
                        type="number"
                        v-model="clause.early_termination_fee"
                class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                        placeholder="0"
                      />
              </div>

            <div class="space-y-2">
                      <label class="text-sm font-medium">Risk Level</label>
                      <select 
                        v-model="clause.risk_level"
                        class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      >
                        <option value="">Select risk level</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                        <option value="critical">Critical</option>
                <option value="urgent">Urgent</option>
              </select>
              </div>
          </div>

                  <div class="space-y-2">
                    <label class="text-sm font-medium">Termination Conditions</label>
                    <textarea
                      v-model="clause.termination_conditions"
                      class="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                      placeholder="Enter the detailed termination conditions..."
                      rows="4"
                    />
            </div>
          </div>
        </div>

              <div v-if="!contractClauses || !Array.isArray(contractClauses) || contractClauses.filter(c => c?.clause_type === 'termination').length === 0" class="text-center py-8 text-muted-foreground">
                No termination clauses added yet. Click "Add Termination Clause" to get started.
          </div>
            </div>
          </div>
        </div>
      </TabsContent>
    </Tabs>

      <!-- Action Buttons -->
      <div class="flex items-center gap-4 pt-6 border-t">
        <button @click="showVersionDialog = true" :disabled="saving" class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">
          {{ saving ? 'Creating...' : 'Create Amendment' }}
            </button>
        <button @click="navigate(`/contracts/${contractId}/edit-advanced`)" class="px-6 py-2 border rounded-md hover:bg-muted">
          Cancel
            </button>
      </div>
    </div>

    <!-- Version Selection Dialog -->
    <div v-if="showVersionDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-background rounded-lg p-6 w-full max-w-md mx-4">
        <div class="space-y-4">
          <div>
            <h3 class="text-lg font-semibold text-foreground">Select Version Type</h3>
            <p class="text-sm text-muted-foreground mt-1">Choose how you want to version this amendment</p>
          </div>

          <div class="space-y-3">
            <!-- Major Version Option -->
            <div 
              @click="selectedVersionType = 'major'" 
              :class="['border rounded-lg p-4 cursor-pointer transition-colors', selectedVersionType === 'major' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300']"
            >
              <div class="flex items-start space-x-3">
                <div class="flex-shrink-0 mt-1">
                  <div :class="['w-4 h-4 rounded-full border-2', selectedVersionType === 'major' ? 'border-blue-500 bg-blue-500' : 'border-gray-300']">
                    <div v-if="selectedVersionType === 'major'" class="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                  </div>
                </div>
                <div class="flex-1">
                  <h4 class="font-medium text-foreground">Major Version</h4>
                  <p class="text-sm text-muted-foreground">Significant changes (1.0 → 2.0, 2.0 → 3.0)</p>
                  <div class="mt-2 text-xs text-blue-600">
                    Current: v{{ currentVersion }} → New: v{{ getMajorVersion() }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Minor Version Option -->
            <div 
              @click="selectedVersionType = 'minor'" 
              :class="['border rounded-lg p-4 cursor-pointer transition-colors', selectedVersionType === 'minor' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300']"
            >
              <div class="flex items-start space-x-3">
                <div class="flex-shrink-0 mt-1">
                  <div :class="['w-4 h-4 rounded-full border-2', selectedVersionType === 'minor' ? 'border-blue-500 bg-blue-500' : 'border-gray-300']">
                    <div v-if="selectedVersionType === 'minor'" class="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                  </div>
                </div>
                <div class="flex-1">
                  <h4 class="font-medium text-foreground">Minor Version</h4>
                  <p class="text-sm text-muted-foreground">Small changes or updates (1.0 → 1.1, 2.0 → 2.1)</p>
                  <div class="mt-2 text-xs text-blue-600">
                    Current: v{{ currentVersion }} → New: v{{ getMinorVersion() }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="flex justify-end space-x-3 pt-4 border-t">
            <button 
              @click="showVersionDialog = false" 
              class="px-4 py-2 border rounded-md hover:bg-muted"
            >
              Cancel
            </button>
            <button 
              @click="createAmendment" 
              :disabled="!selectedVersionType || saving"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {{ saving ? 'Creating...' : 'Create Amendment' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Contract Comparison Dialog -->
    <div v-if="showComparisonDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-background rounded-lg w-full max-w-6xl mx-4 max-h-[90vh] overflow-hidden">
        <div class="flex flex-col h-full">
          <!-- Header -->
          <div class="flex items-center justify-between p-6 border-b">
            <div>
              <h3 class="text-lg font-semibold text-foreground">Contract Amendment Comparison</h3>
              <p class="text-sm text-muted-foreground mt-1">Compare original contract with the new amendment</p>
            </div>
            <button 
              @click="showComparisonDialog = false" 
              class="p-2 hover:bg-muted rounded-md"
            >
              <X class="w-5 h-5" />
            </button>
          </div>

          <!-- Comparison Content -->
          <div class="flex-1 overflow-y-auto p-6">
            <div class="space-y-6">
              <!-- Contract Basic Information Comparison -->
              <div class="border rounded-lg p-4">
                <h4 class="text-md font-semibold mb-4 flex items-center gap-2">
                  <FileText class="w-4 h-4" />
                  Contract Basic Information
                </h4>
                <div class="space-y-3">
                  <div v-for="field in contractComparisonFields" :key="field.key" class="grid grid-cols-3 gap-4 items-center">
                    <div class="text-sm font-medium text-muted-foreground">{{ field.label }}</div>
                    <div class="text-sm p-2 bg-red-50 border border-red-200 rounded">
                      <span class="font-medium text-red-800">Original:</span>
                      <div class="text-red-700">{{ getOriginalValue(field.key) || 'N/A' }}</div>
                    </div>
                    <div class="text-sm p-2 bg-green-50 border border-green-200 rounded">
                      <span class="font-medium text-green-800">Amendment:</span>
                      <div class="text-green-700">{{ getAmendmentValue(field.key) || 'N/A' }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Contract Terms Comparison -->
              <div class="border rounded-lg p-4">
                <h4 class="text-md font-semibold mb-4 flex items-center gap-2">
                  <FileCheck class="w-4 h-4" />
                  Contract Terms Changes
                </h4>
                <div class="space-y-4">
                  <!-- Terms Added -->
                  <div v-if="addedTerms.length > 0">
                    <h5 class="text-sm font-medium text-green-800 mb-2">➕ Terms Added ({{ addedTerms.length }})</h5>
                    <div class="space-y-2">
                      <div v-for="term in addedTerms" :key="term.term_id" class="p-3 bg-green-50 border border-green-200 rounded">
                        <div class="text-sm font-medium text-green-800">{{ term.term_title || 'Untitled Term' }}</div>
                        <div class="text-xs text-green-700 mt-1">{{ term.term_text }}</div>
                      </div>
                    </div>
                  </div>

                  <!-- Terms Modified -->
                  <div v-if="modifiedTerms.length > 0">
                    <h5 class="text-sm font-medium text-orange-800 mb-2">🔄 Terms Modified ({{ modifiedTerms.length }})</h5>
                    <div class="space-y-2">
                      <div v-for="change in modifiedTerms" :key="change.term_id" class="p-3 bg-orange-50 border border-orange-200 rounded">
                        <div class="text-sm font-medium text-orange-800">{{ change.term_title || 'Untitled Term' }}</div>
                        <div class="grid grid-cols-2 gap-4 mt-2">
                          <div>
                            <div class="text-xs font-medium text-red-800">Original:</div>
                            <div class="text-xs text-red-700">{{ change.original?.term_text || 'N/A' }}</div>
                          </div>
                          <div>
                            <div class="text-xs font-medium text-green-800">Modified:</div>
                            <div class="text-xs text-green-700">{{ change.modified?.term_text || 'N/A' }}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Terms Removed -->
                  <div v-if="removedTerms.length > 0">
                    <h5 class="text-sm font-medium text-red-800 mb-2">➖ Terms Removed ({{ removedTerms.length }})</h5>
                    <div class="space-y-2">
                      <div v-for="term in removedTerms" :key="term.term_id" class="p-3 bg-red-50 border border-red-200 rounded">
                        <div class="text-sm font-medium text-red-800">{{ term.term_title || 'Untitled Term' }}</div>
                        <div class="text-xs text-red-700 mt-1">{{ term.term_text }}</div>
                      </div>
                    </div>
                  </div>

                  <!-- No Changes -->
                  <div v-if="addedTerms.length === 0 && modifiedTerms.length === 0 && removedTerms.length === 0" class="text-center py-4 text-muted-foreground">
                    No changes to contract terms
                  </div>
                </div>
              </div>

              <!-- Contract Clauses Comparison -->
              <div class="border rounded-lg p-4">
                <h4 class="text-md font-semibold mb-4 flex items-center gap-2">
                  <FileText class="w-4 h-4" />
                  Contract Clauses Changes
                </h4>
                <div class="space-y-4">
                  <!-- Clauses Added -->
                  <div v-if="addedClauses.length > 0">
                    <h5 class="text-sm font-medium text-green-800 mb-2">➕ Clauses Added ({{ addedClauses.length }})</h5>
                    <div class="space-y-2">
                      <div v-for="clause in addedClauses" :key="clause.clause_id" class="p-3 bg-green-50 border border-green-200 rounded">
                        <div class="text-sm font-medium text-green-800">{{ clause.clause_name || 'Untitled Clause' }}</div>
                        <div class="text-xs text-green-700 mt-1">{{ clause.clause_text }}</div>
                      </div>
                    </div>
                  </div>

                  <!-- Clauses Modified -->
                  <div v-if="modifiedClauses.length > 0">
                    <h5 class="text-sm font-medium text-orange-800 mb-2">🔄 Clauses Modified ({{ modifiedClauses.length }})</h5>
                    <div class="space-y-2">
                      <div v-for="change in modifiedClauses" :key="change.clause_id" class="p-3 bg-orange-50 border border-orange-200 rounded">
                        <div class="text-sm font-medium text-orange-800">{{ change.clause_name || 'Untitled Clause' }}</div>
                        <div class="grid grid-cols-2 gap-4 mt-2">
                          <div>
                            <div class="text-xs font-medium text-red-800">Original:</div>
                            <div class="text-xs text-red-700">{{ change.original?.clause_text || 'N/A' }}</div>
                          </div>
                          <div>
                            <div class="text-xs font-medium text-green-800">Modified:</div>
                            <div class="text-xs text-green-700">{{ change.modified?.clause_text || 'N/A' }}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Clauses Removed -->
                  <div v-if="removedClauses.length > 0">
                    <h5 class="text-sm font-medium text-red-800 mb-2">➖ Clauses Removed ({{ removedClauses.length }})</h5>
                    <div class="space-y-2">
                      <div v-for="clause in removedClauses" :key="clause.clause_id" class="p-3 bg-red-50 border border-red-200 rounded">
                        <div class="text-sm font-medium text-red-800">{{ clause.clause_name || 'Untitled Clause' }}</div>
                        <div class="text-xs text-red-700 mt-1">{{ clause.clause_text }}</div>
                      </div>
                    </div>
                  </div>

                  <!-- No Changes -->
                  <div v-if="addedClauses.length === 0 && modifiedClauses.length === 0 && removedClauses.length === 0" class="text-center py-4 text-muted-foreground">
                    No changes to contract clauses
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex justify-end gap-3 p-6 border-t">
            <button 
              @click="showComparisonDialog = false" 
              class="px-4 py-2 border rounded-md hover:bg-muted"
            >
              Close
            </button>
            <button 
              @click="downloadComparisonReport" 
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Download Report
            </button>
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
import { ref, onMounted, computed, reactive, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  ArrowLeft, Upload, Plus, Trash2, FileCheck, Search, Calendar, FileText,
  Eye, CheckCircle, AlertTriangle, X, ChevronDown
} from 'lucide-vue-next'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui'
import contractsApi from '@/services/contractsApi'
import { PopupService } from '@/popup/popupService'
import apiService from '@/services/api'
import { getApiUrl, getTprmApiUrl } from '@/utils/backendEnv.js'

// Router and route
const router = useRouter()
const route = useRoute()
const navigate = (path) => router.push(path)
const contractId = parseInt(route.params.id)

// Reactive state
const activeTab = ref('basic')
const saving = ref(false)
const loading = ref(true)

// Version dialog state
const showVersionDialog = ref(false)
const selectedVersionType = ref('')
const currentVersion = ref('1')

// Success and error messages
const successMessage = ref('')
const errors = ref({})

// Risk analysis notifications
const showRiskAnalysisNotification = ref(false)
const showRiskAnalysisTriggered = ref(false)

// Comparison dialog state
const showComparisonDialog = ref(false)

// Original contract data for comparison
const originalContractData = ref({})
const originalContractTerms = ref([])
const originalContractClauses = ref([])

// Amendment form
const amendmentForm = ref({
  amendment_number: '',
  amendment_date: new Date().toISOString().split('T')[0],
  effective_date: '',
  amendment_type: '',
  financial_impact: '',
  currency: 'USD',
  impact_type: '',
  amendment_reason: '',
  changes_summary: '',
  notice_period_days: 30,
  auto_renewal: false,
  renewal_terms: '',
  contract_owner: null,
  legal_reviewer: null,
  approval_status: 'pending'
})

// Contract form data (from CreateContract.vue)
const formData = ref({
  // Basic Contract Information
  contract_title: '',
  contract_number: '',
  contract_type: '',
  contract_kind: 'AMENDMENT',
  contract_category: '',
  
  // Vendor Information
  vendor_id: null,
  vendor_name: '',
  
  // Financial Information
  contract_value: '',
  currency: 'USD',
  liability_cap: '',
  
  // Dates and Terms
  start_date: '',
  end_date: '',
  renewal_terms: '',
  auto_renewal: false,
  notice_period_days: 30,
  
  // Contract Status and Workflow
  status: 'DRAFT',
  workflow_stage: 'draft',
  priority: 'medium',
  compliance_status: 'under_review',
  
  // Legal and Risk Information
  dispute_resolution_method: '',
  governing_law: '',
  contract_risk_score: '',
  termination_clause_type: '',
  
  // JSON Fields
  insurance_requirements: {},
  data_protection_clauses: {},
  custom_fields: {},
  
  // Assignment and Ownership
  contract_owner: null,
  legal_reviewer: null,
  assigned_to: null,
  
  // Additional fields
  parent_contract_id: contractId,
  compliance_framework: '',
  file_path: '',  // S3 URL for uploaded amendment document
  
  // Hierarchy
  main_contract_id: contractId
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
const selectedTermFromTemplate = ref(null) // Store term object when viewing template questions
const selectedTerm = computed(() => {
  // First check if we have a stored term from template view
  if (selectedTermFromTemplate.value) {
    return selectedTermFromTemplate.value
  }
  // Otherwise, find it from contractTerms
  return contractTerms.value.find(term => String(term.term_id) === String(selectedTermId.value)) || null
})

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

// Users and vendors
const users = ref([])
const vendors = ref([])
const legalReviewers = ref([])

// OCR functionality
const ocrResults = ref([])
const uploadStep = ref('upload')
const uploadProgress = ref(0)
const selectedFile = ref(null)
const isDragOver = ref(false)
const s3UploadInfo = ref(null)

// Comparison fields configuration
const contractComparisonFields = ref([
  { key: 'contract_title', label: 'Contract Title' },
  { key: 'contract_number', label: 'Contract Number' },
  { key: 'contract_type', label: 'Contract Type' },
  { key: 'contract_value', label: 'Contract Value' },
  { key: 'currency', label: 'Currency' },
  { key: 'start_date', label: 'Start Date' },
  { key: 'end_date', label: 'End Date' },
  { key: 'priority', label: 'Priority' },
  { key: 'status', label: 'Status' },
  { key: 'contract_category', label: 'Category' },
  { key: 'notice_period_days', label: 'Notice Period (Days)' },
  { key: 'auto_renewal', label: 'Auto Renewal' },
  { key: 'dispute_resolution_method', label: 'Dispute Resolution' },
  { key: 'governing_law', label: 'Governing Law' },
  { key: 'contract_risk_score', label: 'Risk Score' },
  { key: 'compliance_framework', label: 'Compliance Framework' }
])

// Helper function to get stored token
const getStoredToken = () => {
  const keys = ['access_token', 'session_token', 'token', 'jwt_token']
  for (const key of keys) {
    const val = localStorage.getItem(key)
    if (val) return val
  }
  return null
}

// Helper function to refresh token if needed
const refreshTokenIfNeeded = async () => {
  try {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      console.warn('⚠️ No refresh token available')
      return false
    }
    
    console.log('🔄 Attempting to refresh token...')
    const apiOrigin = getApiOrigin() || 'https://grc-tprm.vardaands.com'
    const refreshResponse = await fetch(`${apiOrigin}/api/jwt/refresh/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken })
    })
    
    if (refreshResponse.ok) {
      const refreshData = await refreshResponse.json()
      if (refreshData.access_token) {
        localStorage.setItem('access_token', refreshData.access_token)
        if (refreshData.refresh_token) {
          localStorage.setItem('refresh_token', refreshData.refresh_token)
        }
        console.log('✅ Token refreshed successfully')
        return true
      }
    }
    
    console.warn('⚠️ Token refresh failed')
    return false
  } catch (error) {
    console.error('❌ Error refreshing token:', error)
    return false
  }
}

// Real OCR file upload handler
const handleFileUpload = async (event) => {
  console.log('📁 Amendment file upload triggered:', event)
  
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
  const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/tiff']
  if (!allowedTypes.includes(file.type)) {
    errors.value.ocr = 'Invalid file type. Please upload a PDF, PNG, JPG, or TIFF file.'
    console.log('❌ Invalid file type:', file.type)
    return
  }
  
  // Validate file size (max 10MB)
  const maxSize = 10 * 1024 * 1024 // 10MB in bytes
  if (file.size > maxSize) {
    errors.value.ocr = 'File size exceeds 10MB limit. Please choose a smaller file.'
    console.log('❌ File too large:', file.size, 'bytes')
    return
  }
  
  selectedFile.value = file
  uploadStep.value = 'processing'
  uploadProgress.value = 0
  console.log('✅ File validated, starting OCR processing...')
  
  try {
    // Create FormData for file upload
    const uploadFormData = new FormData()
    uploadFormData.append('file', file)
    uploadFormData.append('document_type', 'amendment')
    uploadFormData.append('contract_id', contractId.toString())
    
    console.log('📤 Uploading file to OCR service...')
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 300)
    
    // Get authentication token
    let token = getStoredToken()
    
    console.log('🔐 Token check:', {
      hasToken: !!token,
      tokenLength: token ? token.length : 0,
      tokenPrefix: token ? token.substring(0, 20) + '...' : 'No token'
    })
    
    // If no token found, show error immediately
    if (!token) {
      console.error('❌ No authentication token found')
      throw new Error('Authentication required. Please log in to upload files.')
    }
    
    // Perform OCR upload with retry logic for 401 errors
    const performOcrUpload = async (authToken) => {
      const headers = {
        'Authorization': `Bearer ${authToken}`
      }
      
      // Use the correct endpoint: /tprm/contracts/contracts/{contractId}/upload-ocr/
      // Note: The contracts URLs are mounted at /api/tprm/contracts/ and routes start with 'contracts/'
      const uploadUrl = getTprmApiUrl(`/contracts/contracts/${contractId}/upload-ocr/`)
      
      console.log('📤 Request headers:', headers)
      console.log('📤 Request URL:', uploadUrl)
      
      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers: headers,
        body: uploadFormData
      })
      
      return response
    }
    
    let finalResponse = await performOcrUpload(token)
    
    // Handle 401 errors - try to refresh token and retry
    if (finalResponse.status === 401) {
      console.log('🔄 401 error detected, attempting token refresh...')
      
      const refreshSuccess = await refreshTokenIfNeeded()
      if (refreshSuccess) {
        // Get the new token and retry
        token = getStoredToken()
        if (token) {
          console.log('✅ Retrying OCR upload with refreshed token')
          finalResponse = await performOcrUpload(token)
        }
      }
    }
    
    clearInterval(progressInterval)
    uploadProgress.value = 100
    
    if (!finalResponse.ok) {
      const errorData = await finalResponse.json().catch(() => ({ error: 'Unknown error occurred' }))
      
      // Handle authentication errors specifically
      if (finalResponse.status === 401 || finalResponse.status === 403) {
        throw new Error('Authentication failed. Please log in again and try uploading the document.')
      }
      
      throw new Error(errorData.error || `HTTP ${finalResponse.status}: ${finalResponse.statusText}`)
    }
    
    const result = await finalResponse.json()
    console.log('✅ OCR processing completed:', result)
    
    // Handle S3 upload information
    if (result.upload_info) {
      s3UploadInfo.value = result.upload_info
      console.log('📁 S3 Upload Info:', result.upload_info)
      if (result.upload_info.success && result.upload_info.file_info?.url) {
        // Store S3 URL in formData
        formData.value.file_path = result.upload_info.file_info.url
        console.log('✅ S3 URL stored in formData:', formData.value.file_path)
      } else {
        console.warn('⚠️ S3 upload failed or URL not available:', result.upload_info)
      }
    } else {
      console.warn('⚠️ No S3 upload info in response (S3 client may not be configured)')
    }
    
    const contractData = result?.data || result?.contract_extraction?.data || null
    if (result.success) {
      if (contractData && typeof contractData === 'object' && Object.keys(contractData).length > 0) {
        // Process the OCR extracted data
        await processOCRResults(contractData)
        uploadStep.value = 'review'
        console.log('✅ OCR data processed, showing review step')
      } else {
        // No data extracted but OCR completed successfully
        console.warn('⚠️ OCR completed but no data was extracted from the document')
        uploadStep.value = 'upload'
        errors.value.ocr = 'No data could be extracted from the document. The document may be blank, unreadable, or in an unsupported format. Please try a different document.'
      }
    } else {
      throw new Error(result.error || 'Failed to extract amendment data')
    }
    
  } catch (error) {
    console.error('❌ OCR processing error:', error)
    errors.value.ocr = `OCR Error: ${error.message}`
    uploadStep.value = 'upload'
    uploadProgress.value = 0
    selectedFile.value = null
  }
}

// Process OCR results into ocrResults array
const processOCRResults = async (ocrData) => {
  console.log('🔄 Processing OCR results for amendment:', ocrData)
  
  // Helper function to calculate confidence and determine if review is needed
  const getConfidenceInfo = (value, defaultConfidence = 85) => {
    if (!value || value === '' || value === null || value === undefined) {
      return { confidence: 0, needsReview: true }
    }
    return { confidence: defaultConfidence, needsReview: defaultConfidence < 85 }
  }
  
  // Build OCR results array from the extracted data
  const results = []
  
  // Amendment-specific fields - Always extract these for amendments
  if (ocrData.amendment_number) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.amendment_number, 95)
    results.push({ field: 'amendment_number', value: ocrData.amendment_number, confidence, needsReview, type: 'text' })
  }
  
  if (ocrData.amendment_date) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.amendment_date, 95)
    results.push({ field: 'amendment_date', value: ocrData.amendment_date, confidence, needsReview, type: 'date' })
  }
  
  if (ocrData.effective_date) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.effective_date, 93)
    results.push({ field: 'effective_date', value: ocrData.effective_date, confidence, needsReview, type: 'date' })
  }
  
  if (ocrData.amendment_type) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.amendment_type, 90)
    results.push({ field: 'amendment_type', value: ocrData.amendment_type, confidence, needsReview, type: 'select', options: ['financial', 'scope', 'timeline', 'terms', 'other'] })
  }
  
  if (ocrData.financial_impact) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.financial_impact, 92)
    results.push({ field: 'financial_impact', value: ocrData.financial_impact, confidence, needsReview, type: 'number', step: '0.01' })
  }
  
  if (ocrData.impact_type) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.impact_type, 88)
    results.push({ field: 'impact_type', value: ocrData.impact_type, confidence, needsReview, type: 'select', options: ['increase', 'decrease', 'no_change'] })
  }
  
  if (ocrData.amendment_reason) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.amendment_reason, 85)
    results.push({ field: 'amendment_reason', value: ocrData.amendment_reason, confidence, needsReview: true, type: 'textarea' })
  }
  
  if (ocrData.changes_summary) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.changes_summary, 87)
    results.push({ field: 'changes_summary', value: ocrData.changes_summary, confidence, needsReview, type: 'textarea' })
  }
  
  // Log for debugging
  console.log('📋 Terms found:', ocrData.terms?.length || 0)
  console.log('📄 Clauses found:', ocrData.clauses?.length || 0)
  
  // Basic contract information
  if (ocrData.contract_title) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_title, 95)
    results.push({ field: 'title', value: ocrData.contract_title, confidence, needsReview, type: 'text' })
  }
  
  if (ocrData.contract_number) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_number, 96)
    results.push({ field: 'contract_number', value: ocrData.contract_number, confidence, needsReview, type: 'text' })
  }
  
  if (ocrData.contract_type) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_type, 92)
    results.push({ field: 'type', value: ocrData.contract_type, confidence, needsReview, type: 'select', options: ['MASTER_AGREEMENT', 'SOW', 'PURCHASE_ORDER', 'SERVICE_AGREEMENT', 'LICENSE', 'NDA'] })
  }
  
  if (ocrData.priority) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.priority, 88)
    results.push({ field: 'priority', value: ocrData.priority, confidence, needsReview, type: 'select', options: ['low', 'medium', 'high', 'urgent'] })
  }
  
  if (ocrData.contract_category) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_category, 89)
    results.push({ field: 'contract_category', value: ocrData.contract_category, confidence, needsReview, type: 'select', options: ['goods', 'services', 'technology', 'consulting', 'others'] })
  }
  
  // Financial information
  if (ocrData.contract_value) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_value, 94)
    results.push({ field: 'value', value: ocrData.contract_value, confidence, needsReview, type: 'number', step: '0.01' })
  }
  
  if (ocrData.currency) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.currency, 97)
    results.push({ field: 'currency', value: ocrData.currency, confidence, needsReview, type: 'select', options: ['USD', 'EUR', 'GBP', 'CAD', 'AUD'] })
  }
  
  if (ocrData.liability_cap) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.liability_cap, 91)
    results.push({ field: 'liability_cap', value: ocrData.liability_cap, confidence, needsReview, type: 'number', step: '0.01' })
  }
  
  // Dates and terms
  if (ocrData.start_date) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.start_date, 96)
    results.push({ field: 'start_date', value: ocrData.start_date, confidence, needsReview, type: 'date' })
  }
  
  if (ocrData.end_date) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.end_date, 95)
    results.push({ field: 'end_date', value: ocrData.end_date, confidence, needsReview, type: 'date' })
  }
  
  if (ocrData.notice_period_days) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.notice_period_days, 87)
    results.push({ field: 'notice_period_days', value: ocrData.notice_period_days, confidence, needsReview, type: 'number' })
  }
  
  if (ocrData.auto_renewal !== undefined) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.auto_renewal, 84)
    results.push({ field: 'auto_renewal', value: ocrData.auto_renewal ? 'true' : 'false', confidence, needsReview, type: 'select', options: ['true', 'false'] })
  }
  
  if (ocrData.renewal_terms) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.renewal_terms, 86)
    results.push({ field: 'renewal_terms', value: ocrData.renewal_terms, confidence, needsReview: true, type: 'textarea' })
  }
  
  // Status
  if (ocrData.status) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.status, 91)
    results.push({ field: 'status', value: ocrData.status, confidence, needsReview, type: 'select', options: ['DRAFT', 'ACTIVE', 'UNDER_REVIEW', 'EXPIRED'] })
  }
  
  // Legal and risk information
  if (ocrData.dispute_resolution_method) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.dispute_resolution_method, 89)
    results.push({ field: 'dispute_resolution_method', value: ocrData.dispute_resolution_method, confidence, needsReview, type: 'select', options: ['negotiation', 'mediation', 'arbitration', 'litigation'] })
  }
  
  if (ocrData.governing_law) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.governing_law, 90)
    results.push({ field: 'governing_law', value: ocrData.governing_law, confidence, needsReview, type: 'text' })
  }
  
  if (ocrData.contract_risk_score) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_risk_score, 83)
    results.push({ field: 'contract_risk_score', value: ocrData.contract_risk_score, confidence, needsReview, type: 'number', step: '0.1' })
  }
  
  if (ocrData.termination_clause_type) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.termination_clause_type, 86)
    results.push({ field: 'termination_clause_type', value: ocrData.termination_clause_type, confidence, needsReview, type: 'select', options: ['convenience', 'cause', 'both', 'none'] })
  }
  
  if (ocrData.compliance_framework) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.compliance_framework, 89)
    results.push({ field: 'compliance_framework', value: ocrData.compliance_framework, confidence, needsReview, type: 'select', options: ['SOC2', 'GDPR', 'CCPA', 'ISO27001', 'PCI DSS', 'HIPAA', 'Other'] })
  }
  
  // Process terms - Backend normalizes to {category, title, text, is_standard}
  if (ocrData.terms && Array.isArray(ocrData.terms)) {
    ocrData.terms.forEach((term, index) => {
      // Check both normalized format (category, title, text) and original format (term_category, term_title, term_text)
      const category = term.category || term.term_category
      const title = term.title || term.term_title
      const text = term.text || term.term_text
      
      if (category && text) {
        const { confidence, needsReview } = getConfidenceInfo(text, 87)
        results.push({ 
          field: `term_${category.replace(/\s+/g, '_')}`, 
          value: text, 
          confidence, 
          needsReview, 
          type: 'textarea',
          metadata: { category, title }  // Store for later use
        })
      }
    })
  }
  
  // Process clauses - Backend normalizes to {name, type, text, ...}
  if (ocrData.clauses && Array.isArray(ocrData.clauses)) {
    ocrData.clauses.forEach((clause, index) => {
      // Check both normalized format (name, type, text) and original format (clause_name, clause_type, clause_text)
      const name = clause.name || clause.clause_name
      const type = clause.type || clause.clause_type || 'standard'
      const text = clause.text || clause.clause_text
      
      if (name && text) {
        const { confidence, needsReview } = getConfidenceInfo(text, 88)
        results.push({ 
          field: `clause_${type}_${index}`,  // Include index to avoid duplicates
          value: text, 
          confidence, 
          needsReview, 
          type: 'textarea',
          metadata: { name, type }  // Store for later use
        })
      }
    })
  }
  
  ocrResults.value = results
  console.log('✅ OCR results processed for amendment:', results.length, 'fields extracted')
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

// Reset upload state
const resetUpload = () => {
  uploadStep.value = 'upload'
  uploadProgress.value = 0
  selectedFile.value = null
  ocrResults.value = []
  s3UploadInfo.value = null
  if (errors.value.ocr) {
    delete errors.value.ocr
  }
}

// OCR result management
const updateOCRResult = (index, newValue) => {
  if (ocrResults.value[index]) {
    ocrResults.value[index].value = newValue
  }
}

const removeOCRResult = (index) => {
  ocrResults.value.splice(index, 1)
}

const clearOCRResults = () => {
  ocrResults.value = []
}

// Helper functions for OCR data processing
const getFieldValue = (fieldName) => {
  const result = ocrResults.value.find(r => r.field === fieldName)
  return result ? result.value : ''
}

const getBooleanFieldValue = (fieldName) => {
  const value = getFieldValue(fieldName)
  return value === 'true' || value === true
}

const getNumberFieldValue = (fieldName) => {
  const value = getFieldValue(fieldName)
  return value ? parseFloat(value) : null
}

const getIntegerFieldValue = (fieldName) => {
  const value = getFieldValue(fieldName)
  return value ? parseInt(value) : null
}

// Map to valid term category helper
const mapToValidTermCategory = (category) => {
  const validCategories = ['Payment', 'Delivery', 'Performance', 'Liability', 'Termination', 'Intellectual Property', 'Confidentiality', 'Other']
  return validCategories.includes(category) ? category : 'Other'
}

// Comprehensive OCR data application
const applyOCRData = () => {
  try {
    console.log('🔄 Applying OCR data to amendment form...')
    
    // Build insurance requirements and data protection clauses JSON objects
    const insuranceRequirements = {
      general_liability: getFieldValue('insurance_requirements') || '',
      professional_liability: '',
      cyber_liability: '',
      workers_compensation: ''
    }
    
    const dataProtectionClauses = {
      gdpr_compliance: getFieldValue('data_protection_clauses') || '',
      data_retention: '',
      breach_notification: '',
      data_processing_agreement: ''
    }
    
    // Apply to amendment form data
    amendmentForm.value.amendment_number = getFieldValue('amendment_number')
    amendmentForm.value.amendment_date = getFieldValue('amendment_date')
    amendmentForm.value.effective_date = getFieldValue('effective_date')
    amendmentForm.value.amendment_type = getFieldValue('amendment_type')
    amendmentForm.value.financial_impact = getNumberFieldValue('financial_impact')
    amendmentForm.value.impact_type = getFieldValue('impact_type')
    amendmentForm.value.amendment_reason = getFieldValue('amendment_reason')
    amendmentForm.value.changes_summary = getFieldValue('changes_summary')
    
    // Apply to contract form data
    formData.value.contract_title = getFieldValue('title')
    formData.value.contract_number = getFieldValue('contract_number')
    formData.value.contract_type = getFieldValue('type')
    formData.value.priority = getFieldValue('priority')
    formData.value.contract_category = getFieldValue('contract_category')
    formData.value.vendor_name = getFieldValue('vendor_name')
    formData.value.contract_value = getNumberFieldValue('value')?.toString()
    formData.value.currency = getFieldValue('currency')
    formData.value.liability_cap = getNumberFieldValue('liability_cap')?.toString()
    formData.value.start_date = getFieldValue('start_date')
    formData.value.end_date = getFieldValue('end_date')
    formData.value.notice_period_days = getIntegerFieldValue('notice_period_days')
    formData.value.auto_renewal = getBooleanFieldValue('auto_renewal')
    formData.value.renewal_terms = getFieldValue('renewal_terms')
    formData.value.status = getFieldValue('status')
    formData.value.dispute_resolution_method = getFieldValue('dispute_resolution_method')
    formData.value.governing_law = getFieldValue('governing_law')
    formData.value.contract_risk_score = getNumberFieldValue('contract_risk_score')?.toString()
    formData.value.termination_clause_type = getFieldValue('termination_clause_type')
    formData.value.compliance_framework = getFieldValue('compliance_framework')
    formData.value.insurance_requirements = insuranceRequirements
    formData.value.data_protection_clauses = dataProtectionClauses
    
    // Process contract terms from OCR
    const ocrTerms = []
    const termFields = ocrResults.value.filter(r => r.field.startsWith('term_'))
    
    termFields.forEach(termField => {
      const category = termField.field.replace('term_', '').replace(/_/g, ' ')
      const categoryWords = category.split(' ').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
      )
      const formattedCategory = categoryWords.join(' ')
      
      ocrTerms.push({
        term_id: `ocr_term_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${contractId}`,
        term_category: mapToValidTermCategory(formattedCategory),
        term_title: `${formattedCategory} Terms`,
        term_text: termField.value,
        risk_level: 'Medium',
        compliance_status: 'Pending',
        is_standard: false,
        approval_status: 'Pending',
        version_number: '1.0'
      })
    })
    
    // Process contract clauses from OCR
    const ocrClauses = []
    const clauseFields = ocrResults.value.filter(r => r.field.startsWith('clause_') || r.field.startsWith('renewal_') || r.field.startsWith('termination_'))
    
    clauseFields.forEach(clauseField => {
      let clauseType = 'standard'
      let clauseName = clauseField.field.replace(/^(clause_|renewal_|termination_)/, '')
      
      if (clauseField.field.startsWith('renewal_')) {
        clauseType = 'renewal'
        clauseName = `Renewal ${clauseName.charAt(0).toUpperCase() + clauseName.slice(1)}`
      } else if (clauseField.field.startsWith('termination_')) {
        clauseType = 'termination'
        clauseName = `Termination ${clauseName.charAt(0).toUpperCase() + clauseName.slice(1)}`
      } else {
        clauseName = clauseName.charAt(0).toUpperCase() + clauseName.slice(1)
      }
      
      const newClause = {
        clause_id: `ocr_clause_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${contractId}`,
        clause_name: clauseName,
        clause_type: clauseType,
        clause_text: clauseField.value,
        risk_level: 'medium',
        legal_category: clauseType === 'renewal' ? 'Contract Renewal' : clauseType === 'termination' ? 'Contract Termination' : 'Standard Clause',
        version_number: '1.0',
        is_standard: false
      }
      
      // Add specific fields based on clause type
      if (clauseType === 'renewal') {
        newClause.notice_period_days = getIntegerFieldValue('renewal_notice_period') || 30
        newClause.auto_renew = getBooleanFieldValue('renewal_auto') || false
        newClause.renewal_terms = getFieldValue('renewal_terms') || ''
      } else if (clauseType === 'termination') {
        newClause.termination_notice_period = getIntegerFieldValue('termination_notice_period') || 30
        newClause.early_termination_fee = getNumberFieldValue('early_termination_fee') || 0
        newClause.termination_conditions = getFieldValue('termination_conditions') || ''
      }
      
      ocrClauses.push(newClause)
    })
    
    // Add OCR terms and clauses to existing ones
    if (ocrTerms.length > 0) {
      contractTerms.value = [...contractTerms.value, ...ocrTerms]
      console.log('✅ Added', ocrTerms.length, 'OCR terms to amendment')
    }
    
    if (ocrClauses.length > 0) {
      contractClauses.value = [...contractClauses.value, ...ocrClauses]
      console.log('✅ Added', ocrClauses.length, 'OCR clauses to amendment')
    }
    
    // Force reactivity updates
    contractTerms.value = [...contractTerms.value]
    contractClauses.value = [...contractClauses.value]
    
    // Switch to terms tab if terms were added
    if (ocrTerms.length > 0) {
      activeTab.value = 'terms'
    }
    
    // Manual DOM updates for better reactivity
    setTimeout(() => {
      // Force re-render of form fields
      const inputs = document.querySelectorAll('input, select, textarea')
      inputs.forEach(input => {
        if (input.value !== input.defaultValue) {
          input.dispatchEvent(new Event('input', { bubbles: true }))
        }
      })
    }, 100)
    
    const totalFields = Object.keys(formData.value).length + Object.keys(amendmentForm.value).length
    const appliedFields = ocrResults.value.length
    
    PopupService.success(`OCR Data Applied Successfully!\n\nApplied ${appliedFields} fields to amendment form\nAdded ${ocrTerms.length} contract terms\nAdded ${ocrClauses.length} contract clauses\n\nAmendment form has been populated with extracted data.`, 'OCR Data Applied')
    
    console.log('✅ OCR data application completed successfully')
    
  } catch (error) {
    console.error('❌ Error applying OCR data:', error)
    PopupService.error('Error applying OCR data: ' + error.message, 'OCR Error')
  }
}

// Clear existing data and apply OCR
const applyOCRDataWithClear = () => {
  if (confirm('This will clear all existing terms and clauses before applying OCR data. Continue?')) {
    contractTerms.value = []
    contractClauses.value = []
    applyOCRData()
  }
}

// Methods for managing terms and clauses
const addNewTerm = () => {
  const newTerm = {
    term_id: `term_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${contractId}`,
    term_category: '',
    term_title: '',
    term_text: '',
    risk_level: 'Low',
    compliance_status: 'Pending',
    is_standard: false,
    approval_status: 'Pending',
    version_number: '1.0'
  }
  contractTerms.value.push(newTerm)
}

const removeTerm = (index) => {
  contractTerms.value = contractTerms.value.filter((_, i) => i !== index)
}

const addNewClause = () => {
  const newClause = {
    clause_id: `clause_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${contractId}`,
    clause_name: '',
    clause_type: 'standard',
    clause_text: '',
    risk_level: 'low',
    legal_category: '',
    version_number: '1.0',
    is_standard: false
  }
  contractClauses.value.push(newClause)
}

const removeClause = (clauseId) => {
  contractClauses.value = contractClauses.value.filter(c => c.clause_id !== clauseId)
}

// Debug methods
const debugTerms = () => {
  try {
    console.log('🐛 DEBUG: Current contract terms state:')
    console.log('📊 Number of terms:', contractTerms.value ? contractTerms.value.length : 0)
    console.log('📋 Full terms array:', JSON.stringify(contractTerms.value || [], null, 2))
    
    if (contractTerms.value && Array.isArray(contractTerms.value)) {
      contractTerms.value.forEach((term, index) => {
        console.log(`🔍 Term ${index + 1}:`, {
          term_id: term?.term_id || 'undefined',
          term_title: term?.term_title || '',
          term_text: term?.term_text || '',
          term_text_length: term?.term_text ? term.term_text.length : 0,
          term_text_empty: !term?.term_text || term.term_text.trim() === ''
        })
      })
    } else {
      console.log('❌ contractTerms is not an array:', contractTerms.value)
    }
  } catch (error) {
    console.error('❌ Error in debugTerms:', error)
  }
}

// Test API calls for debugging
const testApiCalls = async () => {
  try {
    console.log('🧪 Testing API calls for contract ID:', contractId)
    
    // Test contract terms API
    console.log('📞 Testing contract terms API...')
    const termsResponse = await contractsApi.getContractTerms(contractId)
    console.log('📋 Terms API response:', termsResponse)
    
    // Test contract clauses API
    console.log('📞 Testing contract clauses API...')
    const clausesResponse = await contractsApi.getContractClauses(contractId)
    console.log('📋 Clauses API response:', clausesResponse)
    
    // Test contract API
    console.log('📞 Testing contract API...')
    const contractResponse = await contractsApi.getContract(contractId)
    console.log('📋 Contract API response:', contractResponse)
    
  } catch (error) {
    console.error('❌ Error testing API calls:', error)
  }
}

const debugClauses = () => {
  try {
    console.log('🐛 DEBUG: Current contract clauses state:')
    console.log('📊 Number of clauses:', contractClauses.value ? contractClauses.value.length : 0)
    console.log('📋 Full clauses array:', JSON.stringify(contractClauses.value || [], null, 2))
    
    if (contractClauses.value && Array.isArray(contractClauses.value)) {
      contractClauses.value.forEach((clause, index) => {
        console.log(`🔍 Clause ${index + 1}:`, {
          clause_id: clause?.clause_id || 'undefined',
          clause_name: clause?.clause_name || '',
          clause_text: clause?.clause_text || '',
          clause_text_length: clause?.clause_text ? clause.clause_text.length : 0,
          clause_name_empty: !clause?.clause_name || clause.clause_name.trim() === '',
          clause_text_empty: !clause?.clause_text || clause.clause_text.trim() === ''
        })
      })
    } else {
      console.log('❌ contractClauses is not an array:', contractClauses.value)
    }
  } catch (error) {
    console.error('❌ Error in debugClauses:', error)
  }
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
    const qCategory = q.term_category || q._matched_term_category || ''
    const qTermId = q.term_id ? String(q.term_id) : ''
    if (category && qCategory && qCategory.toLowerCase() === category.toLowerCase()) return true
    if (termId && qTermId && (qTermId === termId || qTermId.includes(termId) || termId.includes(qTermId))) return true
    return false
  })
}

const getQuestionnaireCount = (term) => {
  if (!term) return 0
  const category = term.term_category
  const termId = term.term_id ? String(term.term_id) : ''
  return allTermQuestionnaires.value.filter(q => {
    const qCategory = q.term_category || q._matched_term_category || ''
    const qTermId = q.term_id ? String(q.term_id) : ''
    if (category && qCategory && qCategory.toLowerCase() === category.toLowerCase()) return true
    if (termId && qTermId && (qTermId === termId || qTermId.includes(termId) || termId.includes(qTermId))) return true
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
  const termIdStr = String(termId)
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
    TEXT: 'text',
    TEXTAREA: 'textarea',
    NUMBER: 'number',
    BOOLEAN: 'boolean',
    YES_NO: 'yes/no',
    MULTIPLE_CHOICE: 'multiple_choice',
    CHECKBOX: 'checkbox',
    RATING: 'rating',
    SCALE: 'scale',
    DATE: 'date'
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
    // Store the term object so selectedTerm computed can access it
    selectedTermFromTemplate.value = term || null
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
  selectedTermFromTemplate.value = null // Clear stored term
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
    // Store the term object so selectedTerm computed can access it
    selectedTermFromTemplate.value = term
    showQuestionnairesModal.value = true
  } catch (error) {
    console.error('Error loading questionnaires:', error)
    PopupService.error(error.message || 'Failed to load questionnaires.', 'Questionnaires Error')
  }
}

const editQuestionnaires = (term, existingQuestionnaires = []) => {
  if (!term) return

  sessionStorage.setItem('amendment_draft_data', JSON.stringify({
    formData: formData.value,
    contractTerms: contractTerms.value,
    contractClauses: contractClauses.value,
    amendmentForm: amendmentForm.value,
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
      return_to: 'contract-amendment',
      contract_id: contractId,
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
      sessionStorage.setItem('amendment_draft_data', JSON.stringify({
        formData: formData.value,
        contractTerms: contractTerms.value,
        contractClauses: contractClauses.value,
        amendmentForm: amendmentForm.value,
        selectedTemplates: selectedTemplates.value
      }))

      router.push({
        path: '/questionnaire-templates',
        query: {
          module_type: 'CONTRACT',
          term_id: term.term_id,
          term_title: term.term_title,
          term_category: term.term_category,
          return_to: 'contract-amendment',
          contract_id: contractId
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

const addNewRenewalClause = () => {
  const newClause = {
    clause_id: `clause_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${contractId}`,
    clause_name: 'Renewal Terms',
    clause_type: 'renewal',
    clause_text: '',
    risk_level: 'low',
    legal_category: 'Contract Renewal',
    version_number: '1.0',
    is_standard: false,
    notice_period_days: 30,
    auto_renew: false,
    renewal_terms: ''
  }
  contractClauses.value.push(newClause)
}

const addNewTerminationClause = () => {
  const newClause = {
    clause_id: `clause_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${contractId}`,
    clause_name: 'Termination Terms',
    clause_type: 'termination',
    clause_text: '',
    risk_level: 'medium',
    legal_category: 'Contract Termination',
    version_number: '1.0',
    is_standard: false,
    termination_notice_period: 30,
    early_termination_fee: 0,
    termination_conditions: ''
  }
  contractClauses.value.push(newClause)
}



// Load data methods
const loadUsers = async () => {
  try {
    const response = await contractsApi.getUsers()
    if (response.success !== false) {
      users.value = response.success ? response.data : response
    }
  } catch (error) {
    console.error('Error loading users:', error)
  }
}

const loadVendors = async () => {
  try {
    const response = await contractsApi.getVendors()
    if (response.success !== false) {
      vendors.value = response.success ? response.data : response
    }
  } catch (error) {
    console.error('Error loading vendors:', error)
  }
}

const loadLegalReviewers = async () => {
  try {
    const response = await contractsApi.getLegalReviewers()
    if (response.success !== false) {
      legalReviewers.value = response.success ? response.data : response
    }
  } catch (error) {
    console.error('Error loading legal reviewers:', error)
  }
}

// Load original contract data to pre-populate the form
const loadOriginalContract = async () => {
  try {
    // Load contract data, terms, and clauses in parallel
    const [contractResponse, termsResponse, clausesResponse] = await Promise.all([
      contractsApi.getContract(contractId),
      contractsApi.getContractTerms(contractId).catch(err => {
        console.warn('Error loading contract terms:', err)
        return { success: true, data: [] }
      }),
      contractsApi.getContractClauses(contractId).catch(err => {
        console.warn('Error loading contract clauses:', err)
        return { success: true, data: [] }
      })
    ])
    
    if (contractResponse.success !== false) {
      const contractData = contractResponse.success ? contractResponse.data : contractResponse
      
      // Store original contract data for comparison
      originalContractData.value = { ...contractData }
      
      // Pre-populate contract form data with original contract data
      // Set current version for version calculation
      currentVersion.value = contractData.version_number || '1'

      formData.value = {
        // Basic Contract Information
        contract_title: contractData.contract_title || '',
        contract_number: contractData.contract_number || '',
        contract_type: contractData.contract_type || '',
        contract_kind: 'AMENDMENT',
        contract_category: contractData.contract_category || '',
        
        // Vendor Information
        vendor_id: contractData.vendor_id || null,
        vendor_name: contractData.vendor?.company_name || '',
        
        // Financial Information
        contract_value: contractData.contract_value?.toString() || '',
        currency: contractData.currency || 'USD',
        liability_cap: contractData.liability_cap?.toString() || '',
        
        // Dates and Terms
        start_date: contractData.start_date || '',
        end_date: contractData.end_date || '',
        renewal_terms: contractData.renewal_terms || '',
        auto_renewal: contractData.auto_renewal || false,
        notice_period_days: contractData.notice_period_days || 30,
        
        // Contract Status and Workflow
        status: contractData.status || 'DRAFT',
        workflow_stage: contractData.workflow_stage || 'draft',
        priority: contractData.priority || 'medium',
        compliance_status: contractData.compliance_status || 'under_review',
        
        // Legal and Risk Information
        dispute_resolution_method: contractData.dispute_resolution_method || '',
        governing_law: contractData.governing_law || '',
        contract_risk_score: contractData.contract_risk_score?.toString() || '',
        termination_clause_type: contractData.termination_clause_type || '',
        
        // JSON Fields
        insurance_requirements: contractData.insurance_requirements || {},
        data_protection_clauses: contractData.data_protection_clauses || {},
        custom_fields: contractData.custom_fields || {},
        
        // Assignment and Ownership
        contract_owner: contractData.contract_owner || null,
        legal_reviewer: contractData.legal_reviewer || null,
        assigned_to: contractData.assigned_to || null,
        
        // Additional fields
        parent_contract_id: contractId,
        compliance_framework: contractData.compliance_framework || '',
        
        // Hierarchy
        main_contract_id: contractData.main_contract_id || contractId
      }
      
      // Load contract terms from separate API call
      if (termsResponse.success !== false) {
        const termsData = termsResponse.success ? termsResponse.data : termsResponse
        if (Array.isArray(termsData)) {
          // Store original terms for comparison
          originalContractTerms.value = termsData.map(term => ({
            term_id: term.term_id || `term_${Date.now()}`,
            term_category: term.term_category || '',
            term_title: term.term_title || '',
            term_text: term.term_text || '',
            risk_level: term.risk_level || 'Low',
            compliance_status: term.compliance_status || 'Pending',
            is_standard: term.is_standard || false,
            approval_status: term.approval_status || 'Pending',
            version_number: term.version_number || '1.0'
          }))
          
          // Set current terms for editing
          contractTerms.value = [...originalContractTerms.value]
          console.log('✅ Contract terms loaded:', contractTerms.value.length, 'terms')
        }
      }
      
      // Load contract clauses from separate API call
      if (clausesResponse.success !== false) {
        const clausesData = clausesResponse.success ? clausesResponse.data : clausesResponse
        if (Array.isArray(clausesData)) {
          // Store original clauses for comparison
          originalContractClauses.value = clausesData.map(clause => ({
            clause_id: clause.clause_id || `clause_${Date.now()}`,
            clause_name: clause.clause_name || '',
            clause_type: clause.clause_type || 'standard',
            clause_text: clause.clause_text || '',
            risk_level: clause.risk_level || 'low',
            legal_category: clause.legal_category || '',
            version_number: clause.version_number || '1.0',
            is_standard: clause.is_standard || false,
            notice_period_days: clause.notice_period_days || null,
            auto_renew: clause.auto_renew || false,
            renewal_terms: clause.renewal_terms || '',
            termination_notice_period: clause.termination_notice_period || null,
            early_termination_fee: clause.early_termination_fee || null,
            termination_conditions: clause.termination_conditions || ''
          }))
          
          // Set current clauses for editing
          contractClauses.value = [...originalContractClauses.value]
          console.log('✅ Contract clauses loaded:', contractClauses.value.length, 'clauses')
        }
      }
      
      console.log('✅ Original contract data loaded and pre-populated:', formData.value)
      console.log('✅ Contract terms loaded:', contractTerms.value.length, 'terms')
      console.log('✅ Contract clauses loaded:', contractClauses.value.length, 'clauses')
    } else {
      throw new Error(contractResponse.message || 'Failed to load contract')
    }
  } catch (error) {
    console.error('Error loading original contract:', error)
    successMessage.value = ''
    errors.value.general = `Error loading contract data: ${error.message}`
  }
}

// Version calculation methods
const getMajorVersion = () => {
  const current = parseFloat(currentVersion.value)
  return Math.floor(current) + 1
}

const getMinorVersion = () => {
  const current = parseFloat(currentVersion.value)
  const major = Math.floor(current)
  const minor = current - major
  return parseFloat((major + minor + 0.1).toFixed(1))
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

// Create amendment method
const createAmendment = async () => {
  if (!selectedVersionType.value) {
    successMessage.value = ''
    errors.value.general = 'Please select a version type'
    return
  }

  try {
    saving.value = true
    showVersionDialog.value = false

    // Validate required fields
    if (!formData.value.contract_title || !formData.value.contract_type || !formData.value.start_date || !formData.value.end_date) {
      successMessage.value = ''
      errors.value.general = 'Please fill in all required fields (Title, Type, Start Date, End Date)'
      return
    }

    // Calculate new version number
    let newVersionNumber
    if (selectedVersionType.value === 'major') {
      newVersionNumber = getMajorVersion()
    } else {
      newVersionNumber = getMinorVersion()
    }

    // Optimize questionnaire loading: Only load what's needed
    const termsWithQuestionnaires = []
    
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
          termsWithQuestionnaires.push({
            ...result.term,
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
      termsWithQuestionnaires.push({
        ...term,
        questionnaires
      })
    }

    // Prepare amendment data
    const amendmentData = {
      ...formData.value,
      ...amendmentForm.value,
      version_type: selectedVersionType.value,
      version_number: newVersionNumber,
      terms: termsWithQuestionnaires,
      clauses: contractClauses.value || []
    }
    
    // Clean up the data to ensure it's properly formatted
    if (amendmentData.insurance_requirements && typeof amendmentData.insurance_requirements === 'object') {
      amendmentData.insurance_requirements = JSON.stringify(amendmentData.insurance_requirements)
    }
    if (amendmentData.data_protection_clauses && typeof amendmentData.data_protection_clauses === 'object') {
      amendmentData.data_protection_clauses = JSON.stringify(amendmentData.data_protection_clauses)
    }
    if (amendmentData.custom_fields && typeof amendmentData.custom_fields === 'object') {
      amendmentData.custom_fields = JSON.stringify(amendmentData.custom_fields)
    }

    console.log('Creating amendment with data:', amendmentData)
    console.log('Amendment form data:', amendmentForm.value)
    console.log('Contract form data:', formData.value)
    console.log('📁 Amendment document file_path:', amendmentData.file_path || 'No file_path')
    console.log('Contract terms being sent:', contractTerms.value)
    console.log('Contract clauses being sent:', contractClauses.value)
    console.log('Contract ID being used:', contractId)
    console.log('Contract ID type:', typeof contractId)
    
    // Validate required fields before sending
    if (!amendmentData.contract_title) {
      throw new Error('Contract title is required')
    }
    if (!amendmentData.contract_type) {
      throw new Error('Contract type is required')
    }
    if (!amendmentData.start_date) {
      throw new Error('Start date is required')
    }
    if (!amendmentData.end_date) {
      throw new Error('End date is required')
    }
    
    console.log('✅ All required fields validated')

    const response = await contractsApi.createContractAmendment(contractId, amendmentData)
    console.log('✅ API call successful:', response)
    
    if (response.success !== false) {
      // Show success message and risk analysis notification
      successMessage.value = `Contract amendment created successfully as version ${newVersionNumber}!`
      showRiskAnalysisNotification.value = true
      
      // Get the new amendment's contract ID from the response
      // The response structure is: { success: true, data: { contract: { contract_id: ... }, amendment: { ... } } }
      const amendmentContractId = response.data?.contract?.contract_id || response.data?.contract_id || response.data?.id || response.contract_id
      
      console.log('🔍 Amendment creation response:', response)
      console.log('🔍 Response data structure:', response.data)
      console.log('🔍 Contract data:', response.data?.contract)
      console.log('🔍 Amendment contract ID:', amendmentContractId)
      console.log('🔍 Parent contract ID:', contractId)
      
      // Trigger risk analysis for the amendment - this should always work if amendment was created successfully
      if (amendmentContractId) {
        console.log(`🔄 Triggering risk analysis for NEW AMENDMENT with ID: ${amendmentContractId}`)
        triggerRiskAnalysis(amendmentContractId)
      } else {
        console.error('❌ CRITICAL: Amendment created but no contract ID returned!')
        console.error('❌ Response data:', response.data)
        console.error('❌ Full response:', response)
        // This should not happen - if it does, there's a backend issue
        throw new Error('Amendment created but no contract ID returned from server')
      }
      
      // Navigate to contract comparison page after a short delay to allow user to see notifications
      setTimeout(() => {
        router.push({
          path: '/contract-comparison',
          query: {
            originalId: contractId,
            amendmentId: amendmentContractId
          }
        })
      }, 2000)
    } else {
      throw new Error(response.message || 'Failed to create contract amendment')
    }
  } catch (error) {
    console.error('Error creating amendment:', error)
    console.error('Error details:', {
      message: error.message,
      response: error.response?.data,
      status: error.response?.status,
      statusText: error.response?.statusText
    })
    successMessage.value = ''
    errors.value.general = error.message || 'Failed to create contract amendment'
  } finally {
    saving.value = false
  }
}

// Computed properties for comparison
const addedTerms = computed(() => {
  return contractTerms.value.filter(term => 
    !originalContractTerms.value.some(original => 
      original.term_id === term.term_id || 
      (original.term_title === term.term_title && original.term_category === term.term_category)
    )
  )
})

const modifiedTerms = computed(() => {
  return contractTerms.value
    .map(term => {
      const original = originalContractTerms.value.find(orig => 
        orig.term_id === term.term_id || 
        (orig.term_title === term.term_title && orig.term_category === term.term_category)
      )
      
      if (original && (
        original.term_text !== term.term_text ||
        original.risk_level !== term.risk_level ||
        original.compliance_status !== term.compliance_status ||
        original.approval_status !== term.approval_status
      )) {
        return {
          ...term,
          original,
          modified: term
        }
      }
      return null
    })
    .filter(Boolean)
})

const removedTerms = computed(() => {
  return originalContractTerms.value.filter(original => 
    !contractTerms.value.some(term => 
      term.term_id === original.term_id || 
      (term.term_title === original.term_title && term.term_category === original.term_category)
    )
  )
})

const addedClauses = computed(() => {
  return contractClauses.value.filter(clause => 
    !originalContractClauses.value.some(original => 
      original.clause_id === clause.clause_id || 
      (original.clause_name === clause.clause_name && original.clause_type === clause.clause_type)
    )
  )
})

const modifiedClauses = computed(() => {
  return contractClauses.value
    .map(clause => {
      const original = originalContractClauses.value.find(orig => 
        orig.clause_id === clause.clause_id || 
        (orig.clause_name === clause.clause_name && orig.clause_type === clause.clause_type)
      )
      
      if (original && (
        original.clause_text !== clause.clause_text ||
        original.risk_level !== clause.risk_level ||
        original.clause_type !== clause.clause_type
      )) {
        return {
          ...clause,
          original,
          modified: clause
        }
      }
      return null
    })
    .filter(Boolean)
})

const removedClauses = computed(() => {
  return originalContractClauses.value.filter(original => 
    !contractClauses.value.some(clause => 
      clause.clause_id === original.clause_id || 
      (clause.clause_name === original.clause_name && clause.clause_type === original.clause_type)
    )
  )
})

// Helper methods for comparison
const getOriginalValue = (key) => {
  const value = originalContractData.value[key]
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'object') return JSON.stringify(value)
  return value.toString()
}

const getAmendmentValue = (key) => {
  const value = formData.value[key]
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'object') return JSON.stringify(value)
  return value.toString()
}

// Download comparison report
const downloadComparisonReport = () => {
  try {
    const report = {
      contractId: contractId,
      amendmentNumber: amendmentForm.value.amendment_number,
      amendmentDate: amendmentForm.value.amendment_date,
      effectiveDate: amendmentForm.value.effective_date,
      comparisonDate: new Date().toISOString(),
      contractChanges: contractComparisonFields.value.map(field => ({
        field: field.label,
        original: getOriginalValue(field.key),
        amendment: getAmendmentValue(field.key),
        changed: getOriginalValue(field.key) !== getAmendmentValue(field.key)
      })).filter(change => change.changed),
      termsChanges: {
        added: addedTerms.value.length,
        modified: modifiedTerms.value.length,
        removed: removedTerms.value.length,
        details: {
          added: addedTerms.value,
          modified: modifiedTerms.value,
          removed: removedTerms.value
        }
      },
      clausesChanges: {
        added: addedClauses.value.length,
        modified: modifiedClauses.value.length,
        removed: removedClauses.value.length,
        details: {
          added: addedClauses.value,
          modified: modifiedClauses.value,
          removed: removedClauses.value
        }
      }
    }

    const dataStr = JSON.stringify(report, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = `contract-amendment-comparison-${contractId}-${amendmentForm.value.amendment_number || 'draft'}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    console.log('✅ Comparison report downloaded successfully')
  } catch (error) {
    console.error('❌ Error downloading comparison report:', error)
    PopupService.error('Error downloading comparison report: ' + error.message, 'Download Error')
  }
}

// Initialize component
onMounted(async () => {
  try {
    await Promise.all([
      loadUsers(),
      loadVendors(),
      loadLegalReviewers(),
      loadOriginalContract()
    ])

    const draftDataRaw = sessionStorage.getItem('amendment_draft_data')
    if (draftDataRaw) {
      try {
        const draftData = JSON.parse(draftDataRaw)
        if (draftData.formData) {
          formData.value = { ...formData.value, ...draftData.formData }
        }
        if (draftData.amendmentForm) {
          amendmentForm.value = { ...amendmentForm.value, ...draftData.amendmentForm }
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
        sessionStorage.removeItem('amendment_draft_data')

        if (contractTerms.value.length > 0) {
          loadTermQuestionnaires()
          contractTerms.value.forEach(term => {
            if (term.term_category && term.term_id) {
              loadTemplatesForTerm(term)
            }
          })
        }
      } catch (error) {
        console.error('Error restoring amendment draft data:', error)
      }
    }
  } finally {
    loading.value = false
  }
})
</script>
