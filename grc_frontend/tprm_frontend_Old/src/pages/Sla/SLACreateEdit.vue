<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <Button variant="ghost" size="sm" @click="goBack">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"></polyline></svg>
          Back to SLA List
        </Button>
        <div>
          <h1 class="text-3xl font-bold">Create New SLA</h1>
          <p class="text-muted-foreground">Define service level agreement terms and metrics</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="loadExampleData">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><path d="M14 2v6h6"/></svg>
          Load Example
        </Button>
        <Button variant="outline" @click="clearForm">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
          Clear Form
        </Button>
        <Button variant="outline" @click="handleSaveDraft">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/><path d="M7 3H4a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h16a1 1 0 0 0 1-1V8l-5-5Z"/></svg>
          Save as Draft
        </Button>
        <Button @click="handleSubmitForApproval">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13"/><path d="M22 2 15 22 11 13 2 9 22 2z"/></svg>
          Submit for Approval
        </Button>
      </div>
    </div>

    <!-- Document Upload Section -->
    <Card v-if="!extractedData">
      <CardHeader>
        <CardTitle>SLA Document Upload & OCR Processing</CardTitle>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <div class="flex items-start gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-600 mt-0.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
            <div class="text-sm">
              <p class="font-medium text-blue-900 mb-1">Real OCR Processing</p>
              <p class="text-blue-700">
                Upload your SLA document (PDF, DOC, DOCX, TXT, or images). The document will be:
              </p>
              <ul class="list-disc list-inside mt-2 space-y-1 text-blue-700">
                <li>Stored securely in S3</li>
                <li>Processed with AI-powered OCR</li>
                <li>Analyzed using LLaMA to extract SLA data</li>
                <li>Automatically populate form fields</li>
              </ul>
            </div>
          </div>
        </div>
        
        <div class="border-2 border-dashed border-muted-foreground/25 rounded-lg p-6 text-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto mb-2 text-muted-foreground" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><path d="M14 2v6h6"/></svg>
          <p class="text-sm text-muted-foreground mb-3">
            Supports: PDF, DOC, DOCX, TXT, PNG, JPG, JPEG (Max 50MB)
          </p>
          <Button variant="outline" @click="handleDocumentUpload">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 5 17 10"/><line x1="12" y1="5" x2="12" y2="20"/></svg>
            Upload & Process Document
          </Button>
        </div>

        <div v-if="isProcessing" class="space-y-3">
          <div class="flex items-center justify-between text-sm">
            <div class="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/></svg>
              <span class="font-medium">Processing document with AI-powered OCR...</span>
            </div>
            <span class="font-medium">{{ ocrProgress }}%</span>
          </div>
          <!-- Simple progress bar -->
          <div class="w-full h-2 bg-muted rounded overflow-hidden">
            <div class="h-2 bg-primary rounded transition-all duration-500" :style="{ width: ocrProgress + '%' }"></div>
          </div>
          <div class="text-xs text-muted-foreground space-y-1">
            <p>✓ Uploading to S3...</p>
            <p>✓ Running OCR on document...</p>
            <p>✓ Extracting SLA data with LLaMA AI...</p>
            <p class="animate-pulse">⏳ Mapping fields to form...</p>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Extracted Data Preview -->
    <Card v-else>
      <CardHeader>
        <div class="flex items-center justify-between">
          <CardTitle>Extracted SLA Data from OCR</CardTitle>
          <div class="flex items-center gap-2">
            <Button variant="outline" size="sm" @click="extractedData = null">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              Upload New
            </Button>
            <Button size="sm" @click="applyExtractedData">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              Apply to Form
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <div v-if="extractedData.document_url" class="bg-muted p-3 rounded-lg flex items-center justify-between">
            <div class="flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><path d="M14 2v6h6"/></svg>
              <div>
                <p class="text-sm font-medium">Document stored in S3</p>
                <p class="text-xs text-muted-foreground">ID: {{ extractedData.document_id }}</p>
              </div>
            </div>
            <a :href="extractedData.document_url" target="_blank" class="text-primary hover:underline text-sm">
              View Document
            </a>
          </div>
          
          <div class="grid grid-cols-3 gap-4 text-sm">
            <div>
              <p class="font-medium">SLA Name</p>
              <p class="text-muted-foreground">{{ extractedData.sla_name || 'Not extracted' }}</p>
            </div>
            <div>
              <p class="font-medium">Vendor</p>
              <p class="text-muted-foreground">{{ extractedData.vendor_id ? `${getVendorName(extractedData.vendor_id)} (ID: ${extractedData.vendor_id})` : 'Not extracted' }}</p>
            </div>
            <div>
              <p class="font-medium">Contract</p>
              <p class="text-muted-foreground">{{ extractedData.contract_id ? `${getContractName(extractedData.contract_id)} (ID: ${extractedData.contract_id})` : 'Not extracted' }}</p>
            </div>
            <div>
              <p class="font-medium">SLA Type</p>
              <p class="text-muted-foreground capitalize">{{ extractedData.sla_type || 'Not extracted' }}</p>
            </div>
            <div>
              <p class="font-medium">Effective Period</p>
              <p class="text-muted-foreground">{{ extractedData.effective_date && extractedData.expiry_date ? `${extractedData.effective_date} - ${extractedData.expiry_date}` : 'Not extracted' }}</p>
            </div>
            <div>
              <p class="font-medium">Business Service</p>
              <p class="text-muted-foreground">{{ extractedData.business_service_impacted || 'Not extracted' }}</p>
            </div>
            <div>
              <p class="font-medium">Compliance Framework</p>
              <p class="text-muted-foreground">{{ extractedData.compliance_framework || 'Not extracted' }}</p>
            </div>
            <div>
              <p class="font-medium">Priority</p>
              <p class="text-muted-foreground">{{ extractedData.priority || 'Not extracted' }}</p>
            </div>
            <div>
              <p class="font-medium">Compliance Score</p>
              <p class="text-muted-foreground">{{ extractedData.compliance_score ? `${extractedData.compliance_score}%` : 'Not extracted' }}</p>
            </div>
          </div>
          
          <div v-if="extractedData.metrics && extractedData.metrics.length > 0">
            <p class="font-medium mb-2">Extracted Metrics ({{ extractedData.metrics.length }})</p>
            <div class="space-y-2">
              <div v-for="(metric, i) in extractedData.metrics" :key="i" class="flex items-center justify-between p-3 border rounded-lg bg-muted/50">
                <div class="flex-1">
                  <p class="font-medium">{{ metric.metric_name || 'Unnamed Metric' }}</p>
                  <p class="text-sm text-muted-foreground mt-1">
                    Target: {{ metric.target_value || metric.threshold || 'N/A' }} {{ metric.measurement_unit || '' }}
                  </p>
                </div>
                <Badge variant="outline">{{ metric.measurement_frequency || metric.frequency || 'N/A' }}</Badge>
              </div>
            </div>
          </div>
          <div v-else>
            <p class="text-sm text-muted-foreground">No metrics extracted from document</p>
          </div>
        </div>
      </CardContent>
    </Card>

    <!-- Form -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6" :key="formKey">
      <!-- Main Form -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Basic Details -->
        <Card>
          <CardHeader>
            <CardTitle>Basic Details</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="text-sm">SLA Name *</label>
                <input 
                  v-model="formData.sla_name" 
                  placeholder="Enter SLA name" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              <div>
                <label class="text-sm">Vendor *</label>
                <select 
                  v-model="formData.vendor_id" 
                  :disabled="vendorsLoading"
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">
                    {{ vendorsLoading ? 'Loading vendors...' : 'Select Vendor' }}
                  </option>
                  <option v-for="vendor in vendors" :key="vendor.vendor_id" :value="vendor.vendor_id">
                    {{ vendor.company_name }}
                  </option>
                </select>
                <div v-if="!vendorsLoading && vendors.length === 0" class="text-xs text-red-500 mt-1">
                  No vendors available. Please check the backend connection.
                </div>
              </div>
              <div>
                <label class="text-sm">Contract *</label>
                <select 
                  v-model="formData.contract_id" 
                  :disabled="contractsLoading"
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">
                    {{ contractsLoading ? 'Loading contracts...' : 'Select Contract' }}
                  </option>
                  <option v-for="contract in contracts" :key="contract.contract_id" :value="contract.contract_id">
                    {{ contract.contract_name }}
                  </option>
                </select>
                <div v-if="!contractsLoading && contracts.length === 0" class="text-xs text-red-500 mt-1">
                  No contracts available. Please check the backend connection.
                </div>
              </div>
              <div>
                <label class="text-sm">SLA Type *</label>
                <input 
                  v-model="formData.sla_type" 
                  placeholder="e.g., AVAILABILITY, RESPONSE_TIME, RESOLUTION_TIME, QUALITY, CUSTOM" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              <div>
                <label class="text-sm">Effective Date *</label>
                <input 
                  type="date" 
                  v-model="formData.effective_date" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              <div>
                <label class="text-sm">Expiry Date *</label>
                <input 
                  type="date" 
                  v-model="formData.expiry_date" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              <div>
                <label class="text-sm">Business Service Impacted</label>
                <input 
                  v-model="formData.business_service_impacted" 
                  placeholder="e.g., Database Services" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              <div>
                <label class="text-sm">Reporting Frequency</label>
                <input 
                  v-model="formData.reporting_frequency" 
                  placeholder="e.g., daily, weekly, monthly, quarterly" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="text-sm">Baseline Period</label>
                <input 
                  v-model="formData.baseline_period" 
                  placeholder="e.g., Q1 2024" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              <div>
                <label class="text-sm">Penalty Threshold (%)</label>
                <input 
                  v-model="formData.penalty_threshold" 
                  type="number" 
                  step="0.01" 
                  placeholder="5.00" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              <div>
                <label class="text-sm">Credit Threshold (%)</label>
                <input 
                  v-model="formData.credit_threshold" 
                  type="number" 
                  step="0.01" 
                  placeholder="2.00" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
            </div>
            <div>
              <label class="text-sm">Improvement Targets (JSON)</label>
              <textarea
                class="w-full rounded-md border bg-background p-2 text-sm"
                rows="2"
                v-model="formData.improvement_targets"
                placeholder='{"availability": "99.95%", "response_time": "< 150ms"}'
              />
            </div>
            <div>
              <label class="text-sm">Measurement Methodology</label>
              <textarea
                class="w-full rounded-md border bg-background p-2 text-sm"
                rows="3"
                v-model="formData.measurement_methodology"
                placeholder="Describe how metrics will be measured and calculated"
              />
            </div>
            <div>
              <label class="text-sm">Exclusions</label>
              <textarea
                class="w-full rounded-md border bg-background p-2 text-sm"
                rows="2"
                v-model="formData.exclusions"
                placeholder="List any exclusions or exceptions to the SLA"
              />
            </div>
            <div>
              <label class="text-sm">Force Majeure Clauses</label>
              <textarea
                class="w-full rounded-md border bg-background p-2 text-sm"
                rows="2"
                v-model="formData.force_majeure_clauses"
                placeholder="Define force majeure conditions"
              />
            </div>
            <div>
              <label class="text-sm">Audit Requirements</label>
              <textarea
                class="w-full rounded-md border bg-background p-2 text-sm"
                rows="2"
                v-model="formData.audit_requirements"
                placeholder="Specify audit requirements and frequency"
              />
            </div>
              <div>
                <label class="text-sm">Document Versioning</label>
                <input 
                  v-model="formData.document_versioning" 
                  placeholder="e.g., v1.0" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
              <div>
                <label class="text-sm">Priority *</label>
                <select 
                  v-model="formData.priority" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">Select Priority</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="LOW">Low</option>
                </select>
              </div>
              <div>
                <label class="text-sm">Approval Status</label>
                <input 
                  v-model="formData.approval_status" 
                  readonly
                  class="flex h-10 w-full rounded-md border border-input bg-muted px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
          </CardContent>
        </Card>

        <!-- Metrics Definition -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <CardTitle>Metrics & Thresholds</CardTitle>
              <Button variant="outline" size="sm" @click="addMetric">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Add Metric
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div class="space-y-4">
              <div v-for="(metric, index) in formData.metrics" :key="index" class="border rounded-lg p-4">
                <div class="flex items-center justify-between mb-4">
                  <h4 class="font-medium">Metric {{ index + 1 }}</h4>
                  <Button v-if="formData.metrics.length > 1" variant="ghost" size="sm" class="text-status-critical" @click="removeMetric(index)">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
                  </Button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label class="text-sm">Metric Name</label>
                    <div class="relative">
                      <input 
                        v-model="metric.metric_name" 
                        :list="`metric-names-${index}`"
                        placeholder="Select or type metric name" 
                        :disabled="staticMetricsLoading"
                        class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      />
                      <datalist :id="`metric-names-${index}`">
                        <option v-for="name in staticMetricNames" :key="name" :value="name">
                          {{ name }}
                        </option>
                      </datalist>
                    </div>
                    <div v-if="staticMetricsLoading" class="text-xs text-gray-500 mt-1">
                      Loading metric names...
                    </div>
                    <div v-else-if="staticMetricNames.length > 0" class="text-xs text-blue-600 mt-1">

                    </div>
                  </div>
                  <div>
                    <label class="text-sm">Target Value</label>
                    <input 
                      v-model="metric.target_value" 
                      type="number" 
                      step="0.01" 
                      placeholder="e.g., 99.9" 
                      class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <label class="text-sm">Measurement Unit</label>
                    <input 
                      v-model="metric.measurement_unit" 
                      placeholder="e.g., %, ms, sec, min, hours, days, count, ratio" 
                      class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <label class="text-sm">Measurement Frequency</label>
                    <select 
                      v-model="metric.measurement_frequency" 
                      class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      <option value="">Select Frequency</option>
                      <option value="DAILY">Daily</option>
                      <option value="WEEKLY">Weekly</option>
                      <option value="MONTHLY">Monthly</option>
                      <option value="QUARTERLY">Quarterly</option>
                    </select>
                  </div>
                  <div>
                    <label class="text-sm">Penalty Clause</label>
                    <input 
                      v-model="metric.penalty_clause" 
                      placeholder="e.g., 5% service credit" 
                      class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <label class="text-sm">Measurement Methodology</label>
                    <input 
                      v-model="metric.measurement_methodology" 
                      placeholder="e.g., Automated monitoring" 
                      class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                  </div>
                </div>
                
                <!-- Questionnaires Button -->
                <div v-if="metric.metric_name" class="mt-4 pt-4 border-t">
                  <div class="flex items-center justify-between">
                    <div class="text-sm text-muted-foreground">
                      Questionnaires for this metric
                    </div>
                    <div class="flex gap-2">
                      <Button 
                        v-if="hasQuestionnaires(metric.metric_name)" 
                        variant="outline" 
                        size="sm" 
                        @click="viewQuestionnaires(metric.metric_name)"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                        View {{ getQuestionnaireCount(metric.metric_name) }} Questions
                      </Button>
                      <Button 
                        v-else 
                        variant="outline" 
                        size="sm" 
                        @click="createQuestionnaires(metric.metric_name)"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        Create Questionnaires
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Framework Mapping -->
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <CardTitle>Framework Mapping</CardTitle>
              <Button variant="outline" size="sm" @click="loadFrameworks" :disabled="frameworksLoading">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M3 21v-5h5"/></svg>
                {{ frameworksLoading ? 'Loading...' : 'Refresh' }}
              </Button>
            </div>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="text-sm">Compliance Framework *</label>
                <select 
                  v-model="formData.compliance_framework" 
                  :disabled="frameworksLoading"
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="">
                    {{ frameworksLoading ? 'Loading frameworks...' : 'Select Framework' }}
                  </option>
                  <option v-for="framework in frameworks" :key="framework.FrameworkId" :value="framework.FrameworkName">
                    {{ framework.FrameworkName }} (v{{ framework.CurrentVersion }}) - {{ framework.Category }}
                  </option>
                </select>
                <div v-if="!frameworksLoading && frameworks.length === 0" class="text-xs text-red-500 mt-1">
                  No frameworks available. Please check the backend connection.
                </div>
              </div>
              <div>
                <label class="text-sm">Compliance Score (%)</label>
                <input 
                  v-model="formData.compliance_score" 
                  type="number" 
                  step="0.01" 
                  min="0" 
                  max="100" 
                  placeholder="e.g., 95.50" 
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
            </div>
            <div v-if="selectedFramework" class="mt-4 p-4 bg-muted rounded-lg">
              <h4 class="font-medium mb-2">Selected Framework Details</h4>
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="font-medium">Framework ID:</span>
                  <span class="ml-2">{{ selectedFramework.FrameworkId }}</span>
                </div>
                <div>
                  <span class="font-medium">Category:</span>
                  <span class="ml-2">{{ selectedFramework.Category }}</span>
                </div>
                <div>
                  <span class="font-medium">Version:</span>
                  <span class="ml-2">{{ selectedFramework.CurrentVersion }}</span>
                </div>
                <div>
                  <span class="font-medium">Status:</span>
                  <span class="ml-2">{{ selectedFramework.Status }}</span>
                </div>
                <div>
                  <span class="font-medium">Active/Inactive:</span>
                  <span class="ml-2">{{ selectedFramework.ActiveInactive }}</span>
                </div>
                <div>
                  <span class="font-medium">Internal/External:</span>
                  <span class="ml-2">{{ selectedFramework.InternalExternal }}</span>
                </div>
                <div>
                  <span class="font-medium">Effective Date:</span>
                  <span class="ml-2">{{ selectedFramework.EffectiveDate }}</span>
                </div>
                <div>
                  <span class="font-medium">Start Date:</span>
                  <span class="ml-2">{{ selectedFramework.StartDate }}</span>
                </div>
                <div>
                  <span class="font-medium">End Date:</span>
                  <span class="ml-2">{{ selectedFramework.EndDate }}</span>
                </div>
                <div>
                  <span class="font-medium">Reviewer:</span>
                  <span class="ml-2">{{ selectedFramework.Reviewer }}</span>
                </div>
                <div>
                  <span class="font-medium">Created By:</span>
                  <span class="ml-2">{{ selectedFramework.CreatedByName }}</span>
                </div>
                <div>
                  <span class="font-medium">Created Date:</span>
                  <span class="ml-2">{{ selectedFramework.CreatedByDate }}</span>
                </div>
                <div v-if="selectedFramework.Identifier">
                  <span class="font-medium">Identifier:</span>
                  <span class="ml-2">{{ selectedFramework.Identifier }}</span>
                </div>
                <div class="col-span-2">
                  <span class="font-medium">Description:</span>
                  <p class="mt-1 text-muted-foreground">{{ selectedFramework.FrameworkDescription }}</p>
                </div>
                <div v-if="selectedFramework.DocURL" class="col-span-2">
                  <span class="font-medium">Documentation:</span>
                  <a :href="selectedFramework.DocURL" target="_blank" class="ml-2 text-primary hover:underline">
                    View Documentation
                  </a>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Status -->
        <Card>
          <CardHeader>
            <CardTitle>Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-sm">Status:</span>
                <span class="text-sm font-medium text-status-warning">{{ isDraft ? 'Draft' : 'Pending Approval' }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm">Version:</span>
                <span class="text-sm">1.0</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm">Created:</span>
                <span class="text-sm">{{ createdDate }}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Validation -->
        <Card>
          <CardHeader>
            <CardTitle>Validation</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="space-y-2">
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="formData.sla_name ? 'bg-green-500' : 'bg-red-500'"></div>
                <span class="text-sm">SLA Name {{ formData.sla_name ? '✓' : 'required' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="formData.vendor_id ? 'bg-green-500' : 'bg-red-500'"></div>
                <span class="text-sm">Vendor {{ formData.vendor_id ? '✓' : 'required' }}</span>
                <span v-if="formData.vendor_id" class="text-xs text-muted-foreground">({{ getVendorName(formData.vendor_id) }})</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="formData.contract_id ? 'bg-green-500' : 'bg-red-500'"></div>
                <span class="text-sm">Contract {{ formData.contract_id ? '✓' : 'required' }}</span>
                <span v-if="formData.contract_id" class="text-xs text-muted-foreground">({{ getContractName(formData.contract_id) }})</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="formData.sla_type ? 'bg-green-500' : 'bg-red-500'"></div>
                <span class="text-sm">SLA Type {{ formData.sla_type ? '✓' : 'required' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="formData.effective_date ? 'bg-green-500' : 'bg-red-500'"></div>
                <span class="text-sm">Effective Date {{ formData.effective_date ? '✓' : 'required' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="formData.expiry_date ? 'bg-green-500' : 'bg-red-500'"></div>
                <span class="text-sm">Expiry Date {{ formData.expiry_date ? '✓' : 'required' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="formData.metrics && formData.metrics.length > 0 ? 'bg-green-500' : 'bg-red-500'"></div>
                <span class="text-sm">At least one metric {{ formData.metrics && formData.metrics.length > 0 ? '✓' : 'required' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="formData.compliance_framework ? 'bg-green-500' : 'bg-red-500'"></div>
                <span class="text-sm">Compliance Framework {{ formData.compliance_framework ? '✓' : 'required' }}</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="w-2 h-2 rounded-full" :class="formData.priority ? 'bg-green-500' : 'bg-red-500'"></div>
                <span class="text-sm">Priority {{ formData.priority ? '✓' : 'required' }}</span>
              </div>
            </div>
          </CardContent>
        </Card>

         <!-- Help -->
         <Card>
           <CardHeader>
             <CardTitle>Help & Guidelines</CardTitle>
           </CardHeader>
           <CardContent>
             <div class="text-sm text-muted-foreground space-y-2">
               <p>• Use clear, measurable metrics</p>
               <p>• Define realistic thresholds</p>
               <p>• Include appropriate penalties</p>
               <p>• Specify measurement methods</p>
             </div>
           </CardContent>
         </Card>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
  
  <!-- Questionnaires Modal -->
  <div v-if="showQuestionnairesModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="closeQuestionnairesModal">
    <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden" @click.stop>
      <div class="flex items-center justify-between p-6 border-b">
        <h2 class="text-2xl font-bold">Questionnaires for "{{ selectedMetricName }}"</h2>
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
          No questionnaires found for this metric.
        </div>
      </div>
      <div class="flex items-center justify-end gap-3 p-6 border-t bg-gray-50">
        <Button variant="outline" @click="closeQuestionnairesModal">Close</Button>
        <Button @click="editQuestionnaires(selectedMetricName)">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          Edit Questionnaires
        </Button>
      </div>
    </div>
  </div>
  
</template>

<script setup>
import { ref, reactive, computed, nextTick, watch } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useRouter } from 'vue-router'
import apiService from '@/services/api'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import { usePermissions } from '@/composables/usePermissions'
import loggingService from '@/services/loggingService'
import { getTprmApiUrl } from '@/utils/backendEnv.js'

const router = useRouter()
const { showSLASuccess, showSLAError, showSLAWarning, showInfo } = useNotifications()
const { withPermissionCheck } = usePermissions()

const isDraft = ref(true)
const createdDate = computed(() => new Date().toLocaleDateString())
const formKey = ref(0)

// OCR simulation state
const ocrProgress = ref(0)
const isProcessing = ref(false)
const extractedData = ref(null)

// Framework data
const frameworks = ref([])
const frameworksLoading = ref(false)
const selectedFramework = computed(() => {
  return frameworks.value.find(f => f.FrameworkName === formData.compliance_framework)
})

// Vendor and Contract data
const vendors = ref([])
const contracts = ref([])
const vendorsLoading = ref(false)
const contractsLoading = ref(false)

// Metric names from static_questionnaires
const staticMetricNames = ref([])
const staticMetricsLoading = ref(false)

// All questionnaires data
const allQuestionnaires = ref([])

// Modal state for viewing questionnaires
const showQuestionnairesModal = ref(false)
const selectedMetricName = ref('')
const selectedQuestionnaires = ref([])

// Form data - starts empty, use "Load Example" button to populate
const formData = reactive({
  sla_name: '',
  vendor_id: '',
  contract_id: '',
  sla_type: '',
  effective_date: '',
  expiry_date: '',
  status: 'PENDING',
  business_service_impacted: '',
  reporting_frequency: 'monthly',
  baseline_period: '',
  improvement_targets: '',
  penalty_threshold: '',
  credit_threshold: '',
  measurement_methodology: '',
  exclusions: '',
  force_majeure_clauses: '',
  compliance_framework: '',
  audit_requirements: '',
  document_versioning: '',
  compliance_score: '',
  priority: '',
  approval_status: 'PENDING',
  metrics: [
    { 
      metric_name: '', 
      target_value: '', 
      measurement_unit: '', 
      measurement_frequency: 'MONTHLY', 
      penalty_clause: '', 
      measurement_methodology: '' 
    }
  ]
})

// Watch form data changes for debugging
watch(formData, (newData) => {
  console.log('Form data changed:', newData)
}, { deep: true })

// Load frameworks on component mount
async function loadFrameworks() {
  frameworksLoading.value = true
  try {
    console.log('Loading frameworks from API...')
    frameworks.value = await apiService.getFrameworks()
    console.log('Frameworks loaded successfully:', frameworks.value)
  } catch (error) {
    console.error('Error loading frameworks:', error)
    // Show error message to user
    PopupService.error('Error loading compliance frameworks. Please refresh the page and try again.', 'Loading Error')
    frameworks.value = []
  } finally {
    frameworksLoading.value = false
  }
}

// Load vendors
async function loadVendors() {
  vendorsLoading.value = true
  try {
    console.log('Loading vendors from API...')
    vendors.value = await apiService.getVendors()
    console.log('Vendors loaded successfully:', vendors.value)
  } catch (error) {
    console.error('Error loading vendors:', error)
    PopupService.error('Error loading vendors. Please refresh the page and try again.', 'Loading Error')
    vendors.value = []
  } finally {
    vendorsLoading.value = false
  }
}

// Load contracts
async function loadContracts() {
  contractsLoading.value = true
  try {
    console.log('Loading contracts from API...')
    contracts.value = await apiService.getContracts()
    console.log('Contracts loaded successfully:', contracts.value)
  } catch (error) {
    console.error('Error loading contracts:', error)
    PopupService.error('Error loading contracts. Please refresh the page and try again.', 'Loading Error')
    contracts.value = []
  } finally {
    contractsLoading.value = false
  }
}

// Load static metric names from static_questionnaires table
async function loadStaticMetricNames() {
  staticMetricsLoading.value = true
  try {
    console.log('Loading static metric names from API...')
    
    // Fetch all questionnaires with a large page size to get all records
    const response = await apiService.getAllStaticQuestionnaires()
    
    // Handle both paginated and non-paginated responses
    const questionnaires = response.results || response || []
    console.log('All questionnaires loaded:', questionnaires.length)
    
    // Store all questionnaires for later use
    allQuestionnaires.value = questionnaires
    
    // Extract unique metric names
    const uniqueMetricNames = [...new Set(
      questionnaires
        .map(q => q.metric_name)
        .filter(name => name && name.trim() !== '')
    )].sort()
    
    staticMetricNames.value = uniqueMetricNames
    console.log('Static metric names loaded successfully:', staticMetricNames.value.length, 'unique metrics')
    console.log('Metric names:', staticMetricNames.value)
  } catch (error) {
    console.error('Error loading static metric names:', error)
    PopupService.error('Error loading metric names. You can still enter custom metric names.', 'Loading Error')
    staticMetricNames.value = []
    allQuestionnaires.value = []
  } finally {
    staticMetricsLoading.value = false
  }
}

// Helper functions to get names by ID
function getVendorName(vendorId) {
  if (!vendorId || !vendors.value.length) return ''
  const vendor = vendors.value.find(v => v.vendor_id == vendorId)
  return vendor ? vendor.company_name : 'Unknown Vendor'
}

function getContractName(contractId) {
  if (!contractId || !contracts.value.length) return ''
  const contract = contracts.value.find(c => c.contract_id == contractId)
  return contract ? contract.contract_name : 'Unknown Contract'
}

// Questionnaire helper functions
function hasQuestionnaires(metricName) {
  if (!metricName || !allQuestionnaires.value.length) return false
  return allQuestionnaires.value.some(q => q.metric_name === metricName)
}

function getQuestionnaireCount(metricName) {
  if (!metricName || !allQuestionnaires.value.length) return 0
  return allQuestionnaires.value.filter(q => q.metric_name === metricName).length
}

async function viewQuestionnaires(metricName) {
  selectedMetricName.value = metricName
  selectedQuestionnaires.value = allQuestionnaires.value.filter(q => q.metric_name === metricName)
  showQuestionnairesModal.value = true
}

function closeQuestionnairesModal() {
  showQuestionnairesModal.value = false
  selectedMetricName.value = ''
  selectedQuestionnaires.value = []
}

function editQuestionnaires(metricName) {
  // Navigate to questionnaire templates page with metric name filter
  router.push({
    path: '/questionnaire-templates',
    query: { metric: metricName }
  })
}

function createQuestionnaires(metricName) {
  PopupService.confirm(
    `Create questionnaires for "${metricName}"? You will be redirected to the Questionnaire Templates page to create questions for this metric. After saving, you'll return here to complete the SLA creation.`,
    'Create Questionnaires',
    () => {
      // Save current form data to sessionStorage before navigating
      sessionStorage.setItem('sla_draft_data', JSON.stringify(formData))
      
      router.push({
        path: '/questionnaire-templates',
        query: { 
          module_type: 'SLA',
          metric_name: metricName,
          return_to: 'sla-create'
        }
      })
    }
  )
}

// Restore draft data if returning from questionnaire creation
async function restoreDraftData() {
  const draftData = sessionStorage.getItem('sla_draft_data')
  if (draftData) {
    try {
      const parsedData = JSON.parse(draftData)
      Object.assign(formData, parsedData)
      sessionStorage.removeItem('sla_draft_data')
      
      // Reload questionnaires to get newly created questions
      await loadStaticMetricNames()
      
      // Force reactivity
      formKey.value++
      
      // Show success message
      PopupService.success('Your SLA draft has been restored. Questionnaires have been refreshed with the newly created questions.', 'Draft Restored')
      
      console.log('Draft data restored successfully and questionnaires reloaded')
    } catch (error) {
      console.error('Error restoring draft data:', error)
      sessionStorage.removeItem('sla_draft_data')
    }
  }
}

// Load data when component mounts
loadFrameworks()
loadVendors()
loadContracts()
loadStaticMetricNames()

// Check if returning from questionnaire creation
setTimeout(() => {
  restoreDraftData()
}, 500)


function goBack() {
  router.push('/slas')
}

async function loadExampleData() {
  PopupService.confirm(
    'Load example data? This will replace any existing form data.',
    'Load Example Data',
    async () => {
      console.log('Loading example data...')
      console.log('Form data before:', formData)
      
      // Create new form data object to ensure reactivity
      const newFormData = {
      sla_name: 'Oracle Database Service Level Agreement',
      vendor_id: vendors.value.length > 0 ? vendors.value[0].vendor_id.toString() : '1',
      contract_id: contracts.value.length > 0 ? contracts.value[0].contract_id.toString() : '1',
      sla_type: 'AVAILABILITY',
      effective_date: '2024-01-01',
      expiry_date: '2024-12-31',
      status: 'PENDING',
      business_service_impacted: 'Database Services',
      reporting_frequency: 'monthly',
      baseline_period: 'Q1 2024',
      improvement_targets: '{"availability": "99.95%", "response_time": "< 150ms"}',
      penalty_threshold: '5.00',
      credit_threshold: '2.00',
      measurement_methodology: 'Automated monitoring with 24/7 system checks',
      exclusions: 'Scheduled maintenance windows, force majeure events',
      force_majeure_clauses: 'Natural disasters, cyber attacks, third-party failures',
      compliance_framework: frameworks.value.length > 0 ? frameworks.value[0].FrameworkName : 'ISO 27001',
      audit_requirements: 'Quarterly compliance audits',
      document_versioning: 'v1.0',
      compliance_score: '95.50',
      priority: 'HIGH',
      approval_status: 'PENDING',
      metrics: [
        { 
          metric_name: 'Database Availability', 
          target_value: '99.90', 
          measurement_unit: '%', 
          measurement_frequency: 'MONTHLY', 
          penalty_clause: '5% service credit for each 0.1% below target', 
          measurement_methodology: 'Automated uptime monitoring' 
        },
        { 
          metric_name: 'Response Time', 
          target_value: '200.00', 
          measurement_unit: 'ms', 
          measurement_frequency: 'DAILY', 
          penalty_clause: '2% service credit for exceeding threshold', 
          measurement_methodology: 'Real-time performance monitoring' 
        }
      ]
    }
    
    // Clear existing data first
    Object.keys(formData).forEach(key => {
      if (key === 'metrics') {
        formData[key] = []
      } else {
        formData[key] = ''
      }
    })
    
    // Wait for clearing
    await nextTick()
    
    // Assign new data
    Object.assign(formData, newFormData)
    
    // Wait for DOM to update
    await nextTick()
    
    // Force reactivity by updating the form key
    setTimeout(() => {
      console.log('Form data after:', formData)
      console.log('SLA Name value:', formData.sla_name)
      console.log('Vendor ID value:', formData.vendor_id)
      console.log('Contract ID value:', formData.contract_id)
      console.log('SLA Type value:', formData.sla_type)
      console.log('Effective Date value:', formData.effective_date)
      console.log('Expiry Date value:', formData.expiry_date)
      console.log('Business Service value:', formData.business_service_impacted)
      console.log('Reporting Frequency value:', formData.reporting_frequency)
      console.log('Baseline Period value:', formData.baseline_period)
      console.log('Penalty Threshold value:', formData.penalty_threshold)
      console.log('Credit Threshold value:', formData.credit_threshold)
      console.log('Measurement Methodology value:', formData.measurement_methodology)
      console.log('Exclusions value:', formData.exclusions)
      console.log('Force Majeure value:', formData.force_majeure_clauses)
      console.log('Compliance Framework value:', formData.compliance_framework)
      console.log('Audit Requirements value:', formData.audit_requirements)
      console.log('Document Versioning value:', formData.document_versioning)
      console.log('Improvement Targets value:', formData.improvement_targets)
      console.log('Metrics count:', formData.metrics.length)
      console.log('First metric name:', formData.metrics[0]?.metric_name)
      console.log('Second metric name:', formData.metrics[1]?.metric_name)
      
      // Force reactivity by updating the form key
      formKey.value++
      PopupService.success('Example data loaded successfully! You can now see the form populated with sample SLA data.', 'Data Loaded')
    }, 100)
    }
  )
}

function clearForm() {
  PopupService.confirm(
    'Are you sure you want to clear all form data? This action cannot be undone.',
    'Clear Form',
    () => {
      // Reset form data to empty values using individual assignments for better reactivity
      formData.sla_name = ''
    formData.vendor_id = ''
    formData.contract_id = ''
    formData.sla_type = ''
    formData.effective_date = ''
    formData.expiry_date = ''
    formData.status = 'PENDING'
    formData.business_service_impacted = ''
    formData.reporting_frequency = 'monthly'
    formData.baseline_period = ''
    formData.improvement_targets = ''
    formData.penalty_threshold = ''
    formData.credit_threshold = ''
    formData.measurement_methodology = ''
    formData.exclusions = ''
    formData.force_majeure_clauses = ''
    formData.compliance_framework = ''
    formData.audit_requirements = ''
    formData.document_versioning = ''
    formData.compliance_score = ''
    formData.priority = ''
    formData.approval_status = 'PENDING'
    
    // Reset metrics to single empty metric
    formData.metrics = [
      { 
        metric_name: '', 
        target_value: '', 
        measurement_unit: '', 
        measurement_frequency: 'MONTHLY', 
        penalty_clause: '', 
        measurement_methodology: '' 
      }
    ]
    
    // Force reactivity by updating the form key
    formKey.value++
    PopupService.success('Form cleared successfully!', 'Form Cleared')
    }
  )
}

async function handleDocumentUpload() {
  // Create file input element
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.pdf,.doc,.docx,.txt,.png,.jpg,.jpeg'
  input.onchange = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    // Validate file size (50MB max)
    if (file.size > 50 * 1024 * 1024) {
      PopupService.warning('File size exceeds 50MB limit. Please select a smaller file.', 'File Too Large')
      return
    }

    isProcessing.value = true
    ocrProgress.value = 0

    // Start progress animation
    const progressInterval = setInterval(() => {
      if (ocrProgress.value < 90) {
        ocrProgress.value += 5
      }
    }, 500)

    try {
      console.log('Uploading document for OCR processing...')
      
      // Get authentication token (using 'session_token' as the key)
      const token = localStorage.getItem('session_token') || sessionStorage.getItem('session_token')
      
      if (!token) {
        console.error('❌ No authentication token found in localStorage or sessionStorage')
        throw new Error('Authentication token not found. Please log in and try again.')
      }
      
      // Create FormData for file upload
      const uploadFormData = new FormData()
      uploadFormData.append('file', file)
      uploadFormData.append('title', file.name)
      uploadFormData.append('description', 'SLA document for extraction')
      uploadFormData.append('category', 'SLA')
      uploadFormData.append('department', 'Compliance')
      uploadFormData.append('doc_type', file.name.split('.').pop().toUpperCase())
      uploadFormData.append('module_id', '1')
      // Include reporting_frequency as fallback (will be overridden by AI extraction if found)
      uploadFormData.append('reporting_frequency', formData.reporting_frequency || 'monthly')

      // Upload document and process with OCR
      const uploadUrl = getTprmApiUrl('ocr/upload/')
      const response = await fetch(uploadUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: uploadFormData,
        // Don't set Content-Type header - let browser set it with boundary
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Upload failed with status ${response.status}`)
      }

      const result = await response.json()
      console.log('OCR processing result:', result)

      // Complete progress
      clearInterval(progressInterval)
      ocrProgress.value = 100

      if (result.success && result.extracted_data) {
        // Map the extracted data to form fields
        const extracted = result.extracted_data
        
        extractedData.value = {
          sla_name: extracted.sla_name || '',
          vendor_id: extracted.vendor_id || (vendors.value.length > 0 ? vendors.value[0].vendor_id.toString() : ''),
          contract_id: extracted.contract_id || (contracts.value.length > 0 ? contracts.value[0].contract_id.toString() : ''),
          sla_type: extracted.sla_type || '',
          effective_date: extracted.effective_date || '',
          expiry_date: extracted.expiry_date || '',
          status: extracted.status || 'PENDING',
          business_service_impacted: extracted.business_service_impacted || '',
          reporting_frequency: extracted.reporting_frequency || 'monthly',
          baseline_period: extracted.baseline_period || '',
          improvement_targets: typeof extracted.improvement_targets === 'string' 
            ? extracted.improvement_targets 
            : JSON.stringify(extracted.improvement_targets || {}),
          penalty_threshold: extracted.penalty_threshold?.toString() || '',
          credit_threshold: extracted.credit_threshold?.toString() || '',
          measurement_methodology: extracted.measurement_methodology || '',
          exclusions: extracted.exclusions || '',
          force_majeure_clauses: extracted.force_majeure_clauses || '',
          compliance_framework: extracted.compliance_framework || (frameworks.value.length > 0 ? frameworks.value[0].FrameworkName : ''),
          audit_requirements: extracted.audit_requirements || '',
          document_versioning: extracted.document_versioning || 'v1.0',
          compliance_score: extracted.compliance_score?.toString() || '',
          priority: extracted.priority || '',
          approval_status: extracted.approval_status || 'PENDING',
          metrics: extracted.metrics || []
        }

        // Store document info for reference
        extractedData.value.document_id = result.document.DocumentId
        extractedData.value.document_url = result.upload_info?.file_info?.url || result.document.DocumentLink
        
        setTimeout(() => {
          isProcessing.value = false
          createSLANotification(
            'SLA Document Processed', 
            `Document "${file.name}" has been uploaded and processed. Confidence: ${result.processing_info.extraction_confidence.toFixed(2)}%`, 
            'success'
          )
          PopupService.success(`Document processed successfully!\n\nExtraction Confidence: ${result.processing_info.extraction_confidence.toFixed(2)}%\n\nYou can now review and apply the extracted data to the form.`, 'Document Processed')
        }, 500)
      } else {
        throw new Error('OCR processing completed but no data was extracted. Please check the document format.')
      }
    } catch (error) {
      clearInterval(progressInterval)
      isProcessing.value = false
      ocrProgress.value = 0
      
      console.error('Document upload error:', error)
      PopupService.error(`Error processing document: ${error.message}\n\nPlease try again with a different document or check the OCR service status.`, 'Upload Failed')
      
      createSLANotification('Document Upload Failed', error.message, 'error')
    }
  }
  input.click()
}

function applyExtractedData() {
  if (extractedData.value) {
    console.log('Applying extracted data:', extractedData.value)
    
    // Apply extracted data to form, excluding internal fields
    const excludedFields = ['document_id', 'document_url', 'metrics']
    
    Object.keys(extractedData.value).forEach(key => {
      if (!excludedFields.includes(key) && extractedData.value[key]) {
        formData[key] = extractedData.value[key]
      }
    })
    
    // Apply metrics if they exist - normalize field names
    if (extractedData.value.metrics && extractedData.value.metrics.length > 0) {
      formData.metrics = extractedData.value.metrics.map(metric => ({
        metric_name: metric.metric_name || '',
        target_value: metric.target_value || metric.threshold || '',
        measurement_unit: metric.measurement_unit || '',
        measurement_frequency: metric.measurement_frequency || metric.frequency || 'MONTHLY',
        penalty_clause: metric.penalty_clause || metric.penalty || '',
        measurement_methodology: metric.measurement_methodology || ''
      }))
      console.log('Applied metrics:', formData.metrics)
    }
    
    // Force reactivity
    formKey.value++
    
    setTimeout(() => {
      PopupService.success(`Extracted data applied successfully!\n\nFields populated: ${Object.keys(extractedData.value).filter(k => !excludedFields.includes(k) && extractedData.value[k]).length}\nMetrics: ${formData.metrics.length}`, 'Data Applied')
    }, 100)
  }
}

function addMetric() {
  formData.metrics.push({ 
    metric_name: '', 
    target_value: '', 
    measurement_unit: '', 
    measurement_frequency: '', 
    penalty_clause: '', 
    measurement_methodology: '' 
  })
}

function removeMetric(index) {
  formData.metrics = formData.metrics.filter((_, i) => i !== index)
}

async function handleSaveDraft() {
  try {
    formData.status = 'PENDING'
    
    // Transform form data to match vendor_slas table schema
    const slaData = {
      vendor_id: parseInt(formData.vendor_id),
      contract_id: parseInt(formData.contract_id),
      sla_name: formData.sla_name,
      sla_type: formData.sla_type,
      effective_date: formData.effective_date,
      expiry_date: formData.expiry_date,
      status: 'PENDING',
      business_service_impacted: formData.business_service_impacted,
      reporting_frequency: formData.reporting_frequency,
      baseline_period: formData.baseline_period,
      improvement_targets: typeof formData.improvement_targets === 'string' 
        ? JSON.parse(formData.improvement_targets || '{}') 
        : formData.improvement_targets,
      penalty_threshold: parseFloat(formData.penalty_threshold || 0),
      credit_threshold: parseFloat(formData.credit_threshold || 0),
      measurement_methodology: formData.measurement_methodology,
      exclusions: formData.exclusions,
      force_majeure_clauses: formData.force_majeure_clauses,
      compliance_framework: formData.compliance_framework,
      audit_requirements: formData.audit_requirements,
      document_versioning: formData.document_versioning,
      compliance_score: parseFloat(formData.compliance_score || 0) || 0,
      priority: formData.priority,
      approval_status: formData.approval_status,
      // Metrics will be stored separately in sla_metrics table
      metrics: formData.metrics.map(metric => ({
        metric_name: metric.metric_name,
        threshold: parseFloat(metric.target_value || 0),
        measurement_unit: metric.measurement_unit,
        frequency: normalizeFrequency(metric.measurement_frequency),
        penalty: metric.penalty_clause,
        measurement_methodology: metric.measurement_methodology
      }))
    }
    
    const response = await saveSLA(slaData)
    
    if (response) {
      isDraft.value = true
      
      // Show info notification
      await showInfo('SLA Draft Saved', `SLA "${formData.sla_name}" has been saved as draft.`, {
        sla_name: formData.sla_name,
        action: 'draft_saved'
      })
      
      PopupService.success('Draft saved successfully!', 'Draft Saved')
    } else {
      await showSLAError('create_failed', 'Unexpected response format', {
        sla_name: formData.sla_name
      })
      PopupService.error('Error saving draft: Unexpected response format', 'Save Failed')
    }
  } catch (error) {
    console.error('Error saving draft:', error)
    
    // Show error notification
    await showSLAError('create_failed', error.message || 'Unknown error occurred', {
      sla_name: formData.sla_name
    })
    
    PopupService.error('Error saving draft. Please try again.', 'Save Failed')
  }
}

async function handleSubmitForApproval() {
  try {
    // Validate required fields
    if (!formData.sla_name || !formData.vendor_id || !formData.contract_id || !formData.sla_type || !formData.compliance_framework || !formData.priority) {
      PopupService.warning('Please fill in all required fields before submitting.', 'Missing Required Fields')
      return
    }

    if (!formData.metrics || formData.metrics.length === 0) {
      PopupService.warning('Please add at least one metric before submitting.', 'Missing Metrics')
      return
    }

    formData.status = 'PENDING'
    
    // Transform form data to match vendor_slas table schema
    const slaData = {
      vendor_id: parseInt(formData.vendor_id),
      contract_id: parseInt(formData.contract_id),
      sla_name: formData.sla_name,
      sla_type: formData.sla_type,
      effective_date: formData.effective_date,
      expiry_date: formData.expiry_date,
      status: 'PENDING',
      business_service_impacted: formData.business_service_impacted,
      reporting_frequency: formData.reporting_frequency,
      baseline_period: formData.baseline_period,
      improvement_targets: typeof formData.improvement_targets === 'string' 
        ? JSON.parse(formData.improvement_targets || '{}') 
        : formData.improvement_targets,
      penalty_threshold: parseFloat(formData.penalty_threshold || 0),
      credit_threshold: parseFloat(formData.credit_threshold || 0),
      measurement_methodology: formData.measurement_methodology,
      exclusions: formData.exclusions,
      force_majeure_clauses: formData.force_majeure_clauses,
      compliance_framework: formData.compliance_framework,
      audit_requirements: formData.audit_requirements,
      document_versioning: formData.document_versioning,
      compliance_score: parseFloat(formData.compliance_score || 0) || 0,
      priority: formData.priority,
      approval_status: 'PENDING',
      // Metrics will be stored separately in sla_metrics table
      metrics: formData.metrics.map(metric => ({
        metric_name: metric.metric_name,
        threshold: parseFloat(metric.target_value || 0),
        measurement_unit: metric.measurement_unit,
        frequency: normalizeFrequency(metric.measurement_frequency),
        penalty: metric.penalty_clause,
        measurement_methodology: metric.measurement_methodology
      }))
    }
    
    console.log('Normalized SLA Data for submission:', slaData)
    console.log('Normalized Metrics:', slaData.metrics)
    
    const response = await saveSLA(slaData)
    
    if (response && response.sla_id) {
      isDraft.value = false
      
      // Show success notification
      await showSLASuccess('submitted', {
        sla_id: response.sla_id,
        sla_name: formData.sla_name
      })
      
      // Show success popup and navigate on close
      PopupService.success('SLA submitted for approval successfully! Now you need to assign it to a reviewer.', 'Submitted Successfully')
      PopupService.onAction('ok', () => {
        // Navigate to SLA Approval Assignment page with SLA ID parameter
        router.push(`/slas/approval-assignment?slaId=${response.sla_id}&objectType=SLA_CREATION`)
      })
    } else {
      await showSLAError('submission_failed', 'Unexpected response format', {
        sla_name: formData.sla_name
      })
      PopupService.error('Error submitting SLA: Unexpected response format', 'Submission Failed')
    }
  } catch (error) {
    console.error('Error submitting SLA:', error)
    
    // Show error notification
    await showSLAError('submission_failed', error.message || 'Unknown error occurred', {
      sla_name: formData.sla_name
    })
    
    PopupService.error('Error submitting SLA. Please try again.', 'Submission Failed')
  }
}

// Helper function to normalize frequency values
function normalizeFrequency(frequency) {
  if (!frequency) return 'MONTHLY'
  
  // Convert to uppercase and remove spaces
  const normalized = frequency.toString().toUpperCase().trim()
  
  // Map common variations to valid choices (DAILY, WEEKLY, MONTHLY, QUARTERLY only)
  const frequencyMap = {
    'DAILY': 'DAILY',
    'WEEKLY': 'WEEKLY',
    'MONTHLY': 'MONTHLY',
    'QUARTERLY': 'QUARTERLY',
    'YEARLY': 'QUARTERLY',  // Backend doesn't support YEARLY, map to QUARTERLY
    'ANNUAL': 'QUARTERLY',   // Map to QUARTERLY as closest valid option
    'ANNUALLY': 'QUARTERLY', // Map to QUARTERLY as closest valid option
    'BIWEEKLY': 'WEEKLY',
    'BI-WEEKLY': 'WEEKLY',
    'BIMONTHLY': 'MONTHLY',
    'BI-MONTHLY': 'MONTHLY'
  }
  
  return frequencyMap[normalized] || 'MONTHLY'
}

// API functions
async function saveSLA(slaData) {
  try {
    console.log('Sending SLA data to backend:', slaData)
    
    // Wrap API call with permission check
    const result = await withPermissionCheck(
      () => apiService.createSLA(slaData)
    )
    
    // Log the CREATE action
    await loggingService.logSLACreate(
      result.sla_id || result.id,
      slaData.sla_name,
      {
        sla_type: slaData.sla_type,
        effective_date: slaData.effective_date,
        expiry_date: slaData.expiry_date,
        vendor_id: slaData.vendor_id
      }
    )
    
    return result
  } catch (error) {
    console.error('Error saving SLA:', error)
    throw error
  }
}


// Legacy notification function - now uses the new notification system
async function createSLANotification(title, message, type = 'info') {
  try {
    if (type === 'success') {
      await showSLASuccess('created', {
        sla_name: formData.sla_name
      })
    } else if (type === 'error') {
      await showSLAError('create_failed', message, {
        sla_name: formData.sla_name
      })
    } else {
      await showInfo(title, message, {
        sla_name: formData.sla_name,
        action: 'sla_created'
      })
    }
  } catch (error) {
    console.error('Error creating notification:', error)
  }
}

</script>
