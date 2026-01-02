<template>
  <!-- Main Content -->
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <Button variant="ghost" size="icon" @click="go('/contracts')">
          <ArrowLeft class="w-4 h-4" />
        </Button>
        <div>
          <h1 class="text-3xl font-bold text-foreground">{{ contractId ? 'Edit Contract' : 'Create New Contract' }}</h1>
          <p class="text-muted-foreground">{{ contractId ? 'Modify the contract details and terms' : 'Fill in the contract details and terms' }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button @click="() => { console.log('OCR button clicked, current showOCR:', showOCR); showOCR = !showOCR; console.log('showOCR after toggle:', showOCR); }" class="inline-flex items-center gap-2 px-4 py-2 border border-input bg-background hover:bg-accent hover:text-accent-foreground rounded-md">
          <Upload class="w-4 h-4" />
          OCR Upload
        </button>
        <Button variant="outline" @click="handleCreateSubcontract" class="gap-2" :type="'button'">
          <FileText class="w-4 h-4" />
          Create Subcontract
        </Button>
        <Button variant="outline" @click="handleSaveDraft" :disabled="isLoading" class="gap-2" :type="'button'">
          <Save class="w-4 h-4" />
          {{ isLoading ? 'Saving...' : 'Save Draft' }}
        </Button>
        <Button @click="handleSubmitForReview" :disabled="isLoading || isSubmitting" class="gap-2" :type="'button'">
          <Send class="w-4 h-4" />
          {{ isLoading || isSubmitting ? 'Processing...' : 'Preview & Submit' }}
        </Button>
        <Button @click="clearSessionStorage" variant="outline" class="gap-2 text-xs">
          <Trash2 class="w-4 h-4" />
          Clear Session
        </Button>
      </div>
    </div>


    <!-- Info Banner -->
    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <div class="flex items-start gap-3">
        <div class="w-5 h-5 text-blue-600 mt-0.5">
          <svg fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
          </svg>
              </div>
              <div>
          <h3 class="text-sm font-medium text-blue-800">Contract & Subcontract Workflow</h3>
          <p class="text-sm text-blue-700 mt-1">
            <strong>Create Subcontract:</strong> Saves this main contract as draft and opens subcontract creation page.<br>
            <strong>Submit for Review:</strong> Creates a preview where you can submit both contracts together for approval.
                </p>
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


    <!-- OCR Upload Section -->
    <Card v-if="showOCR">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <Upload class="w-5 h-5" />
          OCR Document Upload
        </CardTitle>
        <CardDescription>
          Upload a contract document to auto-populate fields using OCR
        </CardDescription>
      </CardHeader>
      <CardContent>
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
          <h3 class="text-lg font-semibold mb-2">Upload Contract Document</h3>
          <p class="text-muted-foreground mb-4">
            Supports PDF, PNG, JPG, TIFF files up to 10MB
          </p>
          <p class="text-sm text-muted-foreground mb-4">
            Drag and drop a file here or click the button below
          </p>
          <div class="relative inline-block">
            <input
              ref="fileInput"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.tiff"
              @change="handleFileUpload"
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
            />
            <Button @click="triggerFileInput" class="gap-2 relative">
              <Upload class="w-4 h-4" />
              Choose File
            </Button>
          </div>
          <div v-if="errors.ocr" class="mt-2 text-sm text-red-500">
            {{ errors.ocr }}
          </div>
        </div>

        <div v-if="uploadStep === 'processing'" class="space-y-4">
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span>Processing: {{ selectedFile?.name }}</span>
              <span>{{ uploadProgress }}%</span>
            </div>
            <Progress :value="uploadProgress" class="w-full" />
          </div>
          <div class="text-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p class="text-muted-foreground">
              Uploading to cloud storage and analyzing document...
            </p>
            <div class="mt-4 space-y-2 text-sm text-muted-foreground">
              <div class="flex items-center justify-center gap-2">
                <div class="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span>Uploading to S3 storage</span>
              </div>
              <div class="flex items-center justify-center gap-2">
                <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Extracting text with OCR</span>
              </div>
              <div class="flex items-center justify-center gap-2">
                <div class="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                <span>Analyzing contract data with AI</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="uploadStep === 'review'" class="space-y-4">
          <!-- S3 Upload Status -->
          <div v-if="s3UploadInfo" class="p-4 border rounded-lg" :class="s3UploadInfo.success ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'">
            <div class="flex items-center gap-2">
              <div v-if="s3UploadInfo.success" class="w-5 h-5 text-green-600">
                <svg fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
              </div>
              <div v-else class="w-5 h-5 text-yellow-600">
                <svg fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
                </svg>
              </div>
              <div>
                <h4 class="font-medium" :class="s3UploadInfo.success ? 'text-green-800' : 'text-yellow-800'">
                  {{ s3UploadInfo.success ? 'Document Stored Successfully' : 'Storage Notice' }}
                </h4>
                <p class="text-sm" :class="s3UploadInfo.success ? 'text-green-600' : 'text-yellow-600'">
                  {{ s3UploadInfo.success ? 'Your document has been securely uploaded to cloud storage.' : s3UploadInfo.error || 'Cloud storage is temporarily unavailable.' }}
                </p>
                <div v-if="!s3UploadInfo.success" class="mt-2 p-2 bg-yellow-100 rounded text-xs text-yellow-800">
                  <strong>Note:</strong> Your document has been processed successfully. You can still proceed with contract creation.
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
                  v-if="result.field === 'contract_value' || result.field === 'liability_cap'"
                  type="number"
                  :value="result.value"
                  @input="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter amount (e.g., 150000)"
                />
                
                <!-- Date fields -->
                <input
                  v-else-if="result.field === 'start_date' || result.field === 'end_date'"
                  type="date"
                  :value="result.value"
                  @input="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                
                <!-- Notice Period -->
                <input
                  v-else-if="result.field === 'notice_period_days'"
                  type="number"
                  :value="result.value"
                  @input="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter number of days"
                />
                
                <!-- Auto Renewal -->
                <select
                  v-else-if="result.field === 'auto_renewal'"
                  :value="result.value"
                  @change="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
                
                <!-- Priority -->
                <select
                  v-else-if="result.field === 'priority'"
                  :value="result.value"
                  @change="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
                
                <!-- Contract Type -->
                <select
                  v-else-if="result.field === 'contract_type'"
                  :value="result.value"
                  @change="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="MASTER_AGREEMENT">Master Agreement</option>
                  <option value="SOW">Statement of Work (SOW)</option>
                  <option value="PURCHASE_ORDER">Purchase Order</option>
                  <option value="SERVICE_AGREEMENT">Service Agreement</option>
                  <option value="LICENSE">License</option>
                  <option value="NDA">Non-Disclosure Agreement (NDA)</option>
                </select>
                
                <!-- Contract Category -->
                <select
                  v-else-if="result.field === 'contract_category'"
                  :value="result.value"
                  @change="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="goods">Goods</option>
                  <option value="services">Services</option>
                  <option value="technology">Technology</option>
                  <option value="consulting">Consulting</option>
                  <option value="others">Others</option>
                </select>
                
                <!-- Dispute Resolution -->
                <select
                  v-else-if="result.field === 'dispute_resolution_method'"
                  :value="result.value"
                  @change="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="negotiation">Negotiation</option>
                  <option value="mediation">Mediation</option>
                  <option value="arbitration">Arbitration</option>
                  <option value="litigation">Litigation</option>
                </select>
                
                <!-- Termination Clause -->
                <select
                  v-else-if="result.field === 'termination_clause_type'"
                  :value="result.value"
                  @change="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="convenience">Convenience</option>
                  <option value="cause">Cause</option>
                  <option value="both">Both</option>
                  <option value="none">None</option>
                </select>
                
                <!-- Compliance Status -->
                <select
                  v-else-if="result.field === 'compliance_status'"
                  :value="result.value"
                  @change="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="compliant">Compliant</option>
                  <option value="non_compliant">Non-Compliant</option>
                  <option value="under_review">Under Review</option>
                  <option value="exempt">Exempt</option>
                </select>
                
                <!-- Contract Risk Score -->
                <input
                  v-else-if="result.field === 'contract_risk_score'"
                  type="number"
                  step="0.1"
                  min="0"
                  max="10"
                  :value="result.value"
                  @input="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter risk score (0-10)"
                />
                
                <!-- Terms, Clauses, Renewal, Termination, Insurance, Data Protection -->
                <textarea
                  v-else-if="result.field.startsWith('term_') || result.field.startsWith('clause_') || result.field.startsWith('renewal_') || result.field.startsWith('termination_') || result.field.startsWith('insurance_') || result.field.startsWith('data_protection_') || result.field === 'renewal_terms'"
                  :value="result.value"
                  @input="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Enter detailed text..."
                ></textarea>
                
                <!-- Default text input -->
                <input
                  v-else
                  type="text"
                  :value="result.value"
                  @input="(e) => handleOCRValueChange(result.field, e.target.value)"
                  class="text-sm w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div class="ml-4">
                <Badge :class="getConfidenceBadge(result.confidence).class">
                  {{ getConfidenceBadge(result.confidence).text }}
                </Badge>
              </div>
            </div>
          </div>
          
          <div class="flex justify-between items-center pt-4 border-t">
            <div class="text-sm text-muted-foreground">
              {{ ocrResults.filter(r => r.needsReview).length }} fields need review
            </div>
            <div class="flex gap-2">
              <Button variant="outline" @click="showOCR = false">
                Cancel
              </Button>
              <Button @click="applyOCRData" class="gap-2">
                <CheckCircle class="w-4 h-4" />
                Apply to Form
              </Button>
              <Button variant="outline" @click="applyOCRDataWithClear" class="gap-2">
                <Trash2 class="w-4 h-4" />
                Clear & Apply
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Tabbed Form -->
    <Tabs v-model="activeTab" :key="formKey" class="space-y-6">
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
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <FileText class="w-5 h-5" />
              Primary Information
            </CardTitle>
            <CardDescription>
              Enter the fundamental contract details
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="contract_title">Contract Title *</Label>
                <Input
                  id="contract_title"
                  placeholder="e.g., Cloud Infrastructure Services Agreement"
                  :value="formData.contract_title"
                  @input="(e) => handleInputChange('contract_title', e.target.value)"
                  :class="errors.contract_title ? 'border-red-500' : ''"
                />
                <div v-if="errors.contract_title" class="text-sm text-red-500">{{ errors.contract_title }}</div>
              </div>
              
              <div class="space-y-2">
                <Label for="contract_number">Contract Number</Label>
                <Input
                  id="contract_number"
                  placeholder="e.g., CNT-2024-001"
                  :value="formData.contract_number"
                  @input="(e) => handleInputChange('contract_number', e.target.value)"
                />
              </div>

              <div class="space-y-2">
                <Label for="parent_contract_id">Parent Contract ID</Label>
                <Input
                  id="parent_contract_id"
                  placeholder="e.g., 1001 (optional)"
                  :value="formData.parent_contract_id"
                  @input="(e) => handleInputChange('parent_contract_id', e.target.value)"
                />
              </div>

              <div class="space-y-2">
                <Label for="contract_type">Contract Type *</Label>
                <Select :model-value="formData.contract_type" @update:model-value="(value) => handleInputChange('contract_type', value)" :key="`contract_type_${formKey}`">
                  <SelectTrigger :class="errors.contract_type ? 'border-red-500' : ''">
                    <SelectValue :placeholder="formData.contract_type || 'Select contract type'" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="MASTER_AGREEMENT">Master Agreement</SelectItem>
                    <SelectItem value="SOW">Statement of Work (SOW)</SelectItem>
                    <SelectItem value="PURCHASE_ORDER">Purchase Order</SelectItem>
                    <SelectItem value="SERVICE_AGREEMENT">Service Agreement</SelectItem>
                    <SelectItem value="LICENSE">License</SelectItem>
                    <SelectItem value="NDA">Non-Disclosure Agreement (NDA)</SelectItem>
                  </SelectContent>
                </Select>
                <div v-if="errors.contract_type" class="text-sm text-red-500">{{ errors.contract_type }}</div>
              </div>

              <div class="space-y-2">
                <Label for="priority">Priority *</Label>
                <Select :model-value="formData.priority" @update:model-value="(value) => handleInputChange('priority', value)" :key="`priority_${formKey}`">
                  <SelectTrigger>
                    <SelectValue :placeholder="formData.priority || 'Select priority'" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div class="space-y-2">
                <Label for="contract_category">Contract Category</Label>
                <Select :model-value="formData.contract_category" @update:model-value="(value) => handleInputChange('contract_category', value)" :key="`contract_category_${formKey}`">
                  <SelectTrigger>
                    <SelectValue :placeholder="formData.contract_category || 'Select category'" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="goods">Goods</SelectItem>
                    <SelectItem value="services">Services</SelectItem>
                    <SelectItem value="technology">Technology</SelectItem>
                    <SelectItem value="consulting">Consulting</SelectItem>
                    <SelectItem value="others">Others</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Building class="w-5 h-5" />
              Vendor Information
            </CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="vendor_id">Vendor *</Label>
                <Select :model-value="formData.vendor_id" :key="`vendor_id_${formKey}`" @update:model-value="(value) => {
                  handleInputChange('vendor_id', value)
                  const selectedVendor = vendors.find(v => v.vendor_id == value)
                  if (selectedVendor) {
                    formData.vendor_name = selectedVendor.company_name
                  }
                }">
                  <SelectTrigger :class="errors.vendor_id ? 'border-red-500' : ''">
                    <SelectValue placeholder="Select vendor" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="vendor in vendors" :key="vendor.vendor_id" :value="vendor.vendor_id">
                      {{ vendor.company_name }}
                    </SelectItem>
                  </SelectContent>
                </Select>
                <div v-if="errors.vendor_id" class="text-sm text-red-500">{{ errors.vendor_id }}</div>
              </div>
              
              <div class="space-y-2">
                <Label for="vendor_display">Selected Vendor</Label>
                <Input
                  id="vendor_display"
                  :value="formData.vendor_name"
                  placeholder="No vendor selected"
                  readonly
                  class="bg-gray-50"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Financial Tab -->
      <TabsContent value="financial" class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <DollarSign class="w-5 h-5" />
              Financial Details
            </CardTitle>
            <CardDescription>
              Set contract value and financial terms
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="contract_value">Contract Value *</Label>
                <Input
                  id="contract_value"
                  type="number"
                  step="0.01"
                  placeholder="250000"
                  :value="formData.contract_value"
                  @input="(e) => handleInputChange('contract_value', e.target.value)"
                  :class="errors.contract_value ? 'border-red-500' : ''"
                />
                <div v-if="errors.contract_value" class="text-sm text-red-500">{{ errors.contract_value }}</div>
              </div>
              
              <div class="space-y-2">
                <Label for="currency">Currency</Label>
                <Select :model-value="formData.currency" @update:model-value="(value) => handleInputChange('currency', value)">
                  <SelectTrigger>
                    <SelectValue placeholder="Select currency" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="USD">USD - US Dollar</SelectItem>
                    <SelectItem value="EUR">EUR - Euro</SelectItem>
                    <SelectItem value="GBP">GBP - British Pound</SelectItem>
                    <SelectItem value="CAD">CAD - Canadian Dollar</SelectItem>
                    <SelectItem value="AUD">AUD - Australian Dollar</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div class="space-y-2">
                <Label for="liability_cap">Liability Cap</Label>
                <Input
                  id="liability_cap"
                  type="number"
                  placeholder="e.g., 1000000"
                  :value="formData.liability_cap"
                  @input="(e) => handleInputChange('liability_cap', e.target.value)"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Dates & Terms Tab -->
      <TabsContent value="dates" class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Calendar class="w-5 h-5" />
              Dates & Terms
            </CardTitle>
            <CardDescription>
              Define contract duration and renewal terms
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="start_date">Start Date *</Label>
                <Input
                  id="start_date"
                  type="date"
                  :value="formData.start_date"
                  @input="(e) => handleInputChange('start_date', e.target.value)"
                  :class="errors.start_date ? 'border-red-500' : ''"
                />
                <div v-if="errors.start_date" class="text-sm text-red-500">{{ errors.start_date }}</div>
              </div>
              
              <div class="space-y-2">
                <Label for="end_date">End Date *</Label>
                <Input
                  id="end_date"
                  type="date"
                  :value="formData.end_date"
                  @input="(e) => handleInputChange('end_date', e.target.value)"
                  :class="errors.end_date ? 'border-red-500' : ''"
                />
                <div v-if="errors.end_date" class="text-sm text-red-500">{{ errors.end_date }}</div>
              </div>

              <div class="space-y-2">
                <Label for="notice_period_days">Notice Period (Days)</Label>
                <Input
                  id="notice_period_days"
                  type="number"
                  placeholder="30"
                  :value="formData.notice_period_days"
                  @input="(e) => handleInputChange('notice_period_days', parseInt(e.target.value))"
                />
              </div>
            </div>

          </CardContent>
        </Card>
      </TabsContent>

      <!-- Stakeholders Tab -->
      <TabsContent value="stakeholders" class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Stakeholders & Responsibilities</CardTitle>
            <CardDescription>
              Assign contract ownership and reviewers
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="contract_owner">Contract Owner *</Label>
                <Select v-model="formData.contract_owner" @update:model-value="(value) => handleInputChange('contract_owner', parseInt(value))">
                  <SelectTrigger :class="errors.contract_owner ? 'border-red-500' : ''">
                    <SelectValue placeholder="Select contract owner" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="user in users" :key="user.user_id" :value="user.user_id">
                      {{ user.display_name }} (ID: {{ user.user_id }})
                    </SelectItem>
                  </SelectContent>
                </Select>
                <div v-if="errors.contract_owner" class="text-sm text-red-500">{{ errors.contract_owner }}</div>
                <div class="text-sm text-gray-500">Select the user who will own this contract</div>
              </div>
              
              <div class="space-y-2">
                <Label for="legal_reviewer">Legal Reviewer</Label>
                <Select v-model="formData.legal_reviewer" @update:model-value="(value) => handleInputChange('legal_reviewer', parseInt(value))">
                  <SelectTrigger>
                    <SelectValue placeholder="Select legal reviewer" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="reviewer in legalReviewers" :key="reviewer.user_id" :value="reviewer.user_id">
                      {{ reviewer.display_name }} (ID: {{ reviewer.user_id }})
                    </SelectItem>
                  </SelectContent>
                </Select>
                <div class="text-sm text-gray-500">Select a user with legal review permissions</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Compliance Tab -->
      <TabsContent value="compliance" class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Shield class="w-5 h-5" />
              Compliance & Frameworks
            </CardTitle>
            <CardDescription>
              Select applicable compliance frameworks
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="space-y-3">
              <Label for="compliance_framework">Compliance Framework</Label>
              <Select v-model="formData.compliance_framework">
                <SelectTrigger>
                  <SelectValue placeholder="Select compliance framework" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="SOC2">SOC2</SelectItem>
                  <SelectItem value="GDPR">GDPR</SelectItem>
                  <SelectItem value="CCPA">CCPA</SelectItem>
                  <SelectItem value="ISO27001">ISO27001</SelectItem>
                  <SelectItem value="PCI DSS">PCI DSS</SelectItem>
                  <SelectItem value="HIPAA">HIPAA</SelectItem>
                  <SelectItem value="Other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Contract Terms Tab -->
      <TabsContent value="terms" class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <FileCheck class="w-5 h-5" />
              Contract Terms
            </CardTitle>
            <CardDescription>
              Define and manage contract terms with risk assessment
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium">Terms List ({{ contractTerms.length }} terms)</h3>
              <div class="flex gap-2">
                <Button 
                  variant="outline"
                  @click="debugTerms"
                  class="gap-2"
                >
                  <Search class="w-4 h-4" />
                  Debug Terms
                </Button>
              <Button 
                @click="addNewTerm"
                class="gap-2"
              >
                <Plus class="w-4 h-4" />
                Add Term
              </Button>
              </div>
            </div>
            
            <!-- Debug info -->
            <div v-if="contractTerms.length > 0" class="text-xs text-gray-500 bg-gray-100 p-2 rounded">
              Debug: {{ contractTerms.length }} terms loaded. First term: {{ contractTerms[0]?.term_title || 'No title' }}
            </div>
            
            <div class="space-y-4">
              <div v-for="(term, index) in contractTerms" :key="term?.term_id || `term-${index}`" class="border rounded p-4">
                <div class="space-y-4">
                  <div class="flex items-center justify-between">
                    <h4 class="font-medium">Term #{{ index + 1 }}</h4>
                    <Button
                      variant="outline"
                      size="sm"
                      @click="removeTerm(index)"
                      class="gap-2"
                    >
                      <Trash2 class="w-4 h-4" />
                    </Button>
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                      <Label>Term Category</Label>
                                             <Select 
                         :model-value="String(term.term_category || '')"
                       @update:model-value="async (value) => {
                           if (term) {
                             term.term_category = value;
                             // Auto-load templates when category is selected
                             if (value && term.term_id) {
                               console.log(`🔄 Term category changed to ${value}, loading templates...`)
                               await loadTemplatesForTerm(term)
                             }
                           }
                         }"
                       >
                         <SelectTrigger>
                           <SelectValue :placeholder="term?.term_category || 'Select category'" />
                         </SelectTrigger>
                         <SelectContent>
                           <SelectItem value="Payment">Payment</SelectItem>
                           <SelectItem value="Delivery">Delivery</SelectItem>
                           <SelectItem value="Performance">Performance</SelectItem>
                           <SelectItem value="Liability">Liability</SelectItem>
                           <SelectItem value="Termination">Termination</SelectItem>
                           <SelectItem value="Intellectual Property">Intellectual Property</SelectItem>
                           <SelectItem value="Confidentiality">Confidentiality</SelectItem>
                         </SelectContent>
                       </Select>
                    </div>
                    
                    <div class="space-y-2">
                      <Label>Term Title</Label>
                      <Input
                        :value="term.term_title"
                        @input="(event) => {
                          // Force update the reactive object
                          term.term_title = event.target.value;
                          console.log(`✏️ Term ${index + 1} title updated:`, event.target.value);
                          console.log('📋 Current term_title:', term.term_title);
                        }"
                        placeholder="e.g., Payment Schedule"
                      />
                     </div>
                  </div>

                  <div class="space-y-2">
                    <Label>Term Text</Label>
                    <Textarea
                      :value="term.term_text"
                      @input="(event) => {
                        // Force update the reactive object
                        term.term_text = event.target.value;
                        console.log(`✏️ Term ${index + 1} text updated:`, event.target.value);
                        console.log('📋 Current term_text:', term.term_text);
                        console.log('📋 Full term object:', JSON.stringify(term, null, 2));
                      }"
                      placeholder="Enter the detailed term text..."
                      :rows="3"
                    />
                  </div>

                  <div class="flex items-center space-x-2">
                    <Checkbox
                      :id="`standard_${index}`"
                      :checked="term?.is_standard || false"
                      @update:checked="(checked) => {
                        if (term) {
                          term.is_standard = checked;
                          console.log(`✏️ Term ${index + 1} is_standard updated:`, checked);
                          
                          // Force reactivity update
                          if (Array.isArray(contractTerms.value)) {
                            contractTerms.value = [...contractTerms.value];
                          }
                        }
                      }"
                    />
                    <Label :for="`standard_${index}`">Standard Term</Label>
                  </div>

                  <!-- Templates Section -->
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
                            {{ hasQuestionnaires(term.term_title, term.term_id) ? `${getQuestionnaireCount(term.term_title, term.term_id)} questions` : 'No questions yet' }}
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
                            <Button 
                              variant="outline" 
                              size="sm" 
                              @click="loadTemplatesForTerm(term)"
                              class="gap-2"
                            >
                              <Search class="w-4 h-4" />
                              Load Templates
                            </Button>
                            <Button 
                              variant="outline" 
                              size="sm" 
                              @click="createQuestionnaires(term.term_title, term.term_id)"
                              class="gap-2"
                            >
                              <Plus class="w-4 h-4" />
                              Create New Template
                            </Button>
                            <Button 
                              v-if="hasQuestionnaires(term.term_title, term.term_id)"
                              variant="outline" 
                              size="sm" 
                              @click="viewQuestionnaires(term.term_title, term.term_id)"
                              class="gap-2"
                            >
                              <FileText class="w-4 h-4" />
                              View {{ getQuestionnaireCount(term.term_title, term.term_id) }} Questions
                            </Button>
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
                              <Button 
                                variant="outline" 
                                size="sm" 
                                @click="viewTemplateQuestions(term.term_id, getSelectedTemplateForTerm(term.term_id)?.template_id)"
                                class="gap-1"
                              >
                                <FileText class="w-4 h-4" />
                                View
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm" 
                                @click="clearTemplateSelection(term.term_id)"
                              >
                                <X class="w-4 h-4" />
                              </Button>
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
                                <Button 
                                  variant="outline" 
                                  size="sm" 
                                  @click.stop="viewTemplateQuestions(term.term_id, template.template_id)"
                                  class="gap-1"
                                >
                                  <FileText class="w-4 h-4" />
                                  Preview
                                </Button>
                                <div v-if="getSelectedTemplateForTerm(term.term_id)?.template_id === template.template_id" class="w-5 h-5 rounded-full bg-blue-600 flex items-center justify-center">
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
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Contract Clauses Tab -->
      <TabsContent value="clauses" class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <FileText class="w-5 h-5" />
              Contract Clauses Library
            </CardTitle>
            <CardDescription>
              Manage standardized contract clauses
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium">Clauses List ({{ contractClauses.length }} clauses)</h3>
              <div class="flex gap-2">
                <Button 
                  variant="outline"
                  @click="debugClauses"
                  class="gap-2"
                >
                  <Search class="w-4 h-4" />
                  Debug Clauses
                </Button>
              <Button 
                @click="addNewClause"
                class="gap-2"
              >
                <Plus class="w-4 h-4" />
                Add Clause
              </Button>
              </div>
            </div>
            
            <!-- Debug info -->
            <div v-if="contractClauses.length > 0" class="text-xs text-gray-500 bg-gray-100 p-2 rounded">
              Debug: {{ contractClauses.length }} clauses loaded. First clause: {{ contractClauses[0]?.clause_name || 'No name' }}
            </div>
            
            <div class="space-y-4">
              <div v-for="(clause, index) in contractClauses" :key="clause?.clause_id || `clause-${index}`" class="border rounded p-4">
                <div class="space-y-4">
                  <div class="flex items-center justify-between">
                    <h4 class="font-medium">Clause #{{ index + 1 }}</h4>
                    <Button
                      variant="outline"
                      size="sm"
                      @click="removeClause(clause.clause_id)"
                      class="gap-2"
                    >
                      <Trash2 class="w-4 h-4" />
                    </Button>
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                      <Label>Clause Name *</Label>
                      <Input
                        :value="clause.clause_name"
                        @input="(event) => {
                          // Force update the reactive object
                          clause.clause_name = event.target.value;
                          console.log(`✏️ Clause ${index + 1} name updated:`, event.target.value);
                          console.log('📋 Current clause_name:', clause.clause_name);
                          
                          // Force reactivity update - ensure contractClauses is an array
                          if (Array.isArray(contractClauses.value)) {
                            contractClauses.value = [...contractClauses.value];
                          } else {
                            console.warn('contractClauses.value is not an array:', contractClauses.value);
                            contractClauses.value = [];
                          }
                        }"
                        placeholder="e.g., Limitation of Liability"
                      />
                    </div>
                    
                                         <div class="space-y-2">
                       <Label>Clause Type</Label>
                       <Select 
                         :model-value="String(clause.clause_type || 'standard')"
                         @update:model-value="(value) => {
                           if (Array.isArray(contractClauses.value)) {
                           const updatedClauses = [...contractClauses.value];
                           updatedClauses[index].clause_type = value;
                           contractClauses.value = updatedClauses;
                           } else {
                             console.warn('contractClauses.value is not an array for clause_type update:', contractClauses.value);
                           }
                         }"
                       >
                         <SelectTrigger>
                           <SelectValue :placeholder="clause.clause_type || 'Select type'" />
                         </SelectTrigger>
                         <SelectContent>
                           <SelectItem value="standard">Standard</SelectItem>
                           <SelectItem value="risk">Risk</SelectItem>
                           <SelectItem value="compliance">Compliance</SelectItem>
                           <SelectItem value="financial">Financial</SelectItem>
                           <SelectItem value="operational">Operational</SelectItem>
                           <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div class="space-y-2">
                      <Label>Legal Category</Label>
                      <Input
                        :value="clause.legal_category"
                        @input="(event) => {
                          // Force update the reactive object
                          clause.legal_category = event.target.value;
                          console.log(`✏️ Clause ${index + 1} legal category updated:`, event.target.value);
                        }"
                        placeholder="e.g., Commercial Law"
                      />
                    </div>
                  </div>

                  <div class="space-y-2">
                    <Label>Clause Text *</Label>
                    <Textarea
                      :value="clause.clause_text"
                      @input="(event) => {
                        // Force update the reactive object
                        clause.clause_text = event.target.value;
                        console.log(`✏️ Clause ${index + 1} text updated:`, event.target.value);
                        console.log('📋 Current clause_text:', clause.clause_text);
                        console.log('📋 Full clause object:', JSON.stringify(clause, null, 2));
                        
                        // Force reactivity update - ensure contractClauses is an array
                        if (Array.isArray(contractClauses.value)) {
                          contractClauses.value = [...contractClauses.value];
                        } else {
                          console.warn('contractClauses.value is not an array:', contractClauses.value);
                          contractClauses.value = [];
                        }
                      }"
                      placeholder="Enter the detailed clause text..."
                      :rows="4"
                    />
                  </div>

                  <div class="flex items-center space-x-2">
                    <Checkbox
                      :id="`standard_clause_${index}`"
                      :checked="clause.is_standard"
                      @update:checked="(checked) => {
                        if (Array.isArray(contractClauses.value)) {
                        const updatedClauses = [...contractClauses.value];
                        updatedClauses[index].is_standard = checked;
                        contractClauses.value = updatedClauses;
                        } else {
                          console.warn('contractClauses.value is not an array for is_standard update:', contractClauses.value);
                        }
                      }"
                    />
                    <Label :for="`standard_clause_${index}`">Standard Clause</Label>
                  </div>
                </div>
              </div>
              
              <div v-if="contractClauses.length === 0" class="text-center py-8 text-muted-foreground">
                No contract clauses added yet. Click "Add Clause" to get started.
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Renewal Tab -->
      <TabsContent value="renewal" class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Calendar class="w-5 h-5" />
              Renewal Clauses
            </CardTitle>
            <CardDescription>
              Define contract renewal terms and conditions
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium">Renewal Clauses</h3>
              <Button 
                @click="addNewRenewalClause"
                class="gap-2"
              >
                <Plus class="w-4 h-4" />
                Add Renewal Clause
              </Button>
            </div>
            
            <div class="space-y-4">
              <div v-for="(clause, index) in (contractClauses || []).filter(c => c?.clause_type === 'renewal')" :key="clause?.clause_id || `renewal-${index}`" class="border rounded p-4">
                <div class="space-y-4">
                  <div class="flex items-center justify-between">
                    <h4 class="font-medium">Renewal Clause #{{ index + 1 }}</h4>
                    <Button
                      variant="outline"
                      size="sm"
                      @click="removeClause(clause.clause_id)"
                      class="gap-2"
                    >
                      <Trash2 class="w-4 h-4" />
                    </Button>
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                      <Label>Notice Period (Days)</Label>
                      <Input
                        type="number"
                        :value="clause.notice_period_days"
                        @input="(event) => {
                          // Force update the reactive object
                          clause.notice_period_days = parseInt(event.target.value) || null;
                          console.log(`✏️ Renewal clause ${index + 1} notice period updated:`, clause.notice_period_days);
                        }"
                        placeholder="30"
                      />
                    </div>
                  </div>

                  <div class="space-y-2">
                    <Label>Renewal Terms</Label>
                    <Textarea
                      :value="clause.renewal_terms"
                      @input="(event) => {
                        // Force update the reactive object
                        clause.renewal_terms = event.target.value;
                        clause.clause_text = event.target.value; // Sync with clause_text for backend
                        console.log(`✏️ Renewal clause ${index + 1} terms updated:`, event.target.value);
                        console.log(`📋 Synced clause_text:`, clause.clause_text);
                        
                        // Force reactivity update
                        if (Array.isArray(contractClauses.value)) {
                          contractClauses.value = [...contractClauses.value];
                        }
                      }"
                      placeholder="Enter the detailed renewal terms..."
                      :rows="4"
                    />
                  </div>

                  <div class="flex items-center space-x-2">
                    <Checkbox
                      :id="`auto_renew_${clause.clause_id}`"
                      :checked="clause?.auto_renew || false"
                      @update:checked="(checked) => {
                        if (clause) {
                          clause.auto_renew = checked;
                          console.log(`✏️ Renewal clause ${index + 1} auto-renew updated:`, checked);
                          
                          // Force reactivity update
                          if (Array.isArray(contractClauses.value)) {
                            contractClauses.value = [...contractClauses.value];
                          }
                        }
                      }"
                    />
                    <Label :for="`auto_renew_${clause.clause_id}`">Enable Auto-Renewal</Label>
                  </div>
                </div>
              </div>
              
              <div v-if="!contractClauses || !Array.isArray(contractClauses) || contractClauses.filter(c => c?.clause_type === 'renewal').length === 0" class="text-center py-8 text-muted-foreground">
                No renewal clauses added yet. Click "Add Renewal Clause" to get started.
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Termination Tab -->
      <TabsContent value="termination" class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <FileText class="w-5 h-5" />
              Termination Clauses
            </CardTitle>
            <CardDescription>
              Define contract termination conditions and penalties
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="flex justify-between items-center">
              <h3 class="text-lg font-medium">Termination Clauses</h3>
              <Button 
                @click="addNewTerminationClause"
                class="gap-2"
              >
                <Plus class="w-4 h-4" />
                Add Termination Clause
              </Button>
            </div>
            
            <div class="space-y-4">
              <div v-for="(clause, index) in (contractClauses || []).filter(c => c?.clause_type === 'termination')" :key="clause?.clause_id || `termination-${index}`" class="border rounded p-4">
                <div class="space-y-4">
                  <div class="flex items-center justify-between">
                    <h4 class="font-medium">Termination Clause #{{ index + 1 }}</h4>
                    <Button
                      variant="outline"
                      size="sm"
                      @click="removeClause(clause.clause_id)"
                      class="gap-2"
                    >
                      <Trash2 class="w-4 h-4" />
                    </Button>
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="space-y-2">
                      <Label>Notice Period (Days)</Label>
                      <Input
                        type="number"
                        :value="clause.termination_notice_period"
                        @input="(event) => {
                          // Force update the reactive object
                          clause.termination_notice_period = parseInt(event.target.value) || null;
                          console.log(`✏️ Termination clause ${index + 1} notice period updated:`, clause.termination_notice_period);
                        }"
                        placeholder="30"
                      />
                    </div>

                    <div class="space-y-2">
                      <Label>Early Termination Fee</Label>
                      <Input
                        type="number"
                        :value="clause.early_termination_fee"
                        @input="(event) => {
                          // Force update the reactive object
                          clause.early_termination_fee = parseFloat(event.target.value) || null;
                          console.log(`✏️ Termination clause ${index + 1} fee updated:`, clause.early_termination_fee);
                        }"
                        placeholder="0"
                      />
                    </div>
                  </div>

                  <div class="space-y-2">
                    <Label>Termination Conditions</Label>
                    <Textarea
                      :value="clause.termination_conditions"
                      @input="(event) => {
                        // Force update the reactive object
                        clause.termination_conditions = event.target.value;
                        clause.clause_text = event.target.value; // Sync with clause_text for backend
                        console.log(`✏️ Termination clause ${index + 1} conditions updated:`, event.target.value);
                        console.log(`📋 Synced clause_text:`, clause.clause_text);
                        
                        // Force reactivity update
                        if (Array.isArray(contractClauses.value)) {
                          contractClauses.value = [...contractClauses.value];
                        }
                      }"
                      placeholder="Enter the detailed termination conditions..."
                      :rows="4"
                    />
                  </div>
                </div>
              </div>
              
              <div v-if="!contractClauses || !Array.isArray(contractClauses) || contractClauses.filter(c => c?.clause_type === 'termination').length === 0" class="text-center py-8 text-muted-foreground">
                No termination clauses added yet. Click "Add Termination Clause" to get started.
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Legal Tab -->
      <TabsContent value="legal" class="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <Shield class="w-5 h-5" />
              Legal & Risk Management
            </CardTitle>
            <CardDescription>
              Legal terms, risk assessment, and dispute resolution
            </CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="dispute_resolution_method">Dispute Resolution</Label>
                <Select v-model="formData.dispute_resolution_method">
                  <SelectTrigger>
                    <SelectValue :placeholder="formData.dispute_resolution_method || 'Select resolution method'" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="negotiation">Negotiation</SelectItem>
                    <SelectItem value="mediation">Mediation</SelectItem>
                    <SelectItem value="arbitration">Arbitration</SelectItem>
                    <SelectItem value="litigation">Litigation</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div class="space-y-2">
                <Label for="governing_law">Governing Law</Label>
                <Input
                  id="governing_law"
                  placeholder="e.g., California, USA"
                  v-model="formData.governing_law"
                  @input="(e) => handleInputChange('governing_law', e.target.value)"
                />
              </div>

              <div class="space-y-2">
                <Label for="termination_clause_type">Termination Clause</Label>
                <Select v-model="formData.termination_clause_type">
                  <SelectTrigger>
                    <SelectValue :placeholder="formData.termination_clause_type || 'Select termination type'" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="convenience">Convenience</SelectItem>
                    <SelectItem value="cause">For Cause</SelectItem>
                    <SelectItem value="both">Both</SelectItem>
                    <SelectItem value="none">None</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  </div>

  <!-- Questionnaires Modal -->
  <div v-if="showQuestionnairesModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="closeQuestionnairesModal">
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden" @click.stop>
      <div class="flex items-center justify-between p-6 border-b">
        <h2 class="text-2xl font-bold">Questionnaires for "{{ selectedTermTitle || 'Unknown Term' }}"</h2>
        <button @click="closeQuestionnairesModal" class="text-gray-500 hover:text-gray-700">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div class="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
        <div class="space-y-4">
          <div v-for="(question, index) in selectedQuestionnaires" :key="question.question_id" class="border rounded-lg p-4 bg-gray-50">
            <div class="flex items-start justify-between mb-2">
              <div class="flex items-start gap-3 flex-1">
                <div class="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-white text-sm font-medium">
                  {{ index + 1 }}
                </div>
                <div class="flex-1">
                  <h3 class="font-medium text-lg mb-1">{{ question.question_text }}</h3>
                  <div class="flex items-center gap-4 text-sm text-muted-foreground">
                    <span class="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="9" x2="15" y2="9"/><line x1="9" y1="15" x2="15" y2="15"/>
                      </svg>
                      Type: <span class="font-medium capitalize">{{ question.question_type }}</span>
                    </span>
                    <span class="flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                      </svg>
                      Weight: <span class="font-medium">{{ question.scoring_weightings }}%</span>
                    </span>
                    <span v-if="question.is_required" class="flex items-center gap-1 text-red-600">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                      </svg>
                      Required
                    </span>
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
        <Button variant="outline" @click="closeQuestionnairesModal">Close</Button>
        <Button @click="editQuestionnaires(selectedTermTitle, selectedTermId, selectedQuestionnaires)">
          <Edit class="w-4 h-4 mr-2" />
          Edit Questionnaires
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, reactive, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Card, CardContent, CardDescription, CardHeader, CardTitle,
  Badge, Button, Input, Label, Textarea, Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
  Checkbox, Separator, Tabs, TabsContent, TabsList, TabsTrigger,
  Progress
} from '@/components/ui'
import { 
  ArrowLeft, Save, Send, FileText, Building, DollarSign, Calendar, 
  Shield, Upload, CheckCircle, AlertTriangle, Plus, Trash2, 
  FileCheck, Edit, Search, Filter, X, ChevronDown
} from 'lucide-vue-next'
import contractsApi from '@/services/contractsApi'
import apiService from '@/services/api'
import { getApiOrigin } from '@/utils/backendEnv'
import { PopupService } from '@/popup/popupService'

const router = useRouter()
const route = useRoute()
const go = (path) => router.push(path)

// Get contract ID from route params for editing
// IMPORTANT: Only use route.query.edit, never route.params.id (which might be "create")
// If route.params.id exists and equals "create", we're in create mode, not edit mode
const isCreateRoute = route.path === '/contracts/create' || route.path === '/contracts/new' || (route.params.id && route.params.id === 'create')
const contractId = !isCreateRoute && route.query.edit ? parseInt(route.query.edit) : null
console.log('🔍 Route path:', route.path)
console.log('🔍 Route query:', route.query)
console.log('🔍 Route params:', route.params)
console.log('🔍 Is create route:', isCreateRoute)
console.log('🔍 Contract ID for editing:', contractId)
console.log('🔍 Contract ID type:', typeof contractId)

// State
// Initialize activeTab from route query parameter, default to 'basic'
const activeTab = ref(route.query.tab || 'basic')
const showOCR = ref(false)
const formKey = ref(0) // Key to force form re-rendering
const fileInput = ref(null)
const isDragOver = ref(false)



const navigateToPreview = () => {
  console.log('👁️ Navigating to preview page')
  console.log('🔍 Current form data to store:', formData.value)
  console.log('🔍 Current contract terms to store:', contractTerms.value)
  console.log('🔍 Current contract clauses to store:', contractClauses.value)
  console.log('🔍 S3 file_path in formData:', formData.value?.file_path)
  
  // Ensure S3 URL is included in formData (check for fallback storage)
  if (!formData.value?.file_path) {
    const fallbackS3Url = sessionStorage.getItem('contractS3Url')
    if (fallbackS3Url && formData.value) {
      formData.value.file_path = fallbackS3Url
      console.log('💾 Retrieved S3 URL from session storage fallback in navigateToPreview:', fallbackS3Url)
      sessionStorage.removeItem('contractS3Url') // Clean up
    }
  }
  
  console.log('🔍 Final form data with file_path:', formData.value?.file_path)
  
  // Store contract data in session storage for the preview page
  const previewData = {
    contractData: formData.value,
    contractTerms: contractTerms.value,
    contractClauses: contractClauses.value,
    allTermQuestionnaires: allTermQuestionnaires.value, // Include questionnaires for preview page
    selectedTemplates: selectedTemplates.value, // IMPORTANT: Store selected templates so preview page knows which templates to use
    templateQuestionsCache: templateQuestionsCache.value // OPTIMIZATION: Pass cached template questions to avoid API calls in preview
  }
  
  console.log('💾 Storing preview data:', previewData)
  console.log('💾 S3 file_path in preview data:', previewData.contractData?.file_path)
  console.log(`💾 Storing ${allTermQuestionnaires.value.length} questionnaires for preview`)
  console.log(`💾 Storing selected templates:`, selectedTemplates.value)
  console.log(`💾 Storing ${Object.keys(templateQuestionsCache.value).length} cached template question sets`)
  sessionStorage.setItem('contractPreviewData', JSON.stringify(previewData))
  
  // Navigate to preview page
  router.push('/contracts/preview')
}
const uploadStep = ref('upload')
const uploadProgress = ref(0)
const selectedFile = ref(null)
const isLoading = ref(false)
const isSubmitting = ref(false)
const errors = ref({})
const successMessage = ref('')
const vendors = ref([])
const users = ref([])
const legalReviewers = ref([])
const s3UploadInfo = ref(null)

// Form data mapped to backend model structure
const formData = ref({
  // Basic Contract Information - mapped to VendorContract model
  contract_title: '',
  contract_number: '',
  contract_type: '',
  contract_kind: 'MAIN',
  contract_category: '',
  
  // Vendor Information
  vendor_id: null,
  vendor_name: '', // For display only
  
  // Financial Information
  contract_value: '',
  currency: 'USD',
  liability_cap: '',
  
  // Dates and Terms
  start_date: '',
  end_date: '',
  notice_period_days: 30,
  
  // Contract Status and Workflow
  status: 'PENDING_ASSIGNMENT',
  workflow_stage: 'under_review',
  priority: 'medium',
  compliance_status: 'under_review',
  
  // Legal and Risk Information
  dispute_resolution_method: '',
  governing_law: '',
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
  parent_contract_id: null,
  compliance_framework: '',
  
  // Hierarchy
  main_contract_id: null,
  
  // File Management
  file_path: '' // S3 URL for uploaded contract document
})

// Contract terms and clauses - initialize as empty arrays
const contractTerms = ref([])
const contractClauses = ref([])

// Watch for showOCR changes to reset OCR state when closing
watch(showOCR, (newValue, oldValue) => {
  console.log('🔍 showOCR watcher triggered:', { oldValue, newValue })
  if (!newValue) {
    console.log('🔄 Resetting OCR state because showOCR became false')
    // Reset OCR state when closing
    uploadStep.value = 'upload'
    uploadProgress.value = 0
    selectedFile.value = null
    isDragOver.value = false
    s3UploadInfo.value = null
    if (errors.value.ocr) {
      delete errors.value.ocr
    }
    // Reset file input
    if (fileInput.value) {
      fileInput.value.value = ''
    }
    console.log('✅ OCR state reset completed')
  }
})

// OCR results with comprehensive contract fields mapping to database schema
const ocrResults = ref([
  // Basic Contract Information (vendor_contracts table)
  { field: 'contract_title', value: 'Software License Agreement', confidence: 95, needsReview: false },
  { field: 'contract_number', value: 'CNT-2024-001', confidence: 98, needsReview: false },
  { field: 'contract_type', value: 'SERVICE_AGREEMENT', confidence: 88, needsReview: false },
  { field: 'contract_kind', value: 'MAIN', confidence: 95, needsReview: false },
  { field: 'contract_category', value: 'technology', confidence: 92, needsReview: false },
  
  // Vendor Information
  { field: 'vendor_id', value: '1', confidence: 85, needsReview: true },
  { field: 'vendor_name', value: 'TechSoft Solutions Inc.', confidence: 98, needsReview: false },
  
  // Financial Information
  { field: 'contract_value', value: '150000', confidence: 85, needsReview: true },
  { field: 'currency', value: 'USD', confidence: 98, needsReview: false },
  { field: 'liability_cap', value: '1000000', confidence: 78, needsReview: true },
  
  // Dates and Terms
  { field: 'start_date', value: '2024-01-15', confidence: 92, needsReview: false },
  { field: 'end_date', value: '2025-01-14', confidence: 90, needsReview: false },
  { field: 'notice_period_days', value: '30', confidence: 87, needsReview: false },
  { field: 'auto_renewal', value: 'false', confidence: 85, needsReview: true },
  { field: 'renewal_terms', value: 'Renewal for 12 months with 30 days notice', confidence: 82, needsReview: true },
  
  // Contract Status and Workflow
  { field: 'status', value: 'PENDING_ASSIGNMENT', confidence: 95, needsReview: false },
  { field: 'workflow_stage', value: 'under_review', confidence: 95, needsReview: false },
  { field: 'priority', value: 'medium', confidence: 85, needsReview: true },
  { field: 'compliance_status', value: 'under_review', confidence: 90, needsReview: false },
  
  // Legal and Risk Information
  { field: 'dispute_resolution_method', value: 'arbitration', confidence: 80, needsReview: true },
  { field: 'governing_law', value: 'California, USA', confidence: 88, needsReview: false },
  { field: 'termination_clause_type', value: 'convenience', confidence: 85, needsReview: true },
  { field: 'contract_risk_score', value: '6.5', confidence: 75, needsReview: true },
  
  // Assignment and Ownership
  { field: 'contract_owner', value: '1', confidence: 90, needsReview: false },
  { field: 'legal_reviewer', value: '2', confidence: 88, needsReview: false },
  { field: 'assigned_to', value: '1', confidence: 85, needsReview: true },
  
  // Compliance
  { field: 'compliance_framework', value: 'SOC2', confidence: 82, needsReview: true },
  
  // Contract Terms (contract_terms table) - Using only valid term categories
  { field: 'term_Payment', value: 'Payment due within 30 days of invoice receipt', confidence: 92, needsReview: false },
  { field: 'term_Delivery', value: 'All deliverables must meet acceptance criteria as defined in the statement of work', confidence: 88, needsReview: false },
  { field: 'term_Performance', value: 'All work must meet industry best practices and quality standards', confidence: 90, needsReview: false },
  { field: 'term_Liability', value: 'Vendor shall maintain 99.9% uptime and respond to issues within 4 hours', confidence: 87, needsReview: false },
  { field: 'term_Intellectual_Property', value: 'Client retains ownership of all deliverables and intellectual property', confidence: 85, needsReview: true },
  { field: 'term_Confidentiality', value: 'All confidential information shall be protected and not disclosed to third parties', confidence: 94, needsReview: false },
  { field: 'term_Termination', value: 'Either party may terminate this contract with 30 days written notice', confidence: 88, needsReview: false },
  
  // Contract Clauses (contract_clauses table)
  { field: 'clause_Limitation_of_Liability', value: 'Vendor\'s liability shall be limited to the contract value and shall not exceed $1,000,000', confidence: 92, needsReview: false },
  { field: 'clause_Confidentiality', value: 'Both parties agree to maintain confidentiality of all proprietary information', confidence: 94, needsReview: false },
  { field: 'clause_Force_Majeure', value: 'Neither party shall be liable for delays or failures due to circumstances beyond their control', confidence: 87, needsReview: false },
  { field: 'clause_Indemnification', value: 'Vendor shall indemnify and hold harmless client against all claims arising from vendor\'s negligence', confidence: 89, needsReview: true },
  { field: 'clause_Data_Protection', value: 'Vendor shall comply with all applicable data protection laws and regulations', confidence: 91, needsReview: false },
  { field: 'clause_Service_Level_Agreement', value: 'Vendor shall meet service level targets as defined in the SLA appendix', confidence: 86, needsReview: false },
  
  // Renewal Clauses (contract_clauses with clause_type='renewal')
  { field: 'renewal_Notice_Period', value: 'Either party may terminate this agreement with 30 days written notice prior to expiration', confidence: 88, needsReview: false },
  { field: 'renewal_Term_Length', value: 'Contract may be renewed for additional 12-month periods with same terms and conditions', confidence: 85, needsReview: true },
  { field: 'renewal_Pricing_Adjustment', value: 'Pricing may be adjusted annually based on market rates and inflation index', confidence: 82, needsReview: true },
  { field: 'renewal_Auto_Extension', value: 'Contract shall automatically extend for one year unless terminated with proper notice', confidence: 90, needsReview: false },
  
  // Termination Clauses (contract_clauses with clause_type='termination')
  { field: 'termination_Notice_Period', value: 'Either party may terminate this agreement with 60 days written notice for convenience', confidence: 92, needsReview: false },
  { field: 'termination_For_Cause', value: 'Either party may terminate immediately for material breach of contract terms', confidence: 88, needsReview: false },
  { field: 'termination_Early_Fee', value: 'Early termination fee shall be 25% of remaining contract value', confidence: 85, needsReview: true },
  { field: 'termination_Transition_Support', value: 'Vendor shall provide 30 days transition support and knowledge transfer upon termination', confidence: 87, needsReview: false },
  
  // Insurance Requirements (JSON field)
  { field: 'insurance_General_Liability', value: 'General liability insurance of at least $2,000,000 per occurrence', confidence: 89, needsReview: false },
  { field: 'insurance_Professional_Liability', value: 'Professional liability insurance of at least $1,000,000 per claim', confidence: 87, needsReview: false },
  { field: 'insurance_Cyber_Liability', value: 'Cyber liability insurance covering data breaches and security incidents', confidence: 85, needsReview: true },
  
  // Data Protection Clauses (JSON field)
  { field: 'data_protection_GDPR_Compliance', value: 'Vendor shall comply with GDPR requirements for EU data processing', confidence: 88, needsReview: false },
  { field: 'data_protection_Data_Retention', value: 'Personal data shall be retained only as long as necessary for contract performance', confidence: 86, needsReview: false },
  { field: 'data_protection_Right_to_Erasure', value: 'Vendor shall honor data subject requests for data erasure within 30 days', confidence: 84, needsReview: true }
])

// Load vendors on component mount

// Load contract data for editing
const loadContractData = async (contractId) => {
  try {
    console.log('🔄 Loading contract data for editing:', contractId)
    console.log('🔍 Contract ID type:', typeof contractId)
    console.log('🔍 Contract ID value:', contractId)
    
    if (!contractId || contractId === 'undefined' || contractId === 'null') {
      console.error('❌ Invalid contract ID:', contractId)
      return
    }
    
    const response = await contractsApi.getContract(contractId)
    console.log('📡 API response:', response)
    
    if (response.success) {
      const contract = response.data
      console.log('✅ Contract data loaded:', contract)
      
      // Populate form data
      formData.value = {
        contract_title: contract.contract_title || '',
        contract_number: contract.contract_number || '',
        vendor_id: contract.vendor_id || null,
        contract_type: contract.contract_type || '',
        contract_category: contract.contract_category || '',
        contract_value: contract.contract_value || '',
        currency: contract.currency || 'USD',
        start_date: contract.start_date || '',
        end_date: contract.end_date || '',
        notice_period_days: contract.notice_period_days || 30,
        contract_owner: contract.contract_owner || null,
        legal_reviewer: contract.legal_reviewer || null,
        assigned_to: contract.assigned_to || null,
        priority: contract.priority || 'medium',
        compliance_status: contract.compliance_status || 'under_review',
        dispute_resolution_method: contract.dispute_resolution_method || '',
        governing_law: contract.governing_law || '',
        termination_clause_type: contract.termination_clause_type || 'convenience',
        liability_cap: contract.liability_cap || '',
        insurance_requirements: contract.insurance_requirements || {},
        data_protection_clauses: contract.data_protection_clauses || {},
        custom_fields: contract.custom_fields || {},
        compliance_framework: contract.compliance_framework || '',
        parent_contract_id: contract.parent_contract_id || null,
        main_contract_id: contract.main_contract_id || null
      }
      
      console.log('📝 Form data populated:', formData.value)
      console.log('📝 Contract title:', formData.value.contract_title)
      console.log('📝 Contract type:', formData.value.contract_type)
      console.log('📝 Contract category:', formData.value.contract_category)
      
      // Force form re-rendering
      formKey.value++
      console.log('🔄 Form key updated to force re-rendering:', formKey.value)
      
      // Load contract terms and clauses
      await loadContractTermsAndClauses(contractId)
      
      console.log('✅ Contract data populated successfully')
    } else {
      console.error('❌ Failed to load contract data:', response.message)
      PopupService.error('Failed to load contract data. Please try again.', 'Loading Failed')
    }
  } catch (error) {
    console.error('❌ Error loading contract data:', error)
    PopupService.error('Error loading contract data. Please try again.', 'Loading Error')
  }
}

// Load contract terms and clauses
const loadContractTermsAndClauses = async (contractId) => {
  try {
    // Load terms
    const termsResponse = await contractsApi.getContractTerms(contractId)
    if (termsResponse.success) {
      contractTerms.value = termsResponse.data || []
      console.log('✅ Contract terms loaded:', contractTerms.value.length)
    }
    
    // Load clauses
    const clausesResponse = await contractsApi.getContractClauses(contractId)
    if (clausesResponse.success) {
      contractClauses.value = clausesResponse.data || []
      console.log('✅ Contract clauses loaded:', contractClauses.value.length)
    }
  } catch (error) {
    console.error('❌ Error loading contract terms/clauses:', error)
  }
}

// Watch for route query changes to update active tab
watch(() => route.query.tab, (newTab) => {
  if (newTab && typeof newTab === 'string') {
    activeTab.value = newTab
    console.log('🔄 Active tab updated from route query:', newTab)
  }
})

onMounted(async () => {
  console.log('🚀 CreateContract onMounted - contractId:', contractId)
  console.log('🚀 CreateContract onMounted - route.query:', route.query)
  console.log('🚀 CreateContract onMounted - route.params:', route.params)
  console.log('🚀 CreateContract onMounted - showOCR initial value:', showOCR.value)
  console.log('🚀 CreateContract onMounted - testOCRButton function:', typeof testOCRButton)
  
  // Set active tab from route query if present
  if (route.query.tab && typeof route.query.tab === 'string') {
    activeTab.value = route.query.tab
    console.log('🔄 Set active tab from route query:', route.query.tab)
  }
  
  // Clear any leftover session storage data when creating a new contract
  // But only if we're not coming from the preview page
  const isFromPreview = route.query.from === 'preview'
  if (!contractId) {
    // Check if we have preview data or are coming from preview - if so, don't clear it yet
    const hasPreviewData = sessionStorage.getItem('contractPreviewData')
    if (!hasPreviewData && !isFromPreview) {
      sessionStorage.removeItem('subcontractData')
      sessionStorage.removeItem('contractPreviewData')
      console.log('🧹 Cleared session storage for new contract creation')
    } else {
      console.log('🔄 Preview data detected or coming from preview, keeping session storage for restoration')
    }
  }
  
  
  // Load contract data if editing
  // Double-check we're not on the create route
  const currentPath = route.path
  const isOnCreateRoute = currentPath === '/contracts/create' || currentPath === '/contracts/new'
  
  if (contractId && !isOnCreateRoute && contractId > 0) {
    console.log('🔄 Loading contract data for editing in onMounted')
    await loadContractData(contractId)
  } else {
    console.log('⚠️ No contract ID provided - creating new contract')
    console.log('🔍 Current path:', currentPath)
    console.log('🔍 Is on create route:', isOnCreateRoute)
  }
  
  // Check if we're returning from preview page first (higher priority)
  // Then check for questionnaire templates draft data
  const previewDataFromStorage = sessionStorage.getItem('contractPreviewData')
  const contractDraftData = sessionStorage.getItem('contract_draft_data')
  
  // If coming from preview, skip questionnaire draft data restoration
  // (preview data will be restored later after loading vendors/users)
  if (isFromPreview && previewDataFromStorage) {
    console.log('🔄 Coming from preview, will restore preview data after loading vendors/users')
  } else if (contractDraftData) {
    try {
      const parsedData = JSON.parse(contractDraftData)
      console.log('🔄 Restoring contract draft data from questionnaire templates:', parsedData)
      
      // Restore form data
      if (parsedData.formData) {
        Object.keys(parsedData.formData).forEach(key => {
          if (parsedData.formData[key] !== undefined && parsedData.formData[key] !== null) {
            formData.value[key] = parsedData.formData[key]
          }
        })
      }
      
      // Restore contract terms and clauses
      if (parsedData.contractTerms && Array.isArray(parsedData.contractTerms)) {
        contractTerms.value = parsedData.contractTerms.map(term => reactive({ ...term }))
        console.log('✅ Restored contract terms:', contractTerms.value.length)
      }
      
      if (parsedData.contractClauses && Array.isArray(parsedData.contractClauses)) {
        contractClauses.value = parsedData.contractClauses.map(clause => reactive({ ...clause }))
        console.log('✅ Restored contract clauses:', contractClauses.value.length)
      }
      
      // Clear the session storage after restoring
      sessionStorage.removeItem('contract_draft_data')
      
      // Force reactivity update
      contractTerms.value = [...contractTerms.value]
      contractClauses.value = [...contractClauses.value]
      
      // Wait for next tick to ensure DOM is updated
      await nextTick()
      
      // Reload questionnaires after restoring terms (since questions may have been added/removed/edited)
      // Clear cached questionnaires first to ensure fresh data
      if (contractTerms.value.length > 0) {
        console.log('🔄 Reloading questionnaires after returning from questionnaire templates')
        
        // Clear any cached questionnaires to force fresh reload
        allTermQuestionnaires.value = []
        
        // Clear any questionnaire-related sessionStorage
        sessionStorage.removeItem('questionnaire_edit_data')
        
        // Close any open modals to prevent showing stale data
        closeQuestionnairesModal()
        
        // Wait a bit for backend to process, then reload with retry mechanism
        const reloadQuestionnaires = async (attempt = 1, maxAttempts = 3) => {
          try {
            // Force clear before reload to ensure fresh data
            allTermQuestionnaires.value = []
            await loadTermQuestionnaires()
            // Check if we found questionnaires
            const totalLoaded = allTermQuestionnaires.value.length
            console.log(`✅ Questionnaires reloaded (attempt ${attempt}): ${totalLoaded} questionnaires found`)
            
            // If we didn't find any and this isn't the last attempt, retry
            if (totalLoaded === 0 && attempt < maxAttempts) {
              console.log(`⚠️ No questionnaires found, retrying in 1 second... (attempt ${attempt + 1}/${maxAttempts})`)
              setTimeout(() => reloadQuestionnaires(attempt + 1, maxAttempts), 1000)
            } else {
              // Force another reactivity update after loading
              await nextTick()
              console.log('✅ Final questionnaires count:', allTermQuestionnaires.value.length)
              // Force reactivity update to refresh UI
              allTermQuestionnaires.value = [...allTermQuestionnaires.value]
            }
          } catch (error) {
            console.error(`❌ Error reloading questionnaires (attempt ${attempt}):`, error)
            if (attempt < maxAttempts) {
              setTimeout(() => reloadQuestionnaires(attempt + 1, maxAttempts), 1000)
            }
          }
        }
        
        // Start with initial delay, then retry if needed
        setTimeout(() => reloadQuestionnaires(), 1000)
      }
    } catch (error) {
      console.error('Error restoring contract draft data:', error)
    }
  } else {
    // Load questionnaires for existing terms if not restoring
    if (contractTerms.value.length > 0) {
      await loadTermQuestionnaires()
    }
  }
  
  try {
    // Load vendors, users, and legal reviewers in parallel
    const [vendorsResponse, usersResponse, legalReviewersResponse] = await Promise.all([
      contractsApi.getVendors(),
      contractsApi.getUsers(),
      contractsApi.getLegalReviewers()
    ])
    
    if (vendorsResponse.success) {
      vendors.value = vendorsResponse.data
    }
    
    if (usersResponse.success) {
      users.value = usersResponse.data
    }
    
    if (legalReviewersResponse.success) {
      legalReviewers.value = legalReviewersResponse.data
    }
    
    // After loading all data, check if we're returning from preview page or OCR and restore form data
    const previewData = sessionStorage.getItem('contractPreviewData')
    const ocrData = localStorage.getItem('ocrContractData')
    
    if (previewData) {
      try {
        const parsedData = JSON.parse(previewData)
        console.log('🔄 Restoring form data from preview:', parsedData)
        
        // Restore form data
        if (parsedData.contractData) {
          console.log('🔍 Original form data before restoration:', formData.value)
          console.log('🔍 Preview data to restore:', parsedData.contractData)
          
          // Restore each field individually to ensure reactivity
          const contractData = parsedData.contractData
          Object.keys(contractData).forEach(key => {
            if (contractData[key] !== undefined && contractData[key] !== null) {
              formData.value[key] = contractData[key]
              console.log(`✅ Restored ${key}:`, contractData[key])
            }
          })
          
          console.log('✅ Form data restored:', formData.value)
          
          // Set vendor name for display if vendor_id is selected
          if (formData.value.vendor_id && vendors.value.length > 0) {
            const selectedVendor = vendors.value.find(v => v.vendor_id == formData.value.vendor_id)
            if (selectedVendor) {
              formData.value.vendor_name = selectedVendor.company_name
              console.log('✅ Vendor name set for display:', formData.value.vendor_name)
            }
          }
          
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
              'contract_title', 'contract_number', 'parent_contract_id', 'contract_value',
              'liability_cap', 'start_date', 'end_date', 'notice_period_days',
              'governing_law', 'contract_risk_score'
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
            const textareaFields = ['renewal_terms']
            textareaFields.forEach(fieldId => {
              const textarea = document.getElementById(fieldId)
              if (textarea && formData.value[fieldId] !== undefined && formData.value[fieldId] !== null) {
                textarea.value = formData.value[fieldId] || ''
                textarea.dispatchEvent(new Event('input', { bubbles: true }))
                console.log(`🔧 Manually set ${fieldId} textarea value:`, textarea.value)
              }
            })
            
            console.log('🔍 Form field values after restoration:')
            console.log('  - contract_title:', formData.value.contract_title)
            console.log('  - contract_number:', formData.value.contract_number)
            console.log('  - contract_value:', formData.value.contract_value)
            console.log('  - start_date:', formData.value.start_date)
            console.log('  - end_date:', formData.value.end_date)
            console.log('  - vendor_id:', formData.value.vendor_id)
            console.log('  - contract_owner:', formData.value.contract_owner)
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
        sessionStorage.removeItem('contractPreviewData')
        
        console.log('✅ All form data restored successfully')
        console.log('🔍 Final contractTerms length:', contractTerms.value.length)
        console.log('🔍 Final contractClauses length:', contractClauses.value.length)
      } catch (error) {
        console.error('Error restoring form data from preview:', error)
      }
    } else if (ocrData) {
      // Handle OCR data restoration
      try {
        const parsedOCRData = JSON.parse(ocrData)
        console.log('🔄 Restoring form data from OCR:', parsedOCRData)
        
        // Restore form data
        if (parsedOCRData) {
          console.log('🔍 Original form data before OCR restoration:', formData.value)
          console.log('🔍 OCR data to restore:', parsedOCRData)
          
          // Restore each field individually to ensure reactivity
          Object.keys(parsedOCRData).forEach(key => {
            if (key !== 'contractTerms' && key !== 'contractClauses' && parsedOCRData[key] !== undefined && parsedOCRData[key] !== null) {
              formData.value[key] = parsedOCRData[key]
              console.log(`✅ Restored ${key}:`, parsedOCRData[key])
            }
          })
          
          console.log('✅ Form data restored from OCR:', formData.value)
          
          // Set vendor name for display if vendor_id is selected
          if (formData.value.vendor_id && vendors.value.length > 0) {
            const selectedVendor = vendors.value.find(v => v.vendor_id == formData.value.vendor_id)
            if (selectedVendor) {
              formData.value.vendor_name = selectedVendor.company_name
              console.log('✅ Vendor name set for display from OCR:', formData.value.vendor_name)
            }
          }
          
          // Force reactivity update by creating a completely new reactive object
          const newFormData = { ...formData.value }
          formData.value = newFormData
          console.log('🔄 Form data after reactivity update from OCR:', formData.value)
          
          // Force a DOM update by using nextTick
          await nextTick()
          console.log('🔄 DOM should be updated now from OCR')
          
          // Force form re-render by updating the key
          formKey.value++
          console.log('🔄 Form key updated to force re-render from OCR:', formKey.value)
        }
        
        // Restore contract terms from OCR - ensure each term is reactive
        if (parsedOCRData.contractTerms && Array.isArray(parsedOCRData.contractTerms)) {
          contractTerms.value = parsedOCRData.contractTerms.map(term => reactive({ ...term })) // Make each term reactive
          console.log('✅ Contract terms restored from OCR:', contractTerms.value)
          console.log('✅ Contract terms count from OCR:', contractTerms.value.length)
          console.log('✅ First term details from OCR:', contractTerms.value[0])
        } else {
          console.log('⚠️ No contract terms found in OCR data')
        }
        
        // Restore contract clauses from OCR - ensure each clause is reactive
        if (parsedOCRData.contractClauses && Array.isArray(parsedOCRData.contractClauses)) {
          contractClauses.value = parsedOCRData.contractClauses.map(clause => reactive({ ...clause })) // Make each clause reactive
          console.log('✅ Contract clauses restored from OCR:', contractClauses.value)
          console.log('✅ Contract clauses count from OCR:', contractClauses.value.length)
          console.log('✅ First clause details from OCR:', contractClauses.value[0])
        } else {
          console.log('⚠️ No contract clauses found in OCR data')
        }
        
        // Force reactivity update for terms and clauses
        contractTerms.value = [...contractTerms.value]
        contractClauses.value = [...contractClauses.value]
        
        // Force form re-render to ensure terms and clauses are displayed
        formKey.value++
        console.log('🔄 Form key updated after terms/clauses restoration from OCR:', formKey.value)
        
        // Ensure the form is properly rendered by waiting for next tick
        await nextTick()
        console.log('🔄 DOM updated after terms/clauses restoration from OCR')
        
        // Additional debugging to verify the data is properly set
        console.log('🔍 After OCR restoration - contractTerms.value:', contractTerms.value)
        console.log('🔍 After OCR restoration - contractClauses.value:', contractClauses.value)
        console.log('🔍 After OCR restoration - contractTerms.length:', contractTerms.value.length)
        console.log('🔍 After OCR restoration - contractClauses.length:', contractClauses.value.length)
        
        // Force another reactivity update after nextTick
        setTimeout(() => {
          contractTerms.value = [...contractTerms.value]
          contractClauses.value = [...contractClauses.value]
          console.log('🔄 Final reactivity update completed from OCR')
        }, 100)
        
        // Clear the OCR data from localStorage
        localStorage.removeItem('ocrContractData')
        
        console.log('✅ All OCR form data restored successfully')
        console.log('🔍 Final contractTerms length from OCR:', contractTerms.value.length)
        console.log('🔍 Final contractClauses length from OCR:', contractClauses.value.length)
      } catch (error) {
        console.error('Error restoring form data from OCR:', error)
      }
    }
  } catch (error) {
    console.error('Error loading data:', error)
    
    // Provide specific error messages based on error type
    if (error.message.includes('Network Error') || error.message.includes('ERR_CONNECTION_REFUSED')) {
      errors.value.general = 'Cannot connect to server. Please check your network connection and try again.'
    } else if (error.message.includes('Authentication required')) {
      errors.value.general = 'Authentication required. Please log in to access this feature.'
      // For development, provide mock data if authentication fails
      console.warn('Using mock data for development')
      vendors.value = [
        { vendor_id: 1, company_name: 'TechCloud Solutions' },
        { vendor_id: 2, company_name: 'DataSync Corp' },
        { vendor_id: 3, company_name: 'SecureNet Systems' }
      ]
      users.value = [
        { user_id: 1, username: 'admin', display_name: 'Admin User', role: 'Admin' },
        { user_id: 2, username: 'manager', display_name: 'Manager User', role: 'Contract Manager' }
      ]
      legalReviewers.value = [
        { user_id: 1, username: 'admin', display_name: 'Admin User', role: 'Admin' },
        { user_id: 3, username: 'legal', display_name: 'Legal Counsel', role: 'Legal Counsel' }
      ]
      
      // After setting mock data, try to restore preview data
      const previewData = sessionStorage.getItem('contractPreviewData')
      if (previewData) {
        try {
          const parsedData = JSON.parse(previewData)
          console.log('🔄 Restoring form data from preview (with mock data):', parsedData)
          
          if (parsedData.contractData) {
            console.log('🔍 Original form data before restoration (mock data):', formData.value)
            console.log('🔍 Preview data to restore (mock data):', parsedData.contractData)
            
            // Restore each field individually to ensure reactivity
            const contractData = parsedData.contractData
            Object.keys(contractData).forEach(key => {
              if (contractData[key] !== undefined && contractData[key] !== null) {
                formData.value[key] = contractData[key]
                console.log(`✅ Restored ${key} (mock data):`, contractData[key])
              }
            })
            
            console.log('✅ Form data restored (mock data):', formData.value)
            
            // Set vendor name for display if vendor_id is selected
            if (formData.value.vendor_id && vendors.value.length > 0) {
              const selectedVendor = vendors.value.find(v => v.vendor_id == formData.value.vendor_id)
              if (selectedVendor) {
                formData.value.vendor_name = selectedVendor.company_name
                console.log('✅ Vendor name set for display (mock data):', formData.value.vendor_name)
              }
            }
            
            // Force reactivity update by creating a completely new reactive object
            const newFormData = { ...formData.value }
            formData.value = newFormData
            console.log('🔄 Form data after reactivity update (mock data):', formData.value)
            
            // Force a DOM update by using nextTick
            await nextTick()
            console.log('🔄 DOM should be updated now (mock data)')
            
            // Force form re-render by updating the key
            formKey.value++
            console.log('🔄 Form key updated to force re-render (mock data):', formKey.value)
            
            // Force update all form fields by triggering input events
            setTimeout(() => {
              // List of all form field IDs that need to be updated
              const formFields = [
                'contract_title', 'contract_number', 'parent_contract_id', 'contract_value',
                'liability_cap', 'start_date', 'end_date', 'notice_period_days',
                'governing_law', 'contract_risk_score'
              ]
              
              // Update each form field
              formFields.forEach(fieldId => {
                const input = document.getElementById(fieldId)
                if (input && formData.value[fieldId] !== undefined && formData.value[fieldId] !== null) {
                  input.value = formData.value[fieldId] || ''
                  input.dispatchEvent(new Event('input', { bubbles: true }))
                  console.log(`🔧 Manually set ${fieldId} input value (mock data):`, input.value)
                }
              })
              
              // Update textarea fields
              const textareaFields = ['renewal_terms']
              textareaFields.forEach(fieldId => {
                const textarea = document.getElementById(fieldId)
                if (textarea && formData.value[fieldId] !== undefined && formData.value[fieldId] !== null) {
                  textarea.value = formData.value[fieldId] || ''
                  textarea.dispatchEvent(new Event('input', { bubbles: true }))
                  console.log(`🔧 Manually set ${fieldId} textarea value (mock data):`, textarea.value)
                }
              })
              
              console.log('🔍 Form field values after restoration (mock data):')
              console.log('  - contract_title:', formData.value.contract_title)
              console.log('  - contract_number:', formData.value.contract_number)
              console.log('  - contract_value:', formData.value.contract_value)
              console.log('  - start_date:', formData.value.start_date)
              console.log('  - end_date:', formData.value.end_date)
              console.log('  - vendor_id:', formData.value.vendor_id)
              console.log('  - contract_owner:', formData.value.contract_owner)
            }, 200)
          }
          
          if (parsedData.contractTerms && Array.isArray(parsedData.contractTerms)) {
            contractTerms.value = parsedData.contractTerms.map(term => reactive({ ...term })) // Make each term reactive
            console.log('✅ Contract terms restored (mock data):', contractTerms.value)
            console.log('✅ Contract terms count (mock data):', contractTerms.value.length)
          } else {
            console.log('⚠️ No contract terms found in preview data (mock data)')
          }
          
          if (parsedData.contractClauses && Array.isArray(parsedData.contractClauses)) {
            contractClauses.value = parsedData.contractClauses.map(clause => reactive({ ...clause })) // Make each clause reactive
            console.log('✅ Contract clauses restored (mock data):', contractClauses.value)
            console.log('✅ Contract clauses count (mock data):', contractClauses.value.length)
          } else {
            console.log('⚠️ No contract clauses found in preview data (mock data)')
          }
          
          // Force reactivity update for terms and clauses
          contractTerms.value = [...contractTerms.value]
          contractClauses.value = [...contractClauses.value]
          
          // Force form re-render to ensure terms and clauses are displayed
          formKey.value++
          console.log('🔄 Form key updated after terms/clauses restoration (mock data):', formKey.value)
          
          // Ensure the form is properly rendered by waiting for next tick
          await nextTick()
          console.log('🔄 DOM updated after terms/clauses restoration (mock data)')
          
          sessionStorage.removeItem('contractPreviewData')
          console.log('✅ Form data restored with mock data')
          console.log('🔍 Final contractTerms length (mock data):', contractTerms.value.length)
          console.log('🔍 Final contractClauses length (mock data):', contractClauses.value.length)
        } catch (error) {
          console.error('Error restoring form data from preview:', error)
        }
      }
    } else if (error.message.includes('permission')) {
      errors.value.general = 'You do not have permission to access this feature.'
    } else {
      errors.value.general = 'Failed to load data. Please check if the backend server is running.'
    }
  }
})

// Methods
const handleInputChange = (field, value) => {
  formData.value[field] = value
  // Clear field-specific errors when user starts typing
  if (errors.value[field]) {
    delete errors.value[field]
  }
}

const validateForm = () => {
  const newErrors = {}
  
  console.log('🔍 Validating form with data:', {
    contract_title: formData.value.contract_title,
    contract_type: formData.value.contract_type,
    vendor_id: formData.value.vendor_id,
    contract_value: formData.value.contract_value,
    start_date: formData.value.start_date,
    end_date: formData.value.end_date,
    contract_owner: formData.value.contract_owner
  })
  
  // Required field validation
  if (!formData.value.contract_title) {
    newErrors.contract_title = 'Contract title is required'
    console.log('❌ Missing contract_title')
  }
  if (!formData.value.contract_type) {
    newErrors.contract_type = 'Contract type is required'
    console.log('❌ Missing contract_type')
  }
  if (!formData.value.vendor_id) {
    newErrors.vendor_id = 'Vendor selection is required'
    console.log('❌ Missing vendor_id')
  }
  if (!formData.value.contract_value) {
    newErrors.contract_value = 'Contract value is required'
    console.log('❌ Missing contract_value')
  }
  if (!formData.value.start_date) {
    newErrors.start_date = 'Start date is required'
    console.log('❌ Missing start_date')
  }
  if (!formData.value.end_date) {
    newErrors.end_date = 'End date is required'
    console.log('❌ Missing end_date')
  }
  if (!formData.value.contract_owner) {
    newErrors.contract_owner = 'Contract owner is required'
    console.log('❌ Missing contract_owner')
  }
  
  // Date validation
  if (formData.value.start_date && formData.value.end_date) {
    if (new Date(formData.value.start_date) >= new Date(formData.value.end_date)) {
      newErrors.end_date = 'End date must be after start date'
    }
  }
  
  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

const handleSaveDraft = async () => {
  if (!validateForm()) {
    return
  }
  
  isLoading.value = true
  errors.value = {}
  
  try {
    // Load questionnaires before saving if terms exist
    if (contractTerms.value.length > 0) {
      await loadTermQuestionnaires()
    }
    
    const contractData = {
      ...prepareContractData(),
      contract_kind: 'MAIN',  // Explicitly set as MAIN contract
      status: 'PENDING_ASSIGNMENT',
      workflow_stage: 'under_review'
    }
    
    const response = await contractsApi.createContract(contractData)
    
      if (response.success) {
        // Save terms and clauses if any exist
        if (contractTerms.value.length > 0) {
          await saveContractTerms(response.data.contract_id)
        }
        
        if (contractClauses.value.length > 0) {
          await saveContractClauses(response.data.contract_id)
        }
        
        // Trigger risk analysis in the background (non-blocking)
        triggerRiskAnalysis(response.data.contract_id)
        
        showSuccessMessage('Contract draft saved successfully', '/contracts')
      }
  } catch (error) {
    console.error('Error saving draft:', error)
    if (error.message.includes('Authentication required')) {
      errors.value.general = 'Authentication required. Please log in to save contracts.'
    } else {
      errors.value.general = error.message || 'Failed to save contract draft'
    }
  } finally {
    isLoading.value = false
  }
}

const handleSubmitForReview = async () => {
  console.log('🚀 Submit for Review clicked')
  console.log('📋 Current form data:', formData.value)
  console.log('📋 Current errors:', errors.value)
  
  // Prevent multiple rapid clicks
  if (isLoading.value) {
    console.log('⚠️ Already processing, ignoring duplicate click')
    return
  }
  
  // Additional protection against double clicks
  if (isSubmitting.value) {
    console.log('⚠️ Already submitting, ignoring duplicate click')
    return
  }
  
  if (!validateForm()) {
    console.log('❌ Form validation failed:', errors.value)
    return
  }
  
  // Check if we have subcontract data in session storage
  const subcontractData = sessionStorage.getItem('subcontractData')
  console.log('🔍 Checking for subcontract data:', subcontractData)
  
  // Also check if we're explicitly creating a standalone contract
  const isStandaloneContract = !subcontractData || subcontractData === 'null' || subcontractData === 'undefined'
  console.log('🔍 Is standalone contract:', isStandaloneContract)
  
  if (subcontractData && !isStandaloneContract) {
    console.log('🔧 Found subcontract data, creating both contracts together')
    try {
      isLoading.value = true
      isSubmitting.value = true
      errors.value = {}
      
      const parsedSubcontractData = JSON.parse(subcontractData)
      
      // Prepare main contract data
      const mainContractData = {
        ...prepareContractData(),
        contract_kind: 'MAIN',
        status: 'PENDING_ASSIGNMENT',
        workflow_stage: 'under_review'
      }
      
      // Prepare subcontract data
      const subcontractFormData = {
        ...parsedSubcontractData,
        contract_kind: 'SUBCONTRACT',
        status: 'PENDING_ASSIGNMENT',
        workflow_stage: 'under_review'
      }
      
      console.log('📤 Creating both contracts together:', {
        mainContract: mainContractData,
        subcontract: subcontractFormData
      })
      
      const response = await contractsApi.createContractWithSubcontract(mainContractData, subcontractFormData)
      
      if (response.success) {
        // Clear subcontract data from session storage
        sessionStorage.removeItem('subcontractData')
        
        PopupService.success('Both contracts have been created and submitted for review.', 'Contract and Subcontract Created Successfully')
        router.push('/contracts')
      } else {
        throw new Error(response.message || 'Failed to create contract and subcontract')
      }
    } catch (error) {
      console.error('❌ Error creating contract and subcontract:', error)
      errors.value.general = error.message || 'Failed to create contract and subcontract'
    } finally {
      isLoading.value = false
      isSubmitting.value = false
    }
  } else {
    // Always navigate to preview page for single contract submission
    // The preview page will handle the actual database save
    console.log('✅ Navigating to preview page for contract review')
    
    // OPTIMIZATION: Pre-load ALL questionnaires for ALL terms in parallel BEFORE navigating
    // This ensures preview page has all data immediately without making API calls
    if (contractTerms.value.length > 0) {
      console.log('📋 Pre-loading all questionnaires for all terms in parallel...')
      isLoading.value = true
      
      try {
        // Load questionnaires for all terms if not already loaded
        if (allTermQuestionnaires.value.length === 0) {
          await loadTermQuestionnaires()
        }
        
        // Pre-load template questions for ALL selected templates in parallel
        await preloadAllTemplateQuestions()
        
        console.log(`✅ Pre-loaded ${allTermQuestionnaires.value.length} questionnaires`)
      } catch (err) {
        console.error('❌ Error pre-loading questionnaires:', err)
        // Continue anyway - preview page will handle missing data
      } finally {
        isLoading.value = false
      }
    }
    
    navigateToPreview()
  }
}


// Update existing contract
const updateContract = async () => {
  try {
    isLoading.value = true
    errors.value = {}
    
    const contractData = {
      ...prepareContractData(),
      contract_kind: 'MAIN',  // Explicitly set as MAIN contract
      status: 'PENDING_ASSIGNMENT',
      workflow_stage: 'under_review'
    }
    
    console.log('📤 Updating contract:', contractId, contractData)
    
    const response = await contractsApi.updateContract(contractId, contractData)
    
    if (response.success) {
      // Update terms and clauses if any exist
      if (contractTerms.value.length > 0) {
        await updateContractTerms(contractId)
      }
      
      if (contractClauses.value.length > 0) {
        await updateContractClauses(contractId)
      }
      
      PopupService.success('Contract updated successfully and submitted for review!', 'Update Successful')
      router.push('/contracts')
    } else {
      throw new Error(response.message || 'Failed to update contract')
    }
  } catch (error) {
    console.error('❌ Error updating contract:', error)
    if (error.message.includes('Authentication required')) {
      errors.value.general = 'Authentication required. Please log in to update contracts.'
    } else {
      errors.value.general = error.message || 'Failed to update contract'
    }
  } finally {
    isLoading.value = false
  }
}

// Update contract terms
const updateContractTerms = async (contractId) => {
  try {
    console.log('🔍 Updating contract terms for contract ID:', contractId)
    
    if (!contractTerms.value || !Array.isArray(contractTerms.value)) {
      console.log('⚠️ No contract terms to update or contractTerms is not an array')
      return
    }
    
    // Delete existing terms first
    await contractsApi.deleteContractTerms(contractId)
    
    // Add new terms
    for (const [index, term] of contractTerms.value.entries()) {
      if (!term) continue
      
      const termData = {
        term_id: term.term_id || `term_${Date.now()}_${index}`,
        term_category: term.term_category || '',
        term_title: term.term_title || '',
        term_text: term.term_text || '',
        risk_level: 'Low', // Default value
        compliance_status: 'Pending', // Default value
        is_standard: Boolean(term.is_standard),
        approval_status: 'Pending', // Default value
        version_number: '1.0', // Default value
        parent_term_id: term.parent_term_id || ''
      }
      
      const response = await contractsApi.createContractTerms(contractId, termData)
      
      // Update the term object with the actual term_id from the response
      // This handles cases where the backend generates a new term_id due to duplicates
      if (response && response.data && response.data.term_id) {
        const savedTermId = response.data.term_id
        if (savedTermId !== termData.term_id) {
          console.log(`⚠️ Term ID changed from ${termData.term_id} to ${savedTermId}, updating frontend term object`)
          term.term_id = savedTermId
        }
      }
    }
    
    // Force reactivity update after all terms are updated
    contractTerms.value = [...contractTerms.value]
    
    console.log('✅ Contract terms updated successfully')
  } catch (error) {
    console.error('❌ Error updating contract terms:', error)
    throw error
  }
}

// Update contract clauses
const updateContractClauses = async (contractId) => {
  try {
    console.log('🔍 Updating contract clauses for contract ID:', contractId)
    
    if (!contractClauses.value || !Array.isArray(contractClauses.value)) {
      console.log('⚠️ No contract clauses to update or contractClauses is not an array')
      return
    }
    
    // Delete existing clauses first
    await contractsApi.deleteContractClauses(contractId)
    
    // Add new clauses
    for (const [index, clause] of contractClauses.value.entries()) {
      if (!clause) continue
      
      const clauseData = {
        clause_id: clause.clause_id || `clause_${Date.now()}`,
        clause_name: clause.clause_name || '',
        clause_type: clause.clause_type || 'standard',
        clause_text: clause.clause_text || '',
        risk_level: 'low', // Default value
        legal_category: clause.legal_category || '',
        version_number: '1', // Default value
        is_standard: Boolean(clause.is_standard),
        notice_period_days: clause.notice_period_days || null,
        auto_renew: Boolean(clause.auto_renew),
        renewal_terms: clause.renewal_terms || '',
        termination_notice_period: clause.termination_notice_period || null,
        early_termination_fee: clause.early_termination_fee || null,
        termination_conditions: clause.termination_conditions || ''
      }
      
      await contractsApi.createContractClauses(contractId, clauseData)
    }
    
    console.log('✅ Contract clauses updated successfully')
  } catch (error) {
    console.error('❌ Error updating contract clauses:', error)
    throw error
  }
}

const handleCreateSubcontract = async () => {
  // Guard against accidental double-trigger
  if (isLoading.value || isSubmitting.value) {
    console.log('⚠️ Busy state detected, ignoring Create Subcontract click')
    return
  }
  console.log('🔧 Create Subcontract clicked')
  console.log('📋 Current form data:', formData.value)
  
  // Validate required fields for main contract
  if (!formData.value.contract_title || !formData.value.vendor_id || !formData.value.contract_value || 
      !formData.value.start_date || !formData.value.end_date || !formData.value.contract_owner) {
    PopupService.warning('Please fill in all required fields (Contract Title, Vendor, Contract Value, Start Date, End Date, Contract Owner) before creating a subcontract.', 'Required Fields Missing')
    return
  }
  
  try {
    isLoading.value = true
    errors.value = {}
    
    // Save main contract as draft first
    const contractData = {
      ...prepareContractData(),
      contract_kind: 'MAIN',  // Explicitly set as MAIN contract
      status: 'PENDING_ASSIGNMENT',
      workflow_stage: 'under_review'
    }
    
    console.log('💾 Saving main contract as draft:', contractData)
    const response = await contractsApi.createContract(contractData)
    
    if (response.success) {
      const mainContractId = response.data.contract_id
      console.log('✅ Main contract saved with ID:', mainContractId)
      
      // Navigate immediately - don't wait for terms/clauses to save
      console.log('🔄 Navigating to subcontract creation with parent ID:', mainContractId)
      router.push(`/contracts/${mainContractId}/subcontract`)
      
      // Save terms and clauses in the background (non-blocking)
      // This allows the user to see the subcontract page immediately
      if (contractTerms.value.length > 0 || contractClauses.value.length > 0) {
        console.log('📋 Saving terms and clauses in background...')
        Promise.all([
          contractTerms.value.length > 0 ? saveContractTerms(mainContractId).catch(err => {
            console.error('❌ Error saving terms in background:', err)
          }) : Promise.resolve(),
          contractClauses.value.length > 0 ? saveContractClauses(mainContractId).catch(err => {
            console.error('❌ Error saving clauses in background:', err)
          }) : Promise.resolve()
        ]).then(() => {
          console.log('✅ Terms and clauses saved in background')
        }).catch(err => {
          console.error('❌ Error saving terms/clauses in background:', err)
        })
      }
    } else {
      errors.value.general = response.message || 'Failed to save main contract'
    }
  } catch (error) {
    console.error('❌ Error saving main contract:', error)
    if (error.message.includes('Authentication required')) {
      errors.value.general = 'Authentication required. Please log in to save contracts.'
    } else {
      errors.value.general = error.message || 'Failed to save main contract'
    }
  } finally {
    isLoading.value = false
  }
}


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
      
        // Get questionnaires for this term (from selected template or direct questionnaires)
        const termQuestionnaires = await getQuestionnairesForTerm(term.term_id, term.term_category, term.term_title)
        console.log(`📋 Found ${termQuestionnaires.length} questionnaires for term ${index + 1} (${term.term_id || term.term_title})`)
      
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
          parent_term_id: term.parent_term_id || '',
          questionnaires: termQuestionnaires // Include questionnaires for this term
        }
        
        // Validate term_text before sending
        if (!termData.term_text || termData.term_text.trim() === '') {
          console.error('❌ Term text is empty for term:', termData.term_id)
          throw new Error(`Term text is required for term: ${termData.term_title || termData.term_id}`)
        }
        
        console.log('📤 Sending term data to API:', termData)
        console.log('🔍 Term is_standard value:', termData.is_standard, 'Type:', typeof termData.is_standard)
        
        const response = await contractsApi.createContractTerms(contractId, termData)
        console.log('📥 API response:', response)
        
        // Update the term object with the actual term_id from the response
        // This handles cases where the backend generates a new term_id due to duplicates
        if (response && response.data && response.data.term_id) {
          const savedTermId = response.data.term_id
          if (savedTermId !== termData.term_id) {
            console.log(`⚠️ Term ID changed from ${termData.term_id} to ${savedTermId}, updating frontend term object`)
            term.term_id = savedTermId
            // Force reactivity update
            contractTerms.value = [...contractTerms.value]
          }
          console.log('✅ Term saved successfully with term_id:', savedTermId)
        } else {
          console.log('✅ Term saved successfully:', termData.term_id)
        }
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


const triggerFileInput = () => {
  console.log('🖱️ Button clicked, triggering file input')
  if (fileInput.value) {
    fileInput.value.click()
  } else {
    console.error('❌ File input ref not found')
  }
}

const handleDragOver = (event) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragEnter = (event) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (event) => {
  event.preventDefault()
  isDragOver.value = false
}

const handleFileDrop = (event) => {
  console.log('📁 File dropped:', event)
  isDragOver.value = false
  const files = event.dataTransfer.files
  if (files && files.length > 0) {
    const file = files[0]
    console.log('📁 Dropped file:', file)
    
    // Create a synthetic event to reuse the existing handler
    const syntheticEvent = {
      target: {
        files: [file]
      }
    }
    handleFileUpload(syntheticEvent)
  }
}

// Helper function to get stored token (compatible with GRC auth)
const getStoredToken = () => {
  const keys = ['access_token', 'session_token', 'token', 'jwt_token']
  for (const key of keys) {
    const val = localStorage.getItem(key)
    if (val) return val
  }
  return null
}

const handleFileUpload = async (event) => {
  console.log('📁 File upload triggered:', event)
  
  // Debug: Check formData availability at function start
  console.log('🔍 formData at function start:', !!formData.value)
  console.log('🔍 formData type at function start:', typeof formData.value)
  console.log('🔍 formData.value.file_path at start:', formData.value?.file_path)
  
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
    uploadFormData.append('document_type', 'contract')
    uploadFormData.append('extract_contract_data', 'true')
    // Hint backend to run only contract extraction (safe no-op if unsupported)
    uploadFormData.append('mode', 'contract_only')
    
    // Get authentication token
    const token = getStoredToken()
    if (!token) {
      throw new Error('Authentication required. Please log in to upload files.')
    }
    
    console.log('📤 Uploading file to OCR service...')
    
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
  
  // Log and store S3 upload information
  if (result.upload_info) {
    s3UploadInfo.value = result.upload_info
    console.log('📁 S3 Upload Info:', result.upload_info)
    if (result.upload_info.success) {
      console.log('✅ Document successfully uploaded to S3:', result.upload_info.file_info?.url || 'URL not available')
      // Store S3 URL in formData for contract creation
      if (result.upload_info.file_info?.url) {
        // Debug: Check if formData.value exists
        console.log('🔍 formData.value exists:', !!formData.value)
        console.log('🔍 formData.value type:', typeof formData.value)
        
        if (formData.value) {
          formData.value.file_path = result.upload_info.file_info.url
          console.log('💾 Stored S3 URL in formData.file_path:', formData.value.file_path)
        } else {
          console.error('❌ formData.value is undefined - cannot store S3 URL')
          // Store in session storage as fallback
          const s3Url = result.upload_info.file_info.url
          sessionStorage.setItem('contractS3Url', s3Url)
          console.log('💾 Stored S3 URL in session storage as fallback:', s3Url)
        }
      }
    } else {
      console.warn('⚠️ S3 upload had issues:', result.upload_info.error || 'Unknown error')
      // Show user-friendly error message
      if (result.upload_info.error) {
        console.log('📝 S3 Error Details:', result.upload_info.error)
      }
      // Clear file_path if S3 upload failed
      if (formData.value) {
        formData.value.file_path = ''
      }
    }
  } else {
    // No upload_info means S3 client was not available
    console.warn('⚠️ No S3 upload information available - S3 client may not be configured')
    s3UploadInfo.value = {
      success: false,
      error: 'S3 client not available. Document processing continued without cloud storage.'
    }
    if (formData.value) {
      formData.value.file_path = ''
    }
  }
  
  const contractData = result?.data || result?.contract_extraction?.data || null
  if (result.success && contractData) {
    // Map the OCR extracted data to our form structure
    await processOCRResults(contractData)
      uploadStep.value = 'review'
      console.log('✅ OCR data processed, showing review step')
    } else {
      throw new Error(result.error || 'Failed to extract contract data')
    }
    
  } catch (error) {
    console.error('❌ Error processing file:', error)
    errors.value.ocr = `Failed to process uploaded file: ${error.message}`
    uploadStep.value = 'upload'
    uploadProgress.value = 0
  }
}

const processOCRResults = async (ocrData) => {
  console.log('🔄 Processing OCR results:', ocrData)
  
  // Helper function to calculate confidence and determine if review is needed
  const getConfidenceInfo = (value, defaultConfidence = 85) => {
    if (!value || value === '' || value === null || value === undefined) {
      return { confidence: 0, needsReview: true }
    }
    return { confidence: defaultConfidence, needsReview: defaultConfidence < 85 }
  }
  
  // Build OCR results array from the extracted data
  const results = []
  
  // Basic Contract Information
  if (ocrData.contract_title) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_title, 95)
    results.push({ field: 'contract_title', value: ocrData.contract_title, confidence, needsReview })
  }
  
  if (ocrData.contract_number) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_number, 90)
    results.push({ field: 'contract_number', value: ocrData.contract_number, confidence, needsReview })
  }
  
  if (ocrData.contract_type) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.contract_type, 88)
    results.push({ field: 'contract_type', value: ocrData.contract_type, confidence, needsReview })
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
    results.push({ field: 'contract_value', value: String(ocrData.contract_value), confidence, needsReview: true })
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
  
  // Status and Priority
  if (ocrData.priority) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.priority, 85)
    results.push({ field: 'priority', value: ocrData.priority, confidence, needsReview: true })
  }
  
  // Legal Information
  if (ocrData.dispute_resolution_method) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.dispute_resolution_method, 80)
    results.push({ field: 'dispute_resolution_method', value: ocrData.dispute_resolution_method, confidence, needsReview: true })
  }
  
  if (ocrData.governing_law) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.governing_law, 88)
    results.push({ field: 'governing_law', value: ocrData.governing_law, confidence, needsReview })
  }
  
  if (ocrData.termination_clause_type) {
    const { confidence, needsReview } = getConfidenceInfo(ocrData.termination_clause_type, 85)
    results.push({ field: 'termination_clause_type', value: ocrData.termination_clause_type, confidence, needsReview: true })
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
    console.log('🔍 Processing OCR clauses:', ocrData.clauses.length, ocrData.clauses)
    
    ocrData.clauses.forEach((clause, index) => {
      // Determine clause type and field name prefix
      const clauseType = clause.type || 'standard'
      let fieldName = ''
      
      if (clauseType === 'renewal') {
        fieldName = `clause_renewal_${clause.name || `Renewal_${index + 1}`}`.replace(/\s+/g, '_')
        console.log('🔄 Processing renewal clause:', clause.name, clause)
      } else if (clauseType === 'termination') {
        fieldName = `clause_termination_${clause.name || `Termination_${index + 1}`}`.replace(/\s+/g, '_')
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
  
  // Process SLA terms if available
  if (ocrData.sla_terms && Array.isArray(ocrData.sla_terms)) {
    ocrData.sla_terms.forEach((sla, index) => {
      const fieldName = `term_SLA_${sla.metric || index}`
      const slaText = `${sla.metric}: ${sla.target} (Penalty: ${sla.penalty || 'Not specified'})`
      const { confidence, needsReview } = getConfidenceInfo(slaText, 80)
      results.push({ 
        field: fieldName, 
        value: slaText, 
        confidence, 
        needsReview: true,
        metadata: { category: 'Performance', type: 'SLA' }
      })
    })
  }
  
  // Update the ocrResults ref
  ocrResults.value = results
  
  console.log('✅ OCR results processed:', results.length, 'fields extracted')
  console.log('🔍 OCR results:', results)
}

const handleOCRValueChange = (field, newValue) => {
  // Ensure newValue is properly formatted
  let formattedValue = newValue
  if (typeof newValue === 'object' && newValue !== null) {
    formattedValue = newValue.text || newValue.value || JSON.stringify(newValue)
  } else if (newValue === null || newValue === undefined) {
    formattedValue = ''
  }
  
  ocrResults.value = ocrResults.value.map(result => 
    result.field === field 
      ? { ...result, value: formattedValue, needsReview: false }
      : result
  )
}

const applyOCRData = () => {
  console.log('🔄 Applying OCR data to form...')
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

  // Map OCR results to contract form fields
  const ocrData = {
    // Basic Contract Information (vendor_contracts table)
    contract_title: getFieldValue("contract_title"),
    contract_number: getFieldValue("contract_number"),
    contract_type: getFieldValue("contract_type"),
    contract_kind: getFieldValue("contract_kind"),
    contract_category: getFieldValue("contract_category"),
    
    // Vendor Information
    vendor_id: getIntegerFieldValue("vendor_id"),
    vendor_name: getFieldValue("vendor_name"),
    
    // Financial Information
    contract_value: getNumberFieldValue("contract_value"),
    currency: getFieldValue("currency") || "USD",
    liability_cap: getNumberFieldValue("liability_cap"),
    
    // Dates and Terms
    start_date: getFieldValue("start_date"),
    end_date: getFieldValue("end_date"),
    notice_period_days: getIntegerFieldValue("notice_period_days") || 30,
    auto_renewal: getBooleanFieldValue("auto_renewal"),
    renewal_terms: getFieldValue("renewal_terms"),
    
    // Contract Status and Workflow
    status: getFieldValue("status") || "PENDING_ASSIGNMENT",
    workflow_stage: getFieldValue("workflow_stage") || "under_review",
    priority: getFieldValue("priority") || "medium",
    compliance_status: getFieldValue("compliance_status") || "under_review",
    
    // Legal and Risk Information
    dispute_resolution_method: getFieldValue("dispute_resolution_method"),
    governing_law: getFieldValue("governing_law"),
    termination_clause_type: getFieldValue("termination_clause_type"),
    contract_risk_score: getNumberFieldValue("contract_risk_score"),
    
    // Assignment and Ownership
    contract_owner: getIntegerFieldValue("contract_owner"),
    legal_reviewer: getIntegerFieldValue("legal_reviewer"),
    assigned_to: getIntegerFieldValue("assigned_to"),
    
    // Compliance
    compliance_framework: getFieldValue("compliance_framework"),
    
    // JSON Fields
    insurance_requirements: insuranceRequirements,
    data_protection_clauses: dataProtectionClauses,
    custom_fields: {}
  }
  
  // Set form data
  formData.value = { ...formData.value, ...ocrData }
  
  // Set vendor name for display if vendor_id is selected
  if (formData.value.vendor_id && vendors.value.length > 0) {
    const selectedVendor = vendors.value.find(v => v.vendor_id == formData.value.vendor_id)
    if (selectedVendor) {
      formData.value.vendor_name = selectedVendor.company_name
    }
  }

  // Process contract terms from OCR
  const termFields = ocrResults.value.filter(r => r.field.startsWith("term_"))
  console.log('🔍 Found term fields:', termFields)
  
  // Helper function to map field names to valid term categories
  const mapToValidTermCategory = (fieldName, metadata) => {
    // Use metadata category if available
    if (metadata && metadata.category) {
      return metadata.category
    }
    
    const categoryMap = {
      'term_Payment': 'Payment',
      'term_Delivery': 'Delivery', 
      'term_Performance': 'Performance',
      'term_Liability': 'Liability',
      'term_Termination': 'Termination',
      'term_Intellectual_Property': 'Intellectual Property',
      'term_Confidentiality': 'Confidentiality',
      'term_SLA': 'Performance'
    }
    return categoryMap[fieldName] || fieldName.replace("term_", "").replace(/_/g, " ")
  }
  
  const ocrTerms = termFields.map((term, index) => ({
      term_id: `term_${Date.now()}_${index}`,
      term_category: mapToValidTermCategory(term.field, term.metadata),
      term_title: term.metadata?.title || term.field.replace("term_", "").replace(/_/g, " "),
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

  // Process contract clauses from OCR - including renewal and termination
  const clauseFields = ocrResults.value.filter(r => r.field.startsWith("clause_") && !r.field.startsWith("clause_renewal_") && !r.field.startsWith("clause_termination_"))
  const renewalFields = ocrResults.value.filter(r => r.field.startsWith("renewal_") || r.field.startsWith("clause_renewal_"))
  const terminationFields = ocrResults.value.filter(r => r.field.startsWith("termination_") || r.field.startsWith("clause_termination_"))
  
  console.log('🔍 Found clause fields:', clauseFields.length, clauseFields)
  console.log('🔍 Found renewal fields:', renewalFields.length, renewalFields)
  console.log('🔍 Found termination fields:', terminationFields.length, terminationFields)
  console.log('🔍 Total OCR results:', ocrResults.value.length)
  
  // Process all clause fields together to avoid duplicates
  const allClauseFields = [...clauseFields, ...renewalFields, ...terminationFields]
  
  // Remove duplicates based on clause text content
  const uniqueClauses = []
  const seenTexts = new Set()
  
  for (const clause of allClauseFields) {
    // Handle case where clause.value might be an object or non-string
    let clauseText = ''
    if (clause.value) {
      if (typeof clause.value === 'string') {
        clauseText = clause.value.trim()
      } else if (typeof clause.value === 'object') {
        // If it's an object, try to extract text or convert to string
        clauseText = (clause.value.text || clause.value.value || JSON.stringify(clause.value)).trim()
      } else {
        clauseText = String(clause.value).trim()
      }
    }
    
    if (clauseText && !seenTexts.has(clauseText)) {
      seenTexts.add(clauseText)
      uniqueClauses.push(clause)
    }
  }
  
  console.log('🔍 Unique clauses after deduplication:', uniqueClauses.length, uniqueClauses)
  
  const ocrClauses = uniqueClauses.map((clause, index) => {
    const metadata = clause.metadata || {}
    const fullClause = metadata.fullClause || {}
    
    // Ensure clause.value is a string
    let clauseValue = ''
    if (clause.value) {
      if (typeof clause.value === 'string') {
        clauseValue = clause.value
      } else if (typeof clause.value === 'object') {
        clauseValue = clause.value.text || clause.value.value || JSON.stringify(clause.value)
      } else {
        clauseValue = String(clause.value)
      }
    }
    
    // Determine clause type and name
    let clauseType = "standard"
    let clauseName = "Clause"
    let legalCategory = "Contract Terms"
    let riskLevel = "medium"
    
    if (clause.field.includes("renewal") || clause.field.includes("clause_renewal")) {
      clauseType = "renewal"
      clauseName = fullClause.name || metadata.name || "Renewal Terms"
      legalCategory = "Contract Renewal"
      riskLevel = "low"
    } else if (clause.field.includes("termination") || clause.field.includes("clause_termination")) {
      clauseType = "termination"
      clauseName = fullClause.name || metadata.name || "Termination Terms"
      legalCategory = "Contract Termination"
      riskLevel = "medium"
    } else {
      clauseName = clause.metadata?.name || clause.field.replace("clause_", "").replace(/_/g, " ")
    }
    
    return {
      clause_id: `${clauseType}_${Date.now()}_${index}`,
      clause_name: clauseName,
      clause_type: clauseType,
      clause_text: clauseValue,
      risk_level: riskLevel,
      legal_category: legalCategory,
      version_number: "1.0",
      is_standard: Boolean(fullClause.is_standard || false),
      created_by: getIntegerFieldValue("contract_owner"),
      // Renewal-specific fields
      notice_period_days: metadata.notice_period_days || fullClause.notice_period_days || null,
      auto_renew: clauseType === "renewal" ? Boolean(metadata.auto_renew || fullClause.auto_renew) : null,
      renewal_terms: clauseType === "renewal" ? (metadata.renewal_terms || fullClause.renewal_terms || clause.value) : null,
      // Termination-specific fields
      termination_notice_period: clauseType === "termination" ? (metadata.termination_notice_period || fullClause.termination_notice_period || null) : null,
      early_termination_fee: clauseType === "termination" ? (metadata.early_termination_fee || fullClause.early_termination_fee || null) : null,
      termination_conditions: clauseType === "termination" ? (metadata.termination_conditions || fullClause.termination_conditions || clause.value) : null
    }
  })

  // Add OCR terms and clauses to existing ones with proper reactivity
  if (ocrTerms.length > 0) {
    console.log('🔍 OCR Terms to add:', ocrTerms.length, ocrTerms)
    console.log('🔍 Current contractTerms before adding:', contractTerms.value.length, contractTerms.value)
    
    // Check for duplicates before adding
    const existingTermTitles = contractTerms.value.map(t => t.term_title)
    const newTerms = ocrTerms.filter(term => !existingTermTitles.includes(term.term_title))
    
    console.log('🔍 New terms after deduplication:', newTerms.length, newTerms)
    
    if (newTerms.length > 0) {
      // Create new reactive objects for each term
      const reactiveTerms = newTerms.map(term => reactive({ ...term }))
      contractTerms.value = [...contractTerms.value, ...reactiveTerms]
      
      console.log('✅ Added OCR contract terms:', newTerms.length)
    } else {
      console.log('⚠️ No new terms to add (all were duplicates)')
    }
    
    console.log('🔍 Updated contractTerms after adding:', contractTerms.value.length, contractTerms.value)
  }

  if (ocrClauses.length > 0) {
    console.log('🔍 OCR Clauses to add:', ocrClauses.length, ocrClauses)
    console.log('🔍 Current contractClauses before adding:', contractClauses.value.length, contractClauses.value)
    
    // Check for duplicates before adding
    const existingClauseNames = contractClauses.value.map(c => c.clause_name)
    const newClauses = ocrClauses.filter(clause => !existingClauseNames.includes(clause.clause_name))
    
    console.log('🔍 New clauses after deduplication:', newClauses.length, newClauses)
    
    if (newClauses.length > 0) {
      // Create new reactive objects for each clause
      const reactiveClauses = newClauses.map(clause => reactive({ ...clause }))
      contractClauses.value = [...contractClauses.value, ...reactiveClauses]
      
      console.log('✅ Added OCR contract clauses:', newClauses.length)
    } else {
      console.log('⚠️ No new clauses to add (all were duplicates)')
    }
    
    console.log('🔍 Updated contractClauses after adding:', contractClauses.value.length, contractClauses.value)
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
      'contract_title', 'contract_number', 'parent_contract_id', 'contract_value',
      'liability_cap', 'start_date', 'end_date', 'notice_period_days',
      'governing_law', 'contract_risk_score', 'renewal_terms'
    ]
    
    formFields.forEach(fieldId => {
      const input = document.getElementById(fieldId)
      if (input && formData.value[fieldId] !== undefined && formData.value[fieldId] !== null) {
        input.value = formData.value[fieldId] || ''
        input.dispatchEvent(new Event('input', { bubbles: true }))
        console.log(`🔧 Updated ${fieldId} field:`, input.value)
      }
    })
    
    // Update select fields
    const selectFields = ['contract_type', 'contract_category', 'priority', 'compliance_status']
    selectFields.forEach(fieldName => {
      const select = document.querySelector(`[data-field="${fieldName}"]`)
      if (select && formData.value[fieldName]) {
        select.value = formData.value[fieldName]
        select.dispatchEvent(new Event('change', { bubbles: true }))
        console.log(`🔧 Updated ${fieldName} select:`, select.value)
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
  const s3Status = s3UploadInfo.value?.success 
    ? '📁 Document has been securely stored in cloud storage'
    : '⚠️ Document processed but cloud storage is temporarily unavailable'
  
  const message = `✅ OCR data applied successfully!\n\n` +
    `📋 Form fields populated: ${totalFieldsApplied}\n` +
    `📄 Contract terms added: ${ocrTerms.length}\n` +
    `📑 Contract clauses added: ${ocrClauses.length}\n\n` +
    `${s3Status}\n\n` +
    `Please review the data in the form tabs and make any necessary adjustments.`
  
  PopupService.success(message, 'OCR Data Applied Successfully')
  
  console.log('✅ OCR data applied successfully:', ocrData)
  console.log('✅ Updated form data:', formData.value)
  console.log('✅ Total contract terms:', contractTerms.value.length)
  console.log('✅ Total contract clauses:', contractClauses.value.length)
  
  // Debug: Log all terms and clauses for verification
  console.log('🔍 All contract terms:', contractTerms.value.map(t => ({
    id: t.term_id,
    title: t.term_title,
    text: t.term_text?.substring(0, 50) + '...'
  })))
  
  console.log('🔍 All contract clauses:', contractClauses.value.map(c => ({
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

const getConfidenceBadge = (confidence) => {
  if (confidence >= 90) {
    return { class: 'bg-success/10 text-success border-success/20', text: `High (${confidence}%)` }
  } else if (confidence >= 70) {
    return { class: 'bg-warning/10 text-warning border-warning/20', text: `Medium (${confidence}%)` }
  } else {
    return { class: 'bg-destructive/10 text-destructive border-destructive/20', text: `Low (${confidence}%)` }
  }
}

// Methods for managing terms and clauses
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

const addNewTerm = () => {
  // Generate a unique term_id that will be preserved when saving
  // Use timestamp + random to ensure uniqueness even if multiple terms are added quickly
  // Add index to further ensure uniqueness
  const index = contractTerms.value.length
  const uniqueId = `${Date.now()}_${index}_${Math.random().toString(36).substr(2, 9)}`
  const newTerm = reactive({
    term_id: `term_${uniqueId}`,
    term_category: '',
    term_title: '',
    term_text: '',
    risk_level: 'Low',
    compliance_status: 'Pending',
    is_standard: false,
    approval_status: 'Pending',
    approved_by: '',
    approved_at: '',
    version_number: '1.0',
    parent_term_id: '',
    created_by: formData.value.owner || ''
  })
  
  // Use push to add the term and trigger reactivity
  contractTerms.value.push(newTerm)
  
  console.log('➕ Added new term with term_id:', newTerm.term_id)
  console.log('📋 Current contract terms:', contractTerms.value)
  console.log('📋 Contract terms length:', contractTerms.value.length)
}

const addNewClause = () => {
  const newClause = reactive({
    clause_id: `clause_${Date.now()}`,
    clause_name: '',
    clause_type: 'standard',
    clause_text: '',
    risk_level: 'low',
    legal_category: '',
    version_number: '1',
    is_standard: false,
    created_by: formData.value.owner || ''
  })
  
  // Use push to add the clause and trigger reactivity
  contractClauses.value.push(newClause)
  console.log('➕ Added new clause:', newClause)
}

const addNewRenewalClause = () => {
  const newClause = reactive({
    clause_id: `clause_${Date.now()}`,
    clause_name: 'Renewal Terms',
    clause_type: 'renewal',
    clause_text: '',
    risk_level: 'low',
    legal_category: 'Contract Renewal',
    version_number: '1',
    is_standard: false,
    created_by: formData.value.owner || '',
    notice_period_days: 30,
    auto_renew: false,
    renewal_terms: ''
  })
  contractClauses.value.push(newClause)
}

const addNewTerminationClause = () => {
  const newClause = reactive({
    clause_id: `clause_${Date.now()}`,
    clause_name: 'Termination Terms',
    clause_type: 'termination',
    clause_text: '',
    risk_level: 'medium',
    legal_category: 'Contract Termination',
    version_number: '1',
    is_standard: false,
    created_by: formData.value.owner || '',
    termination_notice_period: 30,
    early_termination_fee: 0,
    termination_conditions: ''
  })
  contractClauses.value.push(newClause)
}

const removeTerm = (index) => {
  const termToRemove = contractTerms.value[index]
  contractTerms.value = contractTerms.value.filter((_, i) => i !== index)

  if (termToRemove) {
    const termIdStr = String(termToRemove.term_id || '')
    if (termIdStr) {
      const updatedTemplates = allTermTemplates.value.filter(t => t.term_id !== termIdStr)
      if (updatedTemplates.length !== allTermTemplates.value.length) {
        allTermTemplates.value = updatedTemplates
      }
      if (selectedTemplates.value[termIdStr]) {
        const updatedSelected = { ...selectedTemplates.value }
        delete updatedSelected[termIdStr]
        selectedTemplates.value = updatedSelected
      }
      loadedTemplatesForTerms.value.delete(termIdStr)
      setTemplateSectionExpanded(termIdStr, false)
    }
  }
}

// Questionnaire state and functions
const allTermQuestionnaires = ref([])
const showQuestionnairesModal = ref(false)
const selectedTermTitle = ref('')
const selectedTermId = ref(null)
const selectedQuestionnaires = ref([])

// Template state and functions
const allTermTemplates = ref([]) // Store templates by term_id: { term_id: [templates] }
const selectedTemplates = ref({}) // Store selected template_id by term_id: { term_id: template_id }
const loadedTemplatesForTerms = ref(new Set()) // Track which terms have loaded templates
const expandedTemplateSections = ref({})

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

// Load questionnaires for all terms when component mounts or terms change
async function loadTermQuestionnaires() {
  try {
    // Load questionnaires for all unique term categories (preferred) or term titles
    const uniqueTermCategories = [...new Set(contractTerms.value.map(t => t.term_category).filter(Boolean))]
    // Also get unique term_ids for fallback matching
    const uniqueTermIds = [...new Set(contractTerms.value.map(t => t.term_id).filter(Boolean))]
    allTermQuestionnaires.value = []
    
    console.log('📋 Loading questionnaires for term categories:', uniqueTermCategories)
    console.log('📋 Also checking term IDs:', uniqueTermIds)
    
    // Load all questionnaires in parallel for better performance
    const loadPromises = []
    
    // Load by term_category (primary method) - parallelize by category
    for (const termCategory of uniqueTermCategories) {
      // Load by category only (no need to load by each term_id - category lookup is sufficient)
      loadPromises.push(
        apiService.getQuestionnairesByTermTitle(null, null, termCategory)
          .then(response => {
            const questionnaires = response.questionnaires || response.results || response || []
            return questionnaires.map(q => ({ 
              ...q, 
              term_category: termCategory,
              _matched_term_category: termCategory
            }))
          })
          .catch(error => {
            console.error(`Error loading questionnaires for term category "${termCategory}":`, error)
            return []
          })
      )
    }
    
    // Also try loading by term_id for any terms that might not have been matched by category
    for (const termId of uniqueTermIds) {
      const term = contractTerms.value.find(t => String(t.term_id) === String(termId))
      if (!term?.term_category) {
        // Only try by term_id if we don't have a category
        loadPromises.push(
          apiService.getQuestionnairesByTermTitle(null, termId, null)
            .then(response => {
              const questionnaires = response.questionnaires || response.results || response || []
              return questionnaires.map(q => ({ 
                ...q, 
                term_category: term?.term_category || '',
                _matched_term_id: termId
              }))
            })
            .catch(error => {
              console.error(`Error loading questionnaires for term_id "${termId}":`, error)
              return []
            })
        )
      }
    }
    
    // Wait for all API calls to complete in parallel
    const results = await Promise.all(loadPromises)
    
    // Flatten and combine all results
    const allQuestionnaires = results.flat()
    
    // Remove duplicates based on question_id
    const seenIds = new Set()
    allTermQuestionnaires.value = allQuestionnaires.filter(q => {
      if (seenIds.has(q.question_id)) {
        return false
      }
      seenIds.add(q.question_id)
      return true
    })
    
    console.log('📋 Total unique questionnaires loaded:', allTermQuestionnaires.value.length)
    
    // Force reactivity update
    allTermQuestionnaires.value = [...allTermQuestionnaires.value]
  } catch (error) {
    console.error('Error loading term questionnaires:', error)
  }
}

// Check if questionnaires exist for a term
function hasQuestionnaires(termTitle, termId) {
  if (!allTermQuestionnaires.value.length) return false
  
  // Get term_category from the term object
  const term = contractTerms.value.find(t => 
    (termTitle && t.term_title === termTitle) || 
    (termId && String(t.term_id) === String(termId))
  )
  const termCategory = term?.term_category
  
  if (!termCategory) return false
  
  // Check if any questionnaire matches by term_category or term_id (with format variations)
  return allTermQuestionnaires.value.some(q => {
    const qTermCategory = q.term_category || q._matched_term_category || ''
    const qTermId = String(q.term_id || '')
    const searchTermId = String(termId || '')
    
    // Match by term_category (case-insensitive) - PRIMARY METHOD
    if (qTermCategory.toLowerCase() === termCategory.toLowerCase()) {
      return true
    }
    
    // Match by term_id (exact or partial match) - FALLBACK
    if (termId && (qTermId === searchTermId || 
                   qTermId.includes(searchTermId) || 
                   searchTermId.includes(qTermId))) {
      return true
    }
    
    return false
  })
}

// Get questionnaire count for a term
function getQuestionnaireCount(termTitle, termId) {
  if (!allTermQuestionnaires.value.length) return 0
  
  // Get term_category from the term object
  const term = contractTerms.value.find(t => 
    (termTitle && t.term_title === termTitle) || 
    (termId && String(t.term_id) === String(termId))
  )
  const termCategory = term?.term_category
  
  if (!termCategory) return 0
  
  const searchTermId = String(termId || '')
  return allTermQuestionnaires.value.filter(q => {
    const qTermCategory = q.term_category || q._matched_term_category || ''
    const qTermId = String(q.term_id || '')
    
    // Match by term_category (case-insensitive) - PRIMARY METHOD
    if (qTermCategory.toLowerCase() === termCategory.toLowerCase()) {
      return true
    }
    
    // Match by term_id (exact or partial match) - FALLBACK
    if (termId && (qTermId === searchTermId || 
                   qTermId.includes(searchTermId) || 
                   searchTermId.includes(qTermId))) {
      return true
    }
    
    return false
  }).length
}

// Cache for template questions to avoid redundant API calls
const templateQuestionsCache = ref({}) // { template_id: questions[] }

// Pre-load ALL template questions for selected templates in parallel (OPTIMIZATION)
async function preloadAllTemplateQuestions() {
  try {
    const selectedTemplateIds = Object.values(selectedTemplates.value).filter(Boolean)
    if (selectedTemplateIds.length === 0) {
      console.log('📋 No templates selected, skipping pre-load')
      return
    }
    
    console.log(`📋 Pre-loading questions for ${selectedTemplateIds.length} selected templates in parallel...`)
    
    // Load all template questions in PARALLEL
    const loadPromises = selectedTemplateIds.map(async (templateId) => {
      // Skip if already cached
      if (templateQuestionsCache.value[templateId]) {
        console.log(`📋 Template ${templateId} already cached, skipping`)
        return
      }
      
      try {
        const response = await apiService.getTemplateQuestions(templateId, null, null)
        const questions = response.questions || []
        
        // Cache the questions
        templateQuestionsCache.value[templateId] = questions.map(q => ({
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
        
        console.log(`✅ Cached ${templateQuestionsCache.value[templateId].length} questions for template ${templateId}`)
      } catch (error) {
        console.error(`❌ Error loading questions for template ${templateId}:`, error)
      }
    })
    
    await Promise.all(loadPromises)
    console.log(`✅ Pre-loaded questions for ${selectedTemplateIds.length} templates`)
  } catch (error) {
    console.error('❌ Error in preloadAllTemplateQuestions:', error)
  }
}

// Get questionnaires for a specific term (used when saving)
// Now uses selected template if available, otherwise falls back to direct questionnaires
async function getQuestionnairesForTerm(termId, termCategory, termTitle) {
  const termIdStr = String(termId || '')
  
  // First, check if a template is selected for this term
  const selectedTemplateId = selectedTemplates.value[termIdStr]
  if (selectedTemplateId) {
    try {
      console.log(`📋 Using selected template ${selectedTemplateId} for term ${termIdStr}`)
      
      // Check cache first (OPTIMIZATION)
      if (templateQuestionsCache.value[selectedTemplateId]) {
        console.log(`📋 Using cached questions for template ${selectedTemplateId}`)
        return templateQuestionsCache.value[selectedTemplateId]
      }
      
      // If not cached, fetch from API
      const response = await apiService.getTemplateQuestions(selectedTemplateId, null, null)
      const questions = response.questions || []
      
      console.log(`✅ Retrieved ${questions.length} questions from template ${selectedTemplateId}`)
      
      // Convert template questions to the format expected by backend
      const formattedQuestions = questions.map(q => ({
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
        template_id: selectedTemplateId // Include template_id for reference
      }))
      
      // Cache for future use
      templateQuestionsCache.value[selectedTemplateId] = formattedQuestions
      
      console.log(`📋 Returning ${formattedQuestions.length} formatted questions from selected template`)
      return formattedQuestions
    } catch (error) {
      console.error(`❌ Error loading questions from template ${selectedTemplateId}:`, error)
      // Don't fall back - if template is selected but fails to load, return empty
      // This prevents accidentally using wrong questionnaires
      return []
    }
  }
  
  // Fallback to direct questionnaires (legacy behavior)
  if (!allTermQuestionnaires.value.length) return []
  
  const searchTermCategory = termCategory || ''
  
  // Filter questionnaires that match this term
  const matchingQuestionnaires = allTermQuestionnaires.value.filter(q => {
    const qTermCategory = q.term_category || q._matched_term_category || ''
    const qTermId = String(q.term_id || '')
    
    // Match by term_category (case-insensitive) - PRIMARY METHOD
    if (searchTermCategory && qTermCategory.toLowerCase() === searchTermCategory.toLowerCase()) {
      return true
    }
    
    // Match by term_id (exact or partial match) - FALLBACK
    if (termId && (qTermId === termIdStr || 
                   qTermId.includes(termIdStr) || 
                   termIdStr.includes(qTermId))) {
      return true
    }
    
    return false
  })
  
  // Return questionnaires in the format expected by backend
  return matchingQuestionnaires.map(q => ({
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

// Load templates for a term
async function loadTemplatesForTerm(termOrTitle, termIdArg = null, termCategoryArg = null) {
  try {
    let term
    if (typeof termOrTitle === 'object' && termOrTitle !== null) {
      term = termOrTitle
    } else {
      term = {
        term_title: termOrTitle,
        term_id: termIdArg,
        term_category: termCategoryArg
      }
    }

    const termIdStr = String(term?.term_id || '')
    const termTitle = term?.term_title || ''
    const termCategory = term?.term_category || ''

    console.log('📋 Loading templates for term:', { termTitle, termId: termIdStr, termCategory })
    
    // Only make API call if we have at least termCategory or termTitle
    if (!termCategory && !termTitle && !termIdStr) {
      console.warn('⚠️ No term category, title, or ID provided - skipping template load')
      loadedTemplatesForTerms.value.add(termIdStr || 'empty')
      return
    }
    
    const response = await apiService.getTemplatesByTerm(termTitle, termIdStr, termCategory)
    const templates = response.templates || response || []
    
    console.log(`✅ Loaded ${templates.length} templates for term ${termIdStr}`)
    
    // Store templates for this term
    if (!allTermTemplates.value.find(t => t.term_id === termIdStr)) {
      allTermTemplates.value.push({
        term_id: termIdStr,
        templates: templates
      })
    } else {
      // Update existing entry
      const entry = allTermTemplates.value.find(t => t.term_id === termIdStr)
      if (entry) {
        entry.templates = templates
      }
    }
    
    // Mark as loaded
    loadedTemplatesForTerms.value.add(termIdStr)
    
    // Force reactivity
    allTermTemplates.value = [...allTermTemplates.value]
    
    // If no templates were found, we simply leave the list empty without showing a popup
  } catch (error) {
    console.error('❌ Error loading templates:', error)
    
    // Don't show error popup for 500 errors if it's likely a backend issue
    // Just log it and mark as loaded so we don't keep retrying
    if (error.message && error.message.includes('500')) {
      console.warn('⚠️ Server error loading templates - this may be a backend issue')
      const termIdStr = String(termOrTitle?.term_id || termIdArg || '')
      loadedTemplatesForTerms.value.add(termIdStr)
      // Don't show popup for server errors - just silently fail
      return
    }
    
    // Only show popup for client-side errors (401, 403, network errors)
    if (error.message && !error.message.includes('500')) {
      PopupService.error(`Failed to load templates: ${error.message || 'Please try again.'}`, 'Error')
    }
  }
}

// Get templates for a specific term
function getTemplatesForTerm(termId) {
  if (!termId) return []
  const termIdStr = String(termId)
  const entry = allTermTemplates.value.find(t => t.term_id === termIdStr)
  return entry?.templates || []
}

// Check if templates have been loaded for a term
function hasLoadedTemplatesForTerm(termId) {
  if (!termId) return false
  return loadedTemplatesForTerms.value.has(String(termId))
}

// Get selected template for a term
function getSelectedTemplateForTerm(termId) {
  if (!termId) return null
  const termIdStr = String(termId)
  const selectedTemplateId = selectedTemplates.value[termIdStr]
  if (!selectedTemplateId) return null
  
  const templates = getTemplatesForTerm(termId)
  return templates.find(t => t.template_id === selectedTemplateId) || null
}

// Select a template for a term
function selectTemplateForTerm(termId, template) {
  const termIdStr = String(termId)
  selectedTemplates.value[termIdStr] = template.template_id
  // Force reactivity
  selectedTemplates.value = { ...selectedTemplates.value }
  console.log(`✅ Selected template ${template.template_id} for term ${termIdStr}`)
}

// Clear template selection for a term
function clearTemplateSelection(termId) {
  const termIdStr = String(termId)
  delete selectedTemplates.value[termIdStr]
  // Force reactivity
  selectedTemplates.value = { ...selectedTemplates.value }
  console.log(`✅ Cleared template selection for term ${termIdStr}`)
}

// View questions from a template
async function viewTemplateQuestions(termId, templateId) {
  try {
    const termIdStr = String(termId || '')
    const term = contractTerms.value.find(t => String(t.term_id) === String(termId))
    const termCategory = term?.term_category || ''
    
    console.log('📋 Loading questions for template:', { templateId, termId: termIdStr, termCategory })
    
    const response = await apiService.getTemplateQuestions(templateId, termIdStr, termCategory)
    const questions = response.questions || []
    
    console.log(`✅ Loaded ${questions.length} questions from template ${templateId}`)
    
    // Convert template questions to the format expected by the modal
    selectedQuestionnaires.value = questions.map(q => ({
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
    
    selectedTermTitle.value = term?.term_title || 'Unknown Term'
    selectedTermId.value = termIdStr
    showQuestionnairesModal.value = true
  } catch (error) {
    console.error('❌ Error loading template questions:', error)
    PopupService.error(`Failed to load template questions: ${error.message || 'Please try again.'}`, 'Error')
  }
}

// Helper function to map answer_type to question_type
function mapAnswerTypeToQuestionType(answerType) {
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

// View questionnaires for a term
async function viewQuestionnaires(termTitle, termId) {
  console.log('🔍 viewQuestionnaires called with:', { termTitle, termId })
  
  // Clear any previous questionnaire data to ensure fresh fetch
  selectedQuestionnaires.value = []
  
  // Get term_category from the term object - try multiple lookup strategies
  let term = null
  
  // First try to find by term_id (most reliable)
  if (termId) {
    term = contractTerms.value.find(t => String(t.term_id) === String(termId))
    console.log('🔍 Found term by term_id:', term)
  }
  
  // If not found, try by term_title
  if (!term && termTitle) {
    term = contractTerms.value.find(t => t.term_title === termTitle)
    console.log('🔍 Found term by term_title:', term)
  }
  
  // If still not found, try by both
  if (!term) {
    term = contractTerms.value.find(t => 
      (termTitle && t.term_title === termTitle) || 
      (termId && String(t.term_id) === String(termId))
    )
    console.log('🔍 Found term by combined search:', term)
  }
  
  if (!term) {
    console.error('❌ Term not found:', { termTitle, termId, availableTerms: contractTerms.value })
    PopupService.error('Term not found. Please try again.', 'Error')
    return
  }
  
  const termCategory = term.term_category
  const actualTermTitle = term.term_title || termTitle || 'Unknown Term'
  const actualTermId = term.term_id || termId
  
  console.log('📋 Using term data:', { 
    termCategory, 
    actualTermTitle, 
    actualTermId,
    term 
  })
  
  if (!termCategory) {
    console.warn('⚠️ No term_category found for term! Using term_title instead.')
  } else {
    console.log('✅ Using term_category for matching:', termCategory)
  }
  
  // Set the modal title using the actual term title from the found term
  selectedTermTitle.value = actualTermTitle
  selectedTermId.value = actualTermId
  
  try {
    // Always fetch fresh data from API - don't use cached data
    // Only pass term_title if we don't have term_category (to ensure backend prioritizes term_category)
    const apiTermTitle = termCategory ? null : actualTermTitle
    console.log('📤 Calling API with (fresh fetch):', { 
      termTitle: apiTermTitle, 
      termId: actualTermId, 
      termCategory,
      note: termCategory ? 'Using term_category (term_title will be ignored)' : 'Using term_title (no term_category available)'
    })
    const response = await apiService.getQuestionnairesByTermTitle(apiTermTitle, actualTermId, termCategory)
    console.log('📥 API response:', response)
    
    // Always set from fresh API response, never use cached data
    selectedQuestionnaires.value = response.questionnaires || response.results || response || []
    console.log('✅ Questionnaires loaded (fresh):', selectedQuestionnaires.value.length)
    
    if (selectedQuestionnaires.value.length === 0) {
      console.warn('⚠️ No questionnaires found in response')
      PopupService.warning(`No questionnaires found for term category "${termCategory}".`, 'No Questionnaires Found')
    }
    
    showQuestionnairesModal.value = true
  } catch (error) {
    console.error('❌ Error loading questionnaires:', error)
    PopupService.error(`Failed to load questionnaires: ${error.message || 'Please try again.'}`, 'Error')
  }
}

// Close questionnaires modal
function closeQuestionnairesModal() {
  showQuestionnairesModal.value = false
  selectedTermTitle.value = ''
  selectedTermId.value = null
  selectedQuestionnaires.value = [] // Clear selected questionnaires to prevent stale data
}

// Edit questionnaires for a term (with existing questions pre-populated)
function editQuestionnaires(termTitle, termId, existingQuestionnaires = []) {
  // Get term_category and term_id from the term object
  const term = contractTerms.value.find(t => 
    (termTitle && t.term_title === termTitle) || 
    (termId && String(t.term_id) === String(termId))
  )
  
  if (!term) {
    console.error('❌ Term not found for editing questionnaires:', { termTitle, termId })
    return
  }
  
  // Use the term's actual term_id, not the parameter (which might be outdated)
  const actualTermId = term.term_id || termId || ''
  const termCategory = term.term_category || ''
  const actualTermTitle = term.term_title || termTitle || 'Term'
  
  console.log('📋 Editing questionnaires for term:', {
    term_id: actualTermId,
    term_title: actualTermTitle,
    term_category: termCategory,
    existing_questions_count: existingQuestionnaires.length
  })
  
  // Save current form data to sessionStorage before navigating
  sessionStorage.setItem('contract_draft_data', JSON.stringify({
    formData: formData.value,
    contractTerms: contractTerms.value,
    contractClauses: contractClauses.value
  }))
  
  // Store existing questionnaires in sessionStorage for QuestionnaireTemplates to load
  if (existingQuestionnaires && existingQuestionnaires.length > 0) {
    // Convert questionnaires to the format expected by QuestionnaireTemplates
    const questionsForTemplate = existingQuestionnaires.map((q, index) => {
      // Map question_type to answer_type
      let answerType = 'TEXT'
      if (q.question_type) {
        answerType = mapQuestionTypeToAnswerType(q.question_type)
      } else if (q.answer_type) {
        // If answer_type is already present, use it
        answerType = q.answer_type
      }
      
      return {
        question_text: q.question_text || '',
        help_text: q.help_text || '',
        question_category: q.question_category || '',
        answer_type: answerType,
        is_required: q.is_required !== undefined ? q.is_required : false,
        weightage: q.scoring_weightings !== undefined ? q.scoring_weightings : (q.weightage !== undefined ? q.weightage : 10.0),
        term_id: actualTermId,
        allow_document_upload: q.allow_document_upload !== undefined ? q.allow_document_upload : false,
        options: Array.isArray(q.options) ? q.options : [],
        _optionsString: Array.isArray(q.options) && q.options.length > 0 ? q.options.join(', ') : '',
        metric_name: q.metric_name || null
      }
    })
    
    sessionStorage.setItem('questionnaire_edit_data', JSON.stringify({
      questions: questionsForTemplate,
      term_id: actualTermId,
      term_title: actualTermTitle,
      term_category: termCategory
    }))
    console.log(`📋 Stored ${questionsForTemplate.length} questions for editing`)
  }
  
  // Close the modal
  closeQuestionnairesModal()
  
  router.push({
    path: '/questionnaire-templates',
    query: { 
      module_type: 'CONTRACT',
      term_id: actualTermId,
      term_title: actualTermTitle,
      term_category: termCategory,
      return_to: 'contract-create',
      edit_mode: existingQuestionnaires.length > 0 ? 'true' : 'false'
    }
  })
}

// Helper function to map question_type to answer_type
function mapQuestionTypeToAnswerType(questionType) {
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

// Create questionnaires for a term (new, no existing questions)
function createQuestionnaires(termTitle, termId) {
  // Get term_category and term_id from the term object
  // Always use the term's actual term_id to ensure consistency
  const term = contractTerms.value.find(t => 
    (termTitle && t.term_title === termTitle) || 
    (termId && String(t.term_id) === String(termId))
  )
  
  if (!term) {
    console.error('❌ Term not found for creating questionnaires:', { termTitle, termId })
    PopupService.error('Term not found. Please try again.', 'Error')
    return
  }
  
  // Use the term's actual term_id, not the parameter (which might be outdated)
  const actualTermId = term.term_id || termId || ''
  const termCategory = term.term_category || ''
  const actualTermTitle = term.term_title || termTitle || 'Term'
  
  console.log('📋 Creating questionnaires for term:', {
    term_id: actualTermId,
    term_title: actualTermTitle,
    term_category: termCategory
  })
  
  PopupService.confirm(
    `Create questionnaires for "${actualTermTitle}"? You will be redirected to the Questionnaire Templates page to create questions for this term. After saving, you'll return here to complete the contract creation.`,
    'Create Questionnaires',
    () => {
      // Save current form data to sessionStorage before navigating
      sessionStorage.setItem('contract_draft_data', JSON.stringify({
        formData: formData.value,
        contractTerms: contractTerms.value,
        contractClauses: contractClauses.value
      }))
      
      router.push({
        path: '/questionnaire-templates',
        query: { 
          module_type: 'CONTRACT',
          term_id: actualTermId,  // Use the actual term_id from the term object
          term_title: actualTermTitle,
          term_category: termCategory,
          return_to: 'contract-create'
        }
      })
    }
  )
}

// Watch term_category changes to reload templates and questionnaires
let questionnairesTimer = null
watch(() => contractTerms.value.map(t => t.term_category), async (newCategories, oldCategories) => {
  // Debounce to avoid too many API calls
  if (questionnairesTimer) {
    clearTimeout(questionnairesTimer)
  }
  questionnairesTimer = setTimeout(async () => {
    // OPTIMIZATION: Load templates for ALL terms in PARALLEL
    const termsToLoad = contractTerms.value.filter(term => 
      term.term_category && term.term_id && !hasLoadedTemplatesForTerm(term.term_id)
    )
    
    if (termsToLoad.length > 0) {
      console.log(`🔄 Auto-loading templates for ${termsToLoad.length} terms in PARALLEL...`)
      
      // Load all templates in parallel instead of sequentially
      await Promise.all(
        termsToLoad.map(term => 
          loadTemplatesForTerm(term).catch(err => {
            console.error(`Error loading templates for term ${term.term_id}:`, err)
          })
        )
      )
      
      console.log(`✅ Finished loading templates for ${termsToLoad.length} terms`)
    }
    
    // Also load questionnaires (legacy support)
    await loadTermQuestionnaires()
  }, 1000)
}, { deep: true })

// Watch activeTab to reload templates and questionnaires when switching to terms tab
// This is especially useful after returning from questionnaire templates
watch(activeTab, async (newTab, oldTab) => {
  if (newTab === 'terms' && contractTerms.value.length > 0) {
    console.log('🔄 Switched to terms tab, reloading templates and questionnaires...')
    // Clear cached data and modal state
    allTermQuestionnaires.value = []
    allTermTemplates.value = []
    loadedTemplatesForTerms.value.clear()
    expandedTemplateSections.value = {}
    closeQuestionnairesModal()
    // Small delay to ensure tab is fully rendered
    setTimeout(async () => {
      // OPTIMIZATION: Load templates for all terms with categories in PARALLEL
      const termsToLoad = contractTerms.value.filter(term => term.term_category && term.term_id)
      
      if (termsToLoad.length > 0) {
        console.log(`🔄 Loading templates for ${termsToLoad.length} terms in PARALLEL...`)
        
        await Promise.all(
          termsToLoad.map(term => 
            loadTemplatesForTerm(term).catch(err => {
              console.error(`Error loading templates for term ${term.term_id}:`, err)
            })
          )
        )
      }
      
      // Also load questionnaires (legacy support)
      await loadTermQuestionnaires()
      console.log('✅ Templates and questionnaires reloaded after switching to terms tab')
    }, 300)
  }
})

// Watch for route changes to detect when returning from QuestionnaireTemplates
// This ensures questionnaires are refreshed when navigating back
watch(() => [route.path, route.query.tab], async ([newPath, newTab], [oldPath, oldTab]) => {
  // Check if we're on the create contract page and terms tab is active
  if ((newPath === '/contracts/create' || newPath === '/contracts/new') && newTab === 'terms' && contractTerms.value.length > 0) {
    // Check if we just navigated to this tab (wasn't on terms tab before)
    if (oldTab !== 'terms') {
      console.log('🔄 Detected navigation to terms tab, clearing and reloading questionnaires...')
      // Clear all cached questionnaires to force fresh reload
      allTermQuestionnaires.value = []
      // Close any open modals
      closeQuestionnairesModal()
      // Clear sessionStorage cache
      sessionStorage.removeItem('questionnaire_edit_data')
      // Reload questionnaires immediately
      await loadTermQuestionnaires()
      console.log('✅ Questionnaires reloaded after navigating to terms tab')
    }
  }
}, { immediate: false })

const removeClause = (clauseId) => {
  if (Array.isArray(contractClauses.value)) {
  contractClauses.value = contractClauses.value.filter(c => c.clause_id !== clauseId)
  } else {
    console.warn('contractClauses.value is not an array in removeClause:', contractClauses.value);
    contractClauses.value = [];
  }
}

const updateTerm = (index, field, value) => {
  const updatedTerms = [...contractTerms.value]
  updatedTerms[index][field] = value
  contractTerms.value = updatedTerms
}

const updateClause = (clauseId, field, value) => {
  if (!contractClauses.value || !Array.isArray(contractClauses.value)) {
    console.warn('contractClauses is not an array:', contractClauses.value)
    return
  }
  
  const updatedClauses = contractClauses.value.map(c =>
    c?.clause_id === clauseId ? { ...c, [field]: value } : c
  )
  contractClauses.value = updatedClauses
}

// Helper method to transform form data for API
const prepareContractData = () => {
  const contractData = { ...formData.value }
  
  // Convert string numbers to actual numbers
  if (contractData.contract_value) {
    contractData.contract_value = parseFloat(contractData.contract_value)
  }
  if (contractData.liability_cap) {
    contractData.liability_cap = parseFloat(contractData.liability_cap)
  }
  if (contractData.parent_contract_id) {
    contractData.parent_contract_id = parseInt(contractData.parent_contract_id)
  }
  if (contractData.main_contract_id) {
    contractData.main_contract_id = parseInt(contractData.main_contract_id)
  }
  
  // Ensure proper boolean values for Django
  
  // Handle JSON fields - convert empty objects to null or omit them
  const jsonFields = ['insurance_requirements', 'data_protection_clauses', 'custom_fields']
  jsonFields.forEach(field => {
    if (contractData[field] && Object.keys(contractData[field]).length === 0) {
      // If it's an empty object, set to null
      contractData[field] = null
    }
  })
  
  // Remove display-only fields
  delete contractData.vendor_name
  
  return contractData
}

// Helper method to display success message
const showSuccessMessage = (message, redirectPath = null) => {
  successMessage.value = message
  
  if (redirectPath) {
    setTimeout(() => {
      go(redirectPath)
    }, 2000)
  }
}

// Trigger risk analysis in the background (non-blocking)
const triggerRiskAnalysis = async (contractId) => {
  try {
    console.log(`🔄 Triggering risk analysis for contract ${contractId} in background...`)
    
    // Call the trigger endpoint using the contractsApi service (which includes auth headers)
    contractsApi.triggerContractRiskAnalysis(contractId)
      .then(data => {
        if (data.success) {
          console.log(`✅ Risk analysis triggered successfully for contract ${contractId}:`, data.message)
        } else {
          console.warn(`⚠️ Failed to trigger risk analysis for contract ${contractId}:`, data.message)
        }
      })
      .catch(error => {
        console.error(`❌ Error triggering risk analysis for contract ${contractId}:`, error)
        console.error(`❌ Error details:`, error.message)
      })
    
    // Don't wait for the response - this is fire-and-forget
  } catch (error) {
    console.error(`❌ Error in triggerRiskAnalysis for contract ${contractId}:`, error)
  }
}

// Clear session storage (debug function)
const clearSessionStorage = () => {
  sessionStorage.removeItem('subcontractData')
  sessionStorage.removeItem('contractPreviewData')
  console.log('🧹 Session storage cleared')
  PopupService.success('Session storage cleared! You can now create a standalone contract.', 'Storage Cleared')
}
</script>
