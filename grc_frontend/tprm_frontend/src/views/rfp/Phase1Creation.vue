<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
    <div class="w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <!-- Header -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex flex-col gap-4">
          <!-- Top Bar with Actions -->
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div class="flex items-center gap-3">
              <div class="h-10 w-10 rounded-lg bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
                <Icons name="file-text" class="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-gray-900">RFP Creation & Setup</h1>
                <div v-if="lastSaved" class="flex items-center gap-1 text-xs sm:text-sm text-gray-500 mt-1">
                  <Icons v-if="isAutoSaving" name="clock" class="h-3 w-3 animate-spin" />
                  <Icons v-else name="check-circle" class="h-3 w-3 text-green-500" />
                  <span v-if="isAutoSaving">Saving...</span>
                  <span v-else>Saved {{ formatTime(lastSaved) }}</span>
                </div>
              </div>
            </div>
        
            <!-- Action Buttons -->
            <div class="flex flex-wrap items-center gap-2">
              <!-- Start Fresh -->
              <button 
                v-if="hasExistingDraft" 
                @click="clearDraftAndStartFresh" 
                class="inline-flex items-center justify-center px-4 h-10 rounded-lg border border-orange-200 bg-orange-50 text-orange-700 hover:bg-orange-100 hover:border-orange-300 transition-all text-sm font-medium shadow-sm"
                title="Clear current draft and start fresh"
              >
                <Icons name="refresh-cw" class="h-4 w-4 mr-1.5" />
                <span>Reset</span>
              </button>
              
              <!-- Load Sample Data -->
              <button
                @click="loadSampleData"
                :disabled="isSubmitting || isGeneratingDocument || isUploadingDocuments"
                class="inline-flex items-center justify-center px-4 h-10 rounded-lg border border-indigo-200 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 hover:border-indigo-300 transition-all text-sm font-medium shadow-sm"
                title="Load realistic sample data into the form"
              >
                <Icons name="wand-2" class="h-4 w-4 mr-1.5" />
                <span>Load Sample</span>
              </button>
              
              <!-- Save Draft -->
              <button 
                @click="handleSaveDraft" 
                :disabled="isSubmitting"
                class="inline-flex items-center justify-center px-4 h-10 rounded-lg border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium shadow-sm"
                title="Save draft to server"
              >
                <Icons v-if="isSubmitting && !isFormValid" name="loader" class="h-4 w-4 mr-1.5 animate-spin" />
                <Icons v-else name="save" class="h-4 w-4 mr-1.5" />
                <span>Save Draft</span>
              </button>
              
              <!-- Download PDF -->
              <button 
                @click="generateDocument('pdf')" 
                :disabled="isGeneratingDocument || !formData.rfpNumber || !formData.title || !formData.description || !formData.type"
                class="inline-flex items-center justify-center h-10 w-10 rounded-lg border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                title="Download PDF"
              >
                <svg v-if="isGeneratingDocument" class="h-4 w-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </button>
              
              <!-- Preview -->
              <button 
                @click="previewDocument" 
                :disabled="isGeneratingDocument || !formData.rfpNumber || !formData.title || !formData.description || !formData.type"
                class="inline-flex items-center justify-center h-10 w-10 rounded-lg border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                title="Preview Document"
              >
                <svg class="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>

              <!-- Vendor Portal Preview -->
              <button
                @click="openVendorPortalPreview"
                :disabled="!canPreviewVendorPortal"
                class="inline-flex items-center justify-center px-4 h-10 rounded-lg border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium shadow-sm"
                title="Preview how vendors will experience this RFP"
              >
                <Icons name="eye" class="h-4 w-4 mr-1.5" />
                <span>Vendor Preview</span>
              </button>
              
              <div class="h-6 w-px bg-gray-300"></div>
              
              <!-- Proceed to Approval -->
              <button 
                @click="handleProceedToApprovalWorkflow" 
                :disabled="isSubmitting || isUploadingDocuments || !isFormValid"
                class="inline-flex items-center px-5 h-10 rounded-lg bg-blue-600 text-white hover:bg-blue-700 hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold shadow-md"
                :title="formData.autoApprove ? 'Submit RFP (will be auto-approved)' : 'Proceed to Approval Workflow'"
              >
                <Icons v-if="(isSubmitting || isUploadingDocuments) && isFormValid" name="loader" class="h-4 w-4 mr-2 animate-spin" />
                <Icons v-else name="arrow-right" class="h-4 w-4 mr-2" />
                <span v-if="isUploadingDocuments">Uploading...</span>
                <span v-else-if="isSubmitting">Processing...</span>
                <span v-else>{{ formData.autoApprove ? 'Submit & Auto-Approve' : 'Proceed to Approval' }}</span>
              </button>
            </div>
          </div>
          
          <p class="text-gray-600 text-sm mt-2">
            Create a comprehensive RFP with evaluation criteria, budget, and reviewer assignments.
          </p>
        </div>
      </div>


      <!-- Full-width form container -->
      <div class="space-y-6">
        <!-- Professional Tabs Navigation -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div class="border-b border-gray-200 bg-gray-50/50">
            <nav class="flex overflow-x-auto" aria-label="Tabs" style="scrollbar-width: none; -ms-overflow-style: none;">
              <div 
                class="flex w-full px-2 tab-container"
                :style="{ '--tab-count': visibleTabs.length }"
              >
                <button
                  v-for="(tab, index) in visibleTabs"
                  :key="tab.value"
                  type="button"
                  @click="activeTab = tab.value"
                  :class="[
                    'group relative flex items-center gap-2 px-2 sm:px-3 py-2.5 sm:py-3 text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 tab-button',
                    activeTab === tab.value
                      ? 'text-blue-700 border-b-2 border-blue-600 bg-white shadow-sm'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-white/50 border-b-2 border-transparent'
                  ]"
                  role="tab"
                  :aria-selected="activeTab === tab.value"
                >
                  <span
                    class="flex items-center justify-center h-6 w-6 sm:h-7 sm:w-7 rounded-full text-xs font-bold transition-all duration-200 shrink-0 tab-number"
                    :class="activeTab === tab.value
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-white border-2 border-gray-300 text-gray-600 group-hover:border-gray-400'"
                  >
                    {{ getTabDisplayIndex(tab.value) }}
                  </span>
                  <span class="flex flex-col items-start min-w-0 flex-1 overflow-hidden tab-text">
                    <span class="font-semibold leading-tight truncate w-full text-xs sm:text-sm tab-label">{{ tab.label }}</span>
                    <span class="text-[10px] sm:text-xs font-normal text-gray-500 leading-tight truncate w-full tab-description">
                      {{ tab.description }}
                    </span>
                  </span>
                  <button
                    v-if="tab.canHide"
                    @click.stop="hideTab(tab.value)"
                    type="button"
                    class="ml-1 p-0.5 sm:p-1 rounded-md hover:bg-red-50 text-gray-400 hover:text-red-600 transition-colors shrink-0 flex-shrink-0 tab-close"
                    title="Remove this section"
                  >
                    <Icons name="x" class="h-3 w-3 sm:h-3.5 sm:w-3.5" />
                  </button>
                </button>
              </div>
            </nav>
          </div>
          
          <!-- Hidden Tabs Section -->
          <div v-if="hiddenTabs.size > 0" class="border-t border-gray-200 bg-gray-50 px-4 py-3">
            <button
              @click="showHiddenTabs = !showHiddenTabs"
              class="flex items-center justify-between w-full text-sm text-gray-600 hover:text-gray-900 transition-colors"
            >
              <div class="flex items-center gap-2">
                <Icons name="eye-off" class="h-4 w-4" />
                <span class="font-medium">{{ hiddenTabs.size }} section{{ hiddenTabs.size > 1 ? 's' : '' }} hidden</span>
                <span class="text-xs text-gray-500">(Click to {{ showHiddenTabs ? 'hide' : 'view' }})</span>
              </div>
              <Icons 
                :name="showHiddenTabs ? 'chevron-up' : 'chevron-down'" 
                class="h-4 w-4 transition-transform"
              />
            </button>
            
            <div v-if="showHiddenTabs" class="mt-3 space-y-2">
              <div
                v-for="tab in hiddenTabsList"
                :key="tab.value"
                class="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
              >
                <div class="flex items-center gap-3">
                  <span class="flex items-center justify-center h-7 w-7 rounded-full bg-gray-100 text-gray-600 text-xs font-semibold">
                    {{ getTabDisplayIndex(tab.value) }}
                  </span>
                  <div>
                    <span class="font-medium text-gray-900">{{ tab.label }}</span>
                    <p class="text-xs text-gray-500">{{ tab.description }}</p>
                  </div>
                </div>
                <button
                  @click="restoreTab(tab.value)"
                  type="button"
                  class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 transition-colors"
                  title="Restore this section"
                >
                  <Icons name="rotate-ccw" class="h-3.5 w-3.5" />
                  Restore
                </button>
              </div>
            </div>
          </div>
        </div>
        <!-- Basic Information -->
        <Card
          v-show="activeTab === 'basic' && !hiddenTabs.has('basic')"
          class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
        >
          <CardHeader class="bg-gradient-to-r from-gray-50 to-white border-b border-gray-100 rounded-t-xl">
            <div class="flex items-center gap-3">
              <div class="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-sm">
                <Icons name="file-text" class="h-5 w-5 text-white" />
              </div>
              <div>
                <CardTitle class="text-lg font-semibold text-gray-900">Basic Information</CardTitle>
                <CardDescription class="text-sm text-gray-600 mt-0.5">
                  Define the core details of your RFP
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent class="p-6 space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <Label html-for="rfpNumber" class="flex items-center gap-2">
                  <span>RFP Number *</span>
                  <div class="rfp-data-type-circle-toggle-wrapper">
                    <div class="rfp-data-type-circle-toggle">
                      <div 
                        class="rfp-circle-option rfp-personal-circle" 
                        :class="{ active: getRFPDataType('rfpNumber') === 'personal' }"
                        @click="setRFPDataType('rfpNumber', 'personal')"
                        title="Personal Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-confidential-circle" 
                        :class="{ active: getRFPDataType('rfpNumber') === 'confidential' }"
                        @click="setRFPDataType('rfpNumber', 'confidential')"
                        title="Confidential Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-regular-circle" 
                        :class="{ active: getRFPDataType('rfpNumber') === 'regular' }"
                        @click="setRFPDataType('rfpNumber', 'regular')"
                        title="Regular Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </Label>
                <Input
                  id="rfpNumber"
                  placeholder="e.g., RFP-2024-001"
                  v-model="formData.rfpNumber"
                />
              </div>
              <div class="space-y-2">
                <Label html-for="title" class="flex items-center gap-2">
                  <span>RFP Title *</span>
                  <div class="rfp-data-type-circle-toggle-wrapper">
                    <div class="rfp-data-type-circle-toggle">
                      <div 
                        class="rfp-circle-option rfp-personal-circle" 
                        :class="{ active: getRFPDataType('title') === 'personal' }"
                        @click="setRFPDataType('title', 'personal')"
                        title="Personal Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-confidential-circle" 
                        :class="{ active: getRFPDataType('title') === 'confidential' }"
                        @click="setRFPDataType('title', 'confidential')"
                        title="Confidential Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-regular-circle" 
                        :class="{ active: getRFPDataType('title') === 'regular' }"
                        @click="setRFPDataType('title', 'regular')"
                        title="Regular Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </Label>
                <Input
                  id="title"
                  placeholder="e.g., Cloud Infrastructure Services"
                  v-model="formData.title"
                />
              </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <Label html-for="type" class="flex items-center gap-2">
                  <span>RFP Type *</span>
                  <div class="rfp-data-type-circle-toggle-wrapper">
                    <div class="rfp-data-type-circle-toggle">
                      <div 
                        class="rfp-circle-option rfp-personal-circle" 
                        :class="{ active: getRFPDataType('type') === 'personal' }"
                        @click="setRFPDataType('type', 'personal')"
                        title="Personal Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-confidential-circle" 
                        :class="{ active: getRFPDataType('type') === 'confidential' }"
                        @click="setRFPDataType('type', 'confidential')"
                        title="Confidential Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-regular-circle" 
                        :class="{ active: getRFPDataType('type') === 'regular' }"
                        @click="setRFPDataType('type', 'regular')"
                        title="Regular Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </Label>
                <Select v-model="formData.type" :disabled="loadingRfpTypes">
                  <option value="" disabled>Select type</option>
                  <option v-for="rfpType in rfpTypes" :key="rfpType" :value="rfpType">
                    {{ rfpType }}
                  </option>
                </Select>
                <p v-if="loadingRfpTypes" class="text-xs text-muted-foreground">Loading RFP types...</p>
              </div>
              <div v-if="!hiddenFields.category" class="space-y-2">
                <div class="flex items-center justify-between">
                  <Label html-for="category" class="flex items-center gap-2">
                    <span>Category</span>
                    <div class="rfp-data-type-circle-toggle-wrapper">
                      <div class="rfp-data-type-circle-toggle">
                        <div 
                          class="rfp-circle-option rfp-personal-circle" 
                          :class="{ active: getRFPDataType('category') === 'personal' }"
                          @click="setRFPDataType('category', 'personal')"
                          title="Personal Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-confidential-circle" 
                          :class="{ active: getRFPDataType('category') === 'confidential' }"
                          @click="setRFPDataType('category', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-regular-circle" 
                          :class="{ active: getRFPDataType('category') === 'regular' }"
                          @click="setRFPDataType('category', 'regular')"
                          title="Regular Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </Label>
                  <button
                    @click="hideField('category')"
                    type="button"
                    class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                    title="Remove this field from form"
                  >
                    <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                  </button>
                </div>
                <Select v-model="formData.category">
                  <option value="" disabled>Select category</option>
                  <option value="cloud">Cloud Services</option>
                  <option value="security">Security</option>
                  <option value="data">Data & Analytics</option>
                  <option value="hr">Human Resources</option>
                  <option value="marketing">Marketing</option>
                  <option value="finance">Finance</option>
                </Select>
              </div>
        </div>

            <div class="space-y-2">
              <Label html-for="description" class="flex items-center gap-2">
                <span>Description *</span>
                <div class="rfp-data-type-circle-toggle-wrapper">
                  <div class="rfp-data-type-circle-toggle">
                    <div 
                      class="rfp-circle-option rfp-personal-circle" 
                      :class="{ active: getRFPDataType('description') === 'personal' }"
                      @click="setRFPDataType('description', 'personal')"
                      title="Personal Data"
                    >
                      <div class="rfp-circle-inner"></div>
                    </div>
                    <div 
                      class="rfp-circle-option rfp-confidential-circle" 
                      :class="{ active: getRFPDataType('description') === 'confidential' }"
                      @click="setRFPDataType('description', 'confidential')"
                      title="Confidential Data"
                    >
                      <div class="rfp-circle-inner"></div>
                    </div>
                    <div 
                      class="rfp-circle-option rfp-regular-circle" 
                      :class="{ active: getRFPDataType('description') === 'regular' }"
                      @click="setRFPDataType('description', 'regular')"
                      title="Regular Data"
                    >
                      <div class="rfp-circle-inner"></div>
                    </div>
                  </div>
                </div>
              </Label>
              <Textarea
                id="description"
                placeholder="Provide a detailed description of your requirements..."
                :rows="4"
                v-model="formData.description"
          />
        </div>

            <!-- Dynamic Custom Fields Section -->
            <div v-if="customFieldsSchema && customFieldsSchema.length > 0" class="space-y-4 border-t pt-4 mt-4">
              <div class="flex items-center gap-2">
                <Icons name="settings" class="h-5 w-5 text-primary" />
                <h3 class="text-lg font-semibold">Additional Fields</h3>
              </div>
              <p class="text-sm text-muted-foreground">Fields specific to this RFP type</p>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div 
                  v-for="(field, fieldIndex) in customFieldsSchema.filter(f => !hiddenCustomFields.has(f.name))" 
                  :key="`custom-field-${field.name}-${fieldIndex}`"
                  class="space-y-2"
                >
                  <div class="flex items-center justify-between">
                    <Label :html-for="`custom_${field.name}_${fieldIndex}`">
                      {{ field.label || field.name }}
                      <span v-if="field.required" class="text-red-500">*</span>
                    </Label>
                    <button
                      v-if="!field.required"
                      @click="hideCustomField(field.name)"
                      type="button"
                      class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                      title="Remove this field from form"
                    >
                      <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                    </button>
                  </div>
                  
                  <!-- Text Input -->
                  <Input
                    v-if="field.type === 'text' || field.type === 'email' || field.type === 'number' || !field.type"
                    :id="`custom_${field.name}_${fieldIndex}`"
                    :type="field.type || 'text'"
                    :placeholder="field.placeholder || `Enter ${field.label || field.name}`"
                    :model-value="formData.customFields[field.name]"
                    @update:model-value="(value) => { formData.customFields[field.name] = value }"
                    :required="field.required"
                  />
                  
                  <!-- Textarea -->
                  <Textarea
                    v-else-if="field.type === 'textarea'"
                    :id="`custom_${field.name}_${fieldIndex}`"
                    :placeholder="field.placeholder || `Enter ${field.label || field.name}`"
                    :rows="field.rows || 3"
                    :model-value="formData.customFields[field.name]"
                    @update:model-value="(value) => { formData.customFields[field.name] = value }"
                    :required="field.required"
                  />
                  
                  <!-- Select Dropdown -->
                  <Select
                    v-else-if="field.type === 'select'"
                    :id="`custom_${field.name}_${fieldIndex}`"
                    :model-value="formData.customFields[field.name]"
                    @update:model-value="(value) => { formData.customFields[field.name] = value }"
                    :required="field.required"
                  >
                    <option value="" disabled>Select {{ field.label || field.name }}</option>
                    <option 
                      v-for="option in field.options" 
                      :key="option.value || option"
                      :value="option.value || option"
                    >
                      {{ option.label || option }}
                    </option>
                  </Select>
                  
                  <!-- Date Input -->
                  <Input
                    v-else-if="field.type === 'date'"
                    :id="`custom_${field.name}_${fieldIndex}`"
                    type="date"
                    :model-value="formData.customFields[field.name]"
                    @update:model-value="(value) => { formData.customFields[field.name] = value }"
                    :required="field.required"
                  />
                  
                  <!-- DateTime Input -->
                  <input
                    v-else-if="field.type === 'datetime' || field.type === 'datetime-local'"
                    :id="`custom_${field.name}_${fieldIndex}`"
                    type="datetime-local"
                    :value="formData.customFields[field.name]"
                    @input="(e) => { formData.customFields[field.name] = (e.target as HTMLInputElement).value }"
                    :required="field.required"
                    class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  />
                  
                  <!-- Checkbox -->
                  <div v-else-if="field.type === 'checkbox'" class="flex items-center space-x-2">
                    <Checkbox
                      :id="`custom_${field.name}_${fieldIndex}`"
                      :model-value="formData.customFields[field.name]"
                      @update:model-value="(value) => { formData.customFields[field.name] = value }"
                    />
                    <Label :html-for="`custom_${field.name}_${fieldIndex}`" class="text-sm">
                      {{ field.label || field.name }}
                    </Label>
                  </div>
                  
                  <!-- Fallback for unknown field types -->
                  <Input
                    v-else
                    :id="`custom_${field.name}_${fieldIndex}`"
                    type="text"
                    :placeholder="field.placeholder || `Enter ${field.label || field.name}`"
                    :model-value="formData.customFields[field.name]"
                    @update:model-value="(value) => { formData.customFields[field.name] = value }"
                    :required="field.required"
                  />
                  
                  <p v-if="field.help_text" class="text-xs text-muted-foreground">
                    {{ field.help_text }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Categorized Custom Fields Section -->
            <div class="space-y-4 border-t pt-4 mt-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <Icons name="settings" class="h-5 w-5 text-primary" />
                  <h3 class="text-lg font-semibold">Categorized Custom Fields</h3>
                </div>
                <p class="text-sm text-muted-foreground">Add custom fields organized by categories</p>
              </div>
              
              <!-- Category Tabs -->
              <div class="flex gap-2 border-b border-gray-200 overflow-x-auto">
                <button
                  v-for="category in customFieldCategories"
                  :key="category.id"
                  @click="activeCustomFieldCategory = category.id"
                  :class="[
                    'px-4 py-2 text-sm font-medium transition-colors border-b-2',
                    activeCustomFieldCategory === category.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-900'
                  ]"
                >
                  {{ category.label }}
                  <span v-if="categoryCustomFields[category.id]?.length > 0" class="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                    {{ categoryCustomFields[category.id].length }}
                  </span>
                </button>
              </div>

              <!-- Category Content -->
              <div v-for="category in customFieldCategories" :key="category.id" v-show="activeCustomFieldCategory === category.id" class="space-y-4">
                <!-- Add New Field Form -->
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-4">
                  <div class="flex items-center justify-between">
                    <div>
                      <h4 class="text-sm font-semibold text-blue-900">Add Custom Field to {{ category.label }}</h4>
                      <p class="text-xs text-blue-800">Fields will be saved as key:value pairs under this category</p>
                    </div>
                  </div>
                  
                  <div class="bg-white border border-blue-300 rounded-lg p-4 space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                      <div class="md:col-span-3 space-y-1">
                        <Label class="text-xs font-medium text-blue-900">Field Label *</Label>
                        <Input
                          v-model="newCustomField.label"
                          type="text"
                          placeholder="e.g., Additional Info"
                          @focus="newCustomField.category = category.id"
                        />
                      </div>
                      <div class="md:col-span-2 space-y-1">
                        <Label class="text-xs font-medium text-blue-900">Data Type *</Label>
                        <Select
                          v-model="newCustomField.type"
                          @update:model-value="newCustomField.value = newCustomField.type === 'file' ? null : ''; newCustomField.category = category.id"
                        >
                          <option v-for="type in customFieldTypes" :key="type.value" :value="type.value">
                            {{ type.label }}
                          </option>
                        </Select>
                      </div>
                      <div class="md:col-span-6 space-y-1">
                        <Label class="text-xs font-medium text-blue-900">Value *</Label>
                        <Input
                          v-if="newCustomField.type === 'text' || newCustomField.type === 'email' || newCustomField.type === 'url'"
                          v-model="newCustomField.value"
                          :type="newCustomField.type"
                          placeholder="Enter value"
                          @focus="newCustomField.category = category.id"
                        />
                        <Textarea
                          v-else-if="newCustomField.type === 'textarea'"
                          v-model="newCustomField.value"
                          :rows="2"
                          placeholder="Enter value"
                          @focus="newCustomField.category = category.id"
                        />
                        <Input
                          v-else-if="newCustomField.type === 'number' || newCustomField.type === 'decimal'"
                          v-model.number="newCustomField.value"
                          type="number"
                          :step="newCustomField.type === 'decimal' ? '0.01' : '1'"
                          placeholder="Enter number"
                          @focus="newCustomField.category = category.id"
                        />
                        <Input
                          v-else-if="newCustomField.type === 'date'"
                          v-model="newCustomField.value"
                          type="date"
                          @focus="newCustomField.category = category.id"
                        />
                        <input
                          v-else-if="newCustomField.type === 'datetime' || newCustomField.type === 'datetime-local'"
                          v-model="newCustomField.value"
                          type="datetime-local"
                          @focus="newCustomField.category = category.id"
                          class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        />
                        <div v-else-if="newCustomField.type === 'file'" class="space-y-2">
                          <input
                            type="file"
                            @change="(e) => handleCustomFieldFileChange(e, category.id)"
                            class="block w-full text-sm text-gray-900 border border-input rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring"
                          />
                          <div v-if="newCustomField.fileData" class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded p-2">
                            <span class="text-xs text-gray-700">{{ newCustomField.fileData.fileName }}</span>
                            <button type="button" @click="newCustomField.fileData = null; newCustomField.value = null" class="text-xs text-red-600 hover:text-red-800">Remove</button>
                          </div>
                        </div>
                        <Input
                          v-else
                          v-model="newCustomField.value"
                          type="text"
                          placeholder="Enter value"
                          @focus="newCustomField.category = category.id"
                        />
                      </div>
                      <div class="md:col-span-1">
                        <Button
                          @click="addCustomFieldToCategory(category.id)"
                          variant="default"
                          size="sm"
                          class="w-full"
                        >
                          <Icons name="plus" class="h-4 w-4 mr-1" />
                          Add
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Existing Fields List -->
                <div v-if="categoryCustomFields[category.id]?.length > 0" class="space-y-2">
                  <p class="text-xs font-semibold text-gray-700">Custom fields added (drag to reorder):</p>
                  <div class="space-y-2">
                    <div
                      v-for="(field, fieldIndex) in categoryCustomFields[category.id]"
                      :key="field.id"
                      :draggable="true"
                      @dragstart="handleCustomFieldDragStart(fieldIndex, category.id, $event)"
                      @dragover="handleCustomFieldDragOver(fieldIndex, category.id, $event)"
                      @dragleave="handleCustomFieldDragLeave(fieldIndex, category.id, $event)"
                      @drop="handleCustomFieldDrop(fieldIndex, category.id, $event)"
                      class="bg-white border border-gray-200 rounded-lg p-3 transition-colors"
                      :class="[
                        draggedCustomFieldIndex === fieldIndex && draggedCustomFieldCategory === category.id ? 'opacity-50' : '',
                        dragOverCustomFieldIndex === fieldIndex && dragOverCustomFieldCategory === category.id ? 'border-blue-500 bg-blue-50' : ''
                      ]"
                    >
                      <div class="flex items-start justify-between gap-3">
                        <div class="flex items-center gap-3 flex-1">
                          <!-- Drag Handle -->
                          <div class="cursor-grab active:cursor-grabbing" title="Drag to reorder">
                            <Icons name="grip" class="h-5 w-5 text-gray-400" />
                          </div>
                          
                          <div class="flex-1">
                            <div class="flex items-center gap-2 mb-1">
                              <p class="text-sm font-semibold text-gray-900">{{ field.label }}</p>
                              <span class="text-xs text-gray-500">({{ getCustomFieldTypeLabel(field.type) }})</span>
                              <span class="text-xs text-blue-600 font-mono">Key: {{ field.name }}</span>
                            </div>
                            <div class="mt-2">
                              <p v-if="field.type !== 'file'" class="text-sm text-gray-700">
                                <span class="font-medium">Value:</span>
                                <span class="ml-1">{{ getCustomFieldValue(field, category.id) || '(empty)' }}</span>
                              </p>
                              <div v-else-if="getCustomFieldValue(field, category.id)" class="flex items-center gap-2">
                                <span class="text-sm text-gray-700 font-medium">File:</span>
                                <span class="text-sm text-gray-600">{{ getCustomFieldValue(field, category.id)?.fileName || 'File uploaded' }}</span>
                                <button type="button" @click="downloadCustomFieldFile(field, category.id)" class="text-xs text-blue-600 hover:text-blue-800">Download</button>
                              </div>
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          @click="removeCustomFieldFromCategory(field.id, category.id)"
                          class="text-red-600 hover:text-red-700"
                        >
                          <Icons name="trash2" class="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <Label html-for="issueDate" class="flex items-center gap-2">
                  <span>Issue Date *</span>
                  <div class="rfp-data-type-circle-toggle-wrapper">
                    <div class="rfp-data-type-circle-toggle">
                      <div 
                        class="rfp-circle-option rfp-personal-circle" 
                        :class="{ active: getRFPDataType('issueDate') === 'personal' }"
                        @click="setRFPDataType('issueDate', 'personal')"
                        title="Personal Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-confidential-circle" 
                        :class="{ active: getRFPDataType('issueDate') === 'confidential' }"
                        @click="setRFPDataType('issueDate', 'confidential')"
                        title="Confidential Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-regular-circle" 
                        :class="{ active: getRFPDataType('issueDate') === 'regular' }"
                        @click="setRFPDataType('issueDate', 'regular')"
                        title="Regular Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </Label>
                <Input
                  id="issueDate"
                  type="date"
                  v-model="formData.issueDate"
                />
              </div>
              <div class="space-y-2">
                <Label html-for="deadline" class="flex items-center gap-2">
                  <span>Submission Deadline *</span>
                  <div class="rfp-data-type-circle-toggle-wrapper">
                    <div class="rfp-data-type-circle-toggle">
                      <div 
                        class="rfp-circle-option rfp-personal-circle" 
                        :class="{ active: getRFPDataType('deadline') === 'personal' }"
                        @click="setRFPDataType('deadline', 'personal')"
                        title="Personal Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-confidential-circle" 
                        :class="{ active: getRFPDataType('deadline') === 'confidential' }"
                        @click="setRFPDataType('deadline', 'confidential')"
                        title="Confidential Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-regular-circle" 
                        :class="{ active: getRFPDataType('deadline') === 'regular' }"
                        @click="setRFPDataType('deadline', 'regular')"
                        title="Regular Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </Label>
                <input
                  id="deadline"
                  type="datetime-local"
                  v-model="formData.deadline"
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Document Upload Section -->
        <Card
          v-show="activeTab === 'documents' && !hiddenTabs.has('documents')"
          class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
        >
          <CardHeader>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <Icons name="upload" class="h-5 w-5 text-primary" />
                <CardTitle>Document Upload</CardTitle>
              </div>
              <Button 
                v-if="uploadedDocuments.length > 0"
                @click="saveAllDocuments" 
                variant="default" 
                size="sm"
                :disabled="isUploadingDocuments || isMergingDocuments"
              >
                <Icons v-if="isMergingDocuments" name="loader" class="h-4 w-4 mr-2 animate-spin" />
                <Icons v-else-if="isUploadingDocuments" name="loader" class="h-4 w-4 mr-2 animate-spin" />
                <Icons v-else name="save" class="h-4 w-4 mr-2" />
                <span v-if="isMergingDocuments">Merging...</span>
                <span v-else-if="isUploadingDocuments">Saving All...</span>
                <span v-else-if="uploadedDocuments.length >= 2 && !uploadedDocuments.some(d => d.uploaded)">Merge Documents</span>
                <span v-else-if="uploadedDocuments.some(d => !d.uploaded)">Save All</span>
                <span v-else>Save & Merge All</span>
              </Button>
            </div>
            <CardDescription>
              Upload supporting documents for your RFP
            </CardDescription>
          </CardHeader>
          <CardContent class="p-6 space-y-6">
            <!-- Document Upload Form -->
            <div class="space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <Label html-for="documentName">Document Name *</Label>
                  <Input
                    id="documentName"
                    placeholder="e.g., Technical Specifications"
                    v-model="newDocument.name"
                  />
                </div>
                <div class="space-y-2">
                  <Label html-for="documentFile">Select File *</Label>
                  <input
                    id="documentFile"
                    type="file"
                    @change="handleFileSelect"
                    accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png"
                    class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </div>
              </div>
              
               <div class="flex gap-2">
                 <Button 
                   @click="addDocument" 
                   variant="outline" 
                   size="sm"
                   :disabled="!newDocument.name || !newDocument.file"
                 >
                   <Icons name="plus" class="h-4 w-4 mr-2" />
                   Add Document
                 </Button>
                 <Button 
                   @click="clearDocumentForm" 
                   variant="ghost" 
                   size="sm"
                 >
                   <Icons name="x" class="h-4 w-4 mr-2" />
                   Clear
                 </Button>
               </div>
            </div>

            <!-- Uploaded Documents List -->
            <div v-if="uploadedDocuments.length > 0" class="space-y-3">
              <div class="flex items-center gap-4">
                <h4 class="text-sm font-semibold">Documents ({{ uploadedDocuments.length }})</h4>
                <div class="flex items-center gap-2 text-xs text-muted-foreground">
                  <div class="flex items-center gap-1">
                    <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>{{ uploadedDocuments.filter(d => d.uploaded).length }} Saved</span>
                  </div>
                  <div class="flex items-center gap-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full"></div>
                    <span>{{ uploadedDocuments.filter(d => !d.uploaded).length }} Pending</span>
                  </div>
                </div>
              </div>
              <div class="space-y-2">
                <div 
                  v-for="(doc, index) in uploadedDocuments" 
                  :key="`doc-${index}-${doc.s3Id || doc.name}`"
                  :draggable="uploadedDocuments.length > 1 && !isMergingDocuments"
                  @dragstart="handleDragStart(index, $event)"
                  @dragover="handleDragOver(index, $event)"
                  @dragleave="handleDragLeave(index, $event)"
                  @drop="handleDrop(index, $event)"
                  class="flex items-center justify-between p-3 border border-border rounded-lg transition-colors"
                  :class="[
                    doc.uploaded ? 'bg-green-50 border-green-200' : '',
                    draggedIndex === index ? 'opacity-50' : '',
                    dragOverIndex === index ? 'border-blue-500 bg-blue-50' : ''
                  ]"
                >
                   <div class="flex items-center gap-3 flex-1">
                     <!-- Drag Handle -->
                     <div 
                       v-if="uploadedDocuments.length > 1"
                       class="mr-2 cursor-grab active:cursor-grabbing"
                       :class="{ 'cursor-not-allowed': isMergingDocuments }"
                       title="Drag to reorder"
                     >
                       <Icons name="grip" class="h-5 w-5 text-gray-400" />
                     </div>
                     
                     <Icons 
                       :name="doc.uploaded ? 'check-circle' : 'file'" 
                       :class="doc.uploaded ? 'h-4 w-4 text-green-500' : 'h-4 w-4 text-gray-500'" 
                     />
                     <div class="flex-1">
                       <p class="text-sm font-medium">
                         {{ doc.name }} 
                         <span v-if="doc.isMerged" class="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">Merged</span>
                         <span v-if="uploadedDocuments.length > 1" class="text-xs text-gray-400">(#{{ index + 1 }})</span>
                       </p>
                       <p class="text-xs text-muted-foreground">{{ doc.fileName }} ({{ formatFileSize(doc.fileSize) }})</p>
                       <p v-if="doc.uploaded" class="text-xs text-green-600">✅ Uploaded (ID: {{ doc.s3Id }})</p>
                     </div>
                   </div>
                   <div class="flex items-center gap-2">
                     <Button
                       v-if="doc.uploaded"
                       variant="outline"
                       size="sm"
                       @click="downloadDocument(doc)"
                       title="Download this document"
                     >
                       <Icons name="download" class="h-4 w-4 mr-2" />
                       Download
                     </Button>
                     <Button
                       v-else
                       variant="outline"
                       size="sm"
                       @click="saveSingleDocument(index)"
                       :disabled="perDocUploading[index]"
                     >
                       <Icons v-if="perDocUploading[index]" name="loader" class="h-4 w-4 mr-2 animate-spin" />
                       <Icons v-else name="save" class="h-4 w-4 mr-2" />
                       <span v-if="perDocUploading[index]">Saving...</span>
                       <span v-else>Save</span>
                     </Button>
                     <Button
                       variant="ghost"
                       size="sm"
                       @click="removeDocument(index)"
                       :disabled="doc.uploaded || perDocUploading[index] || isMergingDocuments"
                       :class="doc.uploaded ? 'text-red-600 hover:text-red-700' : ''"
                       :title="doc.uploaded ? 'Delete uploaded document' : 'Remove from queue'"
                     >
                       <Icons name="trash2" class="h-4 w-4" />
                     </Button>
                   </div>
                </div>
              </div>
              
            </div>
          </CardContent>
        </Card>

        <!-- Budget & Timeline -->
        <Card
          v-show="activeTab === 'budget' && !hiddenTabs.has('budget')"
          class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
        >
          <CardHeader>
            <div class="flex items-center gap-2">
              <Icons name="dollar-sign" class="h-5 w-5 text-primary" />
              <CardTitle>Budget & Timeline</CardTitle>
            </div>
            <CardDescription>
              Set budget parameters and project timeline
            </CardDescription>
          </CardHeader>
          <CardContent class="p-6 space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div v-if="!hiddenFields.estimatedValue" class="space-y-2">
                <div class="flex items-center justify-between">
                  <Label html-for="estimatedValue" class="flex items-center gap-2">
                    <span>Estimated Value</span>
                    <div class="rfp-data-type-circle-toggle-wrapper">
                      <div class="rfp-data-type-circle-toggle">
                        <div 
                          class="rfp-circle-option rfp-personal-circle" 
                          :class="{ active: getRFPDataType('estimatedValue') === 'personal' }"
                          @click="setRFPDataType('estimatedValue', 'personal')"
                          title="Personal Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-confidential-circle" 
                          :class="{ active: getRFPDataType('estimatedValue') === 'confidential' }"
                          @click="setRFPDataType('estimatedValue', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-regular-circle" 
                          :class="{ active: getRFPDataType('estimatedValue') === 'regular' }"
                          @click="setRFPDataType('estimatedValue', 'regular')"
                          title="Regular Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </Label>
                  <button
                    @click="hideField('estimatedValue')"
                    type="button"
                    class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                    title="Remove this field from form"
                  >
                    <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                  </button>
                </div>
                <Input
                  id="estimatedValue"
                  type="number"
                  placeholder="250,000"
                  v-model="formData.estimatedValue"
                />
              </div>
              <div v-if="!hiddenFields.currency" class="space-y-2">
                <div class="flex items-center justify-between">
                  <Label html-for="currency" class="flex items-center gap-2">
                    <span>Currency</span>
                    <div class="rfp-data-type-circle-toggle-wrapper">
                      <div class="rfp-data-type-circle-toggle">
                        <div 
                          class="rfp-circle-option rfp-personal-circle" 
                          :class="{ active: getRFPDataType('currency') === 'personal' }"
                          @click="setRFPDataType('currency', 'personal')"
                          title="Personal Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-confidential-circle" 
                          :class="{ active: getRFPDataType('currency') === 'confidential' }"
                          @click="setRFPDataType('currency', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-regular-circle" 
                          :class="{ active: getRFPDataType('currency') === 'regular' }"
                          @click="setRFPDataType('currency', 'regular')"
                          title="Regular Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </Label>
                  <button
                    @click="hideField('currency')"
                    type="button"
                    class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                    title="Remove this field from form"
                  >
                    <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                  </button>
                </div>
                <Select v-model="formData.currency">
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                  <option value="INR">INR</option>
                  <option value="CAD">CAD</option>
                  <option value="AUD">AUD</option>
                </Select>
              </div>
              <div v-if="!hiddenFields.timeline" class="space-y-2">
                <div class="flex items-center justify-between">
                  <Label html-for="timeline" class="flex items-center gap-2">
                    <span>Project Timeline</span>
                    <div class="rfp-data-type-circle-toggle-wrapper">
                      <div class="rfp-data-type-circle-toggle">
                        <div 
                          class="rfp-circle-option rfp-personal-circle" 
                          :class="{ active: getRFPDataType('timeline') === 'personal' }"
                          @click="setRFPDataType('timeline', 'personal')"
                          title="Personal Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-confidential-circle" 
                          :class="{ active: getRFPDataType('timeline') === 'confidential' }"
                          @click="setRFPDataType('timeline', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-regular-circle" 
                          :class="{ active: getRFPDataType('timeline') === 'regular' }"
                          @click="setRFPDataType('timeline', 'regular')"
                          title="Regular Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </Label>
                  <button
                    @click="hideField('timeline')"
                    type="button"
                    class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                    title="Remove this field from form"
                  >
                    <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                  </button>
                </div>
                <Select v-model="formData.timeline">
                  <option value="" disabled>Select timeline</option>
                  <option value="3-months">3 Months</option>
                  <option value="6-months">6 Months</option>
                  <option value="12-months">12 Months</option>
                  <option value="18-months">18+ Months</option>
                </Select>
              </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div v-if="!hiddenFields.budgetMin" class="space-y-2">
                <div class="flex items-center justify-between">
                  <Label html-for="budgetMin" class="flex items-center gap-2">
                    <span>Minimum Budget</span>
                    <div class="rfp-data-type-circle-toggle-wrapper">
                      <div class="rfp-data-type-circle-toggle">
                        <div 
                          class="rfp-circle-option rfp-personal-circle" 
                          :class="{ active: getRFPDataType('budgetMin') === 'personal' }"
                          @click="setRFPDataType('budgetMin', 'personal')"
                          title="Personal Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-confidential-circle" 
                          :class="{ active: getRFPDataType('budgetMin') === 'confidential' }"
                          @click="setRFPDataType('budgetMin', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-regular-circle" 
                          :class="{ active: getRFPDataType('budgetMin') === 'regular' }"
                          @click="setRFPDataType('budgetMin', 'regular')"
                          title="Regular Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </Label>
                  <button
                    @click="hideField('budgetMin')"
                    type="button"
                    class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                    title="Remove this field from form"
                  >
                    <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                  </button>
                </div>
                <Input
                  id="budgetMin"
                  type="number"
                  placeholder="100,000"
                  v-model="formData.budgetMin"
                />
              </div>
              <div v-if="!hiddenFields.budgetMax" class="space-y-2">
                <div class="flex items-center justify-between">
                  <Label html-for="budgetMax" class="flex items-center gap-2">
                    <span>Maximum Budget</span>
                    <div class="rfp-data-type-circle-toggle-wrapper">
                      <div class="rfp-data-type-circle-toggle">
                        <div 
                          class="rfp-circle-option rfp-personal-circle" 
                          :class="{ active: getRFPDataType('budgetMax') === 'personal' }"
                          @click="setRFPDataType('budgetMax', 'personal')"
                          title="Personal Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-confidential-circle" 
                          :class="{ active: getRFPDataType('budgetMax') === 'confidential' }"
                          @click="setRFPDataType('budgetMax', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-regular-circle" 
                          :class="{ active: getRFPDataType('budgetMax') === 'regular' }"
                          @click="setRFPDataType('budgetMax', 'regular')"
                          title="Regular Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </Label>
                  <button
                    @click="hideField('budgetMax')"
                    type="button"
                    class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                    title="Remove this field from form"
                  >
                    <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                  </button>
                </div>
                <Input
                  id="budgetMax"
                  type="number"
                  placeholder="500,000"
                  v-model="formData.budgetMax"
                />
              </div>
            </div>
            
            <div v-if="!hiddenFields.evaluationPeriodEnd" class="space-y-2">
              <div class="flex items-center justify-between">
                <Label html-for="evaluationPeriodEnd" class="flex items-center gap-2">
                  <span>Evaluation Period End</span>
                  <div class="rfp-data-type-circle-toggle-wrapper">
                    <div class="rfp-data-type-circle-toggle">
                      <div 
                        class="rfp-circle-option rfp-personal-circle" 
                        :class="{ active: getRFPDataType('evaluationPeriodEnd') === 'personal' }"
                        @click="setRFPDataType('evaluationPeriodEnd', 'personal')"
                        title="Personal Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-confidential-circle" 
                        :class="{ active: getRFPDataType('evaluationPeriodEnd') === 'confidential' }"
                        @click="setRFPDataType('evaluationPeriodEnd', 'confidential')"
                        title="Confidential Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-regular-circle" 
                        :class="{ active: getRFPDataType('evaluationPeriodEnd') === 'regular' }"
                        @click="setRFPDataType('evaluationPeriodEnd', 'regular')"
                        title="Regular Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </Label>
                <button
                  @click="hideField('evaluationPeriodEnd')"
                  type="button"
                  class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                  title="Remove this field from form"
                >
                  <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                </button>
              </div>
              <Input
                id="evaluationPeriodEnd"
                type="date"
                v-model="formData.evaluationPeriodEnd"
              />
            </div>
          </CardContent>
        </Card>

        <!-- Evaluation Criteria -->
        <Card
          v-show="activeTab === 'criteria' && !hiddenTabs.has('criteria')"
          class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
        >
          <CardHeader>
            <div class="flex items-center gap-2">
              <Icons name="target" class="h-5 w-5 text-primary" />
              <CardTitle>Evaluation Criteria</CardTitle>
            </div>
            <CardDescription>
              Define how vendors will be evaluated (weights must total 100%)
            </CardDescription>
          </CardHeader>
          <CardContent class="p-6 space-y-6">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium">Total Weight:</span>
                <Badge :variant="totalWeight === 100 ? 'default' : totalWeight > 100 ? 'destructive' : 'secondary'">
                  {{ totalWeight }}%
                </Badge>
                <span v-if="totalWeight !== 100" class="text-xs text-muted-foreground">
                  {{ totalWeight > 100 ? `(${totalWeight - 100}% over)` : `(${100 - totalWeight}% remaining)` }}
                </span>
              </div>
              <div class="flex gap-2">
                <Button @click="addCriterion" size="sm" variant="outline">
                  <Icons name="plus" class="h-4 w-4 mr-2" />
                  Add Criterion
                </Button>
                <Button 
                  v-if="totalWeight !== 100 && totalWeight > 0" 
                  @click="normalizeWeights" 
                  size="sm" 
                  variant="secondary"
                >
                  <Icons name="target" class="h-4 w-4 mr-2" />
                  Normalize to 100%
                </Button>
              </div>
            </div>

            <div class="space-y-3">
              <div v-for="(criterion, index) in criteria" :key="criterion.id" class="p-4 border border-border rounded-lg space-y-3">
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium">Criterion {{ index + 1 }}</span>
                  <Button
                    v-if="criteria.length > 1"
                    variant="ghost"
                    size="sm"
                    @click="removeCriterion(criterion.id)"
                  >
                    <Icons name="trash2" class="h-4 w-4" />
                  </Button>
          </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div class="space-y-2">
                    <Label class="flex items-center gap-2">
                      <span>Name</span>
                      <div class="rfp-data-type-circle-toggle-wrapper">
                        <div class="rfp-data-type-circle-toggle">
                          <div 
                            class="rfp-circle-option rfp-personal-circle" 
                            :class="{ active: getCriteriaDataType(criterion.id, 'name') === 'personal' }"
                            @click="setCriteriaDataType(criterion.id, 'name', 'personal')"
                            title="Personal Data"
                          >
                            <div class="rfp-circle-inner"></div>
                          </div>
                          <div 
                            class="rfp-circle-option rfp-confidential-circle" 
                            :class="{ active: getCriteriaDataType(criterion.id, 'name') === 'confidential' }"
                            @click="setCriteriaDataType(criterion.id, 'name', 'confidential')"
                            title="Confidential Data"
                          >
                            <div class="rfp-circle-inner"></div>
                          </div>
                          <div 
                            class="rfp-circle-option rfp-regular-circle" 
                            :class="{ active: getCriteriaDataType(criterion.id, 'name') === 'regular' }"
                            @click="setCriteriaDataType(criterion.id, 'name', 'regular')"
                            title="Regular Data"
                          >
                            <div class="rfp-circle-inner"></div>
                          </div>
                        </div>
                      </div>
                    </Label>
                    <Input
                      placeholder="e.g., Technical Capability"
                      v-model="criterion.name"
                    />
                  </div>
                  <div class="space-y-2">
                    <Label class="flex items-center gap-2">
                      <span>Weight (%)</span>
                      <div class="rfp-data-type-circle-toggle-wrapper">
                        <div class="rfp-data-type-circle-toggle">
                          <div 
                            class="rfp-circle-option rfp-personal-circle" 
                            :class="{ active: getCriteriaDataType(criterion.id, 'weight') === 'personal' }"
                            @click="setCriteriaDataType(criterion.id, 'weight', 'personal')"
                            title="Personal Data"
                          >
                            <div class="rfp-circle-inner"></div>
                          </div>
                          <div 
                            class="rfp-circle-option rfp-confidential-circle" 
                            :class="{ active: getCriteriaDataType(criterion.id, 'weight') === 'confidential' }"
                            @click="setCriteriaDataType(criterion.id, 'weight', 'confidential')"
                            title="Confidential Data"
                          >
                            <div class="rfp-circle-inner"></div>
                          </div>
                          <div 
                            class="rfp-circle-option rfp-regular-circle" 
                            :class="{ active: getCriteriaDataType(criterion.id, 'weight') === 'regular' }"
                            @click="setCriteriaDataType(criterion.id, 'weight', 'regular')"
                            title="Regular Data"
                          >
                            <div class="rfp-circle-inner"></div>
                          </div>
                        </div>
                      </div>
                    </Label>
                    <div class="relative">
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        :value="criterion.weight"
                        @input="handleWeightChange(index, Number($event.target.value))"
                        :class="criterion.weight > 0 && totalWeight > 100 ? 'border-orange-300 bg-orange-50' : ''"
                      />
                      <div v-if="criterion.weight > 0 && totalWeight > 100" class="absolute right-2 top-1/2 transform -translate-y-1/2">
                        <Icons name="alert-triangle" class="h-4 w-4 text-orange-500" />
                      </div>
                    </div>
                    <p v-if="criterion.weight > 0 && totalWeight > 100" class="text-xs text-orange-600">
                      This will trigger auto-adjustment of other criteria
                    </p>
                  </div>
        </div>

                <div class="space-y-2">
                  <Label class="flex items-center gap-2">
                    <span>Description</span>
                    <div class="rfp-data-type-circle-toggle-wrapper">
                      <div class="rfp-data-type-circle-toggle">
                        <div 
                          class="rfp-circle-option rfp-personal-circle" 
                          :class="{ active: getCriteriaDataType(criterion.id, 'description') === 'personal' }"
                          @click="setCriteriaDataType(criterion.id, 'description', 'personal')"
                          title="Personal Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-confidential-circle" 
                          :class="{ active: getCriteriaDataType(criterion.id, 'description') === 'confidential' }"
                          @click="setCriteriaDataType(criterion.id, 'description', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-regular-circle" 
                          :class="{ active: getCriteriaDataType(criterion.id, 'description') === 'regular' }"
                          @click="setCriteriaDataType(criterion.id, 'description', 'regular')"
                          title="Regular Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </Label>
                  <Textarea
                    placeholder="Describe what this criterion evaluates..."
                    :rows="2"
                    v-model="criterion.description"
                  />
                </div>
                
                <div class="flex items-center space-x-2">
                  <Checkbox
                    :id="`veto-${criterion.id}`"
                    v-model="criterion.isVeto"
                  />
                  <Label :html-for="`veto-${criterion.id}`" class="text-sm">
                    Veto Criterion (failing this criterion eliminates the vendor)
                  </Label>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Evaluation & Process Settings -->
        <Card
          v-show="activeTab === 'process' && !hiddenTabs.has('process')"
          class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200"
        >
          <CardHeader>
            <div class="flex items-center gap-2">
              <Icons name="settings" class="h-5 w-5 text-primary" />
              <CardTitle>Evaluation & Process Settings</CardTitle>
            </div>
            <CardDescription>
              Configure evaluation method and process parameters
            </CardDescription>
          </CardHeader>
          <CardContent class="p-6 space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div v-if="!hiddenFields.evaluationMethod" class="space-y-2">
                <div class="flex items-center justify-between">
                  <Label html-for="evaluationMethod" class="flex items-center gap-2">
                    <span>Evaluation Method</span>
                    <div class="rfp-data-type-circle-toggle-wrapper">
                      <div class="rfp-data-type-circle-toggle">
                        <div 
                          class="rfp-circle-option rfp-personal-circle" 
                          :class="{ active: getRFPDataType('evaluationMethod') === 'personal' }"
                          @click="setRFPDataType('evaluationMethod', 'personal')"
                          title="Personal Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-confidential-circle" 
                          :class="{ active: getRFPDataType('evaluationMethod') === 'confidential' }"
                          @click="setRFPDataType('evaluationMethod', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-regular-circle" 
                          :class="{ active: getRFPDataType('evaluationMethod') === 'regular' }"
                          @click="setRFPDataType('evaluationMethod', 'regular')"
                          title="Regular Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </Label>
                  <button
                    @click="hideField('evaluationMethod')"
                    type="button"
                    class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                    title="Remove this field from form"
                  >
                    <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                  </button>
                </div>
                <Select v-model="formData.evaluationMethod">
                  <option value="weighted_scoring">Weighted Scoring</option>
                  <option value="lowest_price">Lowest Price</option>
                  <option value="best_value">Best Value</option>
                </Select>
              </div>
              <div v-if="!hiddenFields.criticalityLevel" class="space-y-2">
                <div class="flex items-center justify-between">
                  <Label html-for="criticalityLevel" class="flex items-center gap-2">
                    <span>Criticality Level</span>
                    <div class="rfp-data-type-circle-toggle-wrapper">
                      <div class="rfp-data-type-circle-toggle">
                        <div 
                          class="rfp-circle-option rfp-personal-circle" 
                          :class="{ active: getRFPDataType('criticalityLevel') === 'personal' }"
                          @click="setRFPDataType('criticalityLevel', 'personal')"
                          title="Personal Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-confidential-circle" 
                          :class="{ active: getRFPDataType('criticalityLevel') === 'confidential' }"
                          @click="setRFPDataType('criticalityLevel', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                        <div 
                          class="rfp-circle-option rfp-regular-circle" 
                          :class="{ active: getRFPDataType('criticalityLevel') === 'regular' }"
                          @click="setRFPDataType('criticalityLevel', 'regular')"
                          title="Regular Data"
                        >
                          <div class="rfp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </Label>
                  <button
                    @click="hideField('criticalityLevel')"
                    type="button"
                    class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                    title="Remove this field from form"
                  >
                    <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                  </button>
                </div>
                <Select v-model="formData.criticalityLevel">
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </Select>
              </div>
            </div>
            
            <div v-if="!hiddenFields.geographicalScope" class="space-y-2">
              <div class="flex items-center justify-between">
                <Label html-for="geographicalScope" class="flex items-center gap-2">
                  <span>Geographical Scope</span>
                  <div class="rfp-data-type-circle-toggle-wrapper">
                    <div class="rfp-data-type-circle-toggle">
                      <div 
                        class="rfp-circle-option rfp-personal-circle" 
                        :class="{ active: getRFPDataType('geographicalScope') === 'personal' }"
                        @click="setRFPDataType('geographicalScope', 'personal')"
                        title="Personal Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-confidential-circle" 
                        :class="{ active: getRFPDataType('geographicalScope') === 'confidential' }"
                        @click="setRFPDataType('geographicalScope', 'confidential')"
                        title="Confidential Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-regular-circle" 
                        :class="{ active: getRFPDataType('geographicalScope') === 'regular' }"
                        @click="setRFPDataType('geographicalScope', 'regular')"
                        title="Regular Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </Label>
                <button
                  @click="hideField('geographicalScope')"
                  type="button"
                  class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                  title="Remove this field from form"
                >
                  <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                </button>
              </div>
              <Input
                id="geographicalScope"
                placeholder="e.g., United States, Global, Europe"
                v-model="formData.geographicalScope"
              />
            </div>
            
            <div v-if="!hiddenFields.complianceRequirements" class="space-y-2">
              <div class="flex items-center justify-between">
                <Label html-for="complianceRequirements" class="flex items-center gap-2">
                  <span>Compliance Requirements</span>
                  <div class="rfp-data-type-circle-toggle-wrapper">
                    <div class="rfp-data-type-circle-toggle">
                      <div 
                        class="rfp-circle-option rfp-personal-circle" 
                        :class="{ active: getRFPDataType('complianceRequirements') === 'personal' }"
                        @click="setRFPDataType('complianceRequirements', 'personal')"
                        title="Personal Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-confidential-circle" 
                        :class="{ active: getRFPDataType('complianceRequirements') === 'confidential' }"
                        @click="setRFPDataType('complianceRequirements', 'confidential')"
                        title="Confidential Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-regular-circle" 
                        :class="{ active: getRFPDataType('complianceRequirements') === 'regular' }"
                        @click="setRFPDataType('complianceRequirements', 'regular')"
                        title="Regular Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </Label>
                <button
                  @click="hideField('complianceRequirements')"
                  type="button"
                  class="p-1 hover:bg-gray-100 rounded-full transition-colors"
                  title="Remove this field from form"
                >
                  <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                </button>
              </div>
              <Textarea
                id="complianceRequirements"
                placeholder="List any compliance requirements (e.g., SOC 2, ISO 27001, GDPR)..."
                :rows="3"
                v-model="formData.complianceRequirements"
              />
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div v-if="!hiddenFields.allowLateSubmissions" class="flex items-center space-x-2">
                <Checkbox
                  id="allowLateSubmissions"
                  v-model="formData.allowLateSubmissions"
                />
                <Label html-for="allowLateSubmissions" class="text-sm flex items-center gap-2">
                  <span>Allow Late Submissions</span>
                  <div class="rfp-data-type-circle-toggle-wrapper">
                    <div class="rfp-data-type-circle-toggle">
                      <div 
                        class="rfp-circle-option rfp-personal-circle" 
                        :class="{ active: getRFPDataType('allowLateSubmissions') === 'personal' }"
                        @click="setRFPDataType('allowLateSubmissions', 'personal')"
                        title="Personal Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-confidential-circle" 
                        :class="{ active: getRFPDataType('allowLateSubmissions') === 'confidential' }"
                        @click="setRFPDataType('allowLateSubmissions', 'confidential')"
                        title="Confidential Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-regular-circle" 
                        :class="{ active: getRFPDataType('allowLateSubmissions') === 'regular' }"
                        @click="setRFPDataType('allowLateSubmissions', 'regular')"
                        title="Regular Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </Label>
                <button
                  @click="hideField('allowLateSubmissions')"
                  type="button"
                  class="p-1 hover:bg-gray-100 rounded-full transition-colors ml-auto"
                  title="Remove this field from form"
                >
                  <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                </button>
              </div>
              <div v-if="!hiddenFields.autoApprove" class="flex items-center space-x-2">
                <Checkbox
                  id="autoApprove"
                  v-model="formData.autoApprove"
                />
                <Label html-for="autoPublish" class="text-sm flex items-center gap-2">
                  <span>Auto-publish when approved</span>
                  <div class="rfp-data-type-circle-toggle-wrapper">
                    <div class="rfp-data-type-circle-toggle">
                      <div 
                        class="rfp-circle-option rfp-personal-circle" 
                        :class="{ active: getRFPDataType('autoPublish') === 'personal' }"
                        @click="setRFPDataType('autoPublish', 'personal')"
                        title="Personal Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-confidential-circle" 
                        :class="{ active: getRFPDataType('autoPublish') === 'confidential' }"
                        @click="setRFPDataType('autoPublish', 'confidential')"
                        title="Confidential Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                      <div 
                        class="rfp-circle-option rfp-regular-circle" 
                        :class="{ active: getRFPDataType('autoPublish') === 'regular' }"
                        @click="setRFPDataType('autoPublish', 'regular')"
                        title="Regular Data"
                      >
                        <div class="rfp-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </Label>
                <Label html-for="autoApprove" class="text-sm" title="When enabled, this RFP is automatically approved by the creator without going through the approval workflow">
                  Auto-approve (no approval workflow required)
                </Label>
                <button
                  @click="hideField('autoApprove')"
                  type="button"
                  class="p-1 hover:bg-gray-100 rounded-full transition-colors ml-auto"
                  title="Remove this field from form"
                >
                  <Icons name="x" class="h-3 w-3 text-gray-500 hover:text-red-500" />
                </button>
              </div>
            </div>
          </CardContent>
        </Card>

      </div>
      </div>

    <!-- Sticky Tips & Guide Button -->
    <button
      @click="showTipsDialog = true"
      class="fixed bottom-6 right-6 z-40 bg-yellow-500 hover:bg-yellow-600 text-white rounded-full p-4 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 group"
      title="Tips & Progress Guide"
    >
      <Icons name="lightbulb" class="h-6 w-6" />
      <span class="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center font-semibold" v-if="hasIncompleteSections">
        !
      </span>
    </button>

    <!-- Tips & Progress Dialog -->
    <div v-if="showTipsDialog" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showTipsDialog = false">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        <!-- Dialog Header -->
        <div class="flex items-center justify-between p-6 border-b">
          <div class="flex items-center gap-3">
            <div class="h-10 w-10 bg-yellow-100 rounded-full flex items-center justify-center">
              <Icons name="lightbulb" class="h-6 w-6 text-yellow-600" />
            </div>
            <h2 class="text-xl font-semibold">Tips & Progress Guide</h2>
          </div>
          <Button
            variant="ghost"
            size="sm"
            @click="showTipsDialog = false"
            class="text-gray-500 hover:text-gray-700"
          >
            <Icons name="x" class="h-5 w-5" />
          </Button>
        </div>

        <!-- Dialog Content -->
        <div class="overflow-y-auto flex-1 p-6 space-y-6">
          <!-- Quick Tips Section -->
          <div>
            <h3 class="text-lg font-semibold mb-4 flex items-center gap-2">
              <Icons name="lightbulb" class="h-5 w-5 text-yellow-500" />
              Quick Tips
            </h3>
            <div class="space-y-3 text-sm">
              <div class="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <p class="font-semibold text-yellow-900 mb-1">Clear Requirements:</p>
                <p class="text-yellow-800">Be specific about your needs to get better proposals.</p>
              </div>
              <div class="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <p class="font-semibold text-yellow-900 mb-1">Evaluation Criteria:</p>
                <p class="text-yellow-800">Use 3-7 criteria with clear weights totaling 100%.</p>
              </div>
              <div class="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <p class="font-semibold text-yellow-900 mb-1">Veto Criteria:</p>
                <p class="text-yellow-800">Mark mandatory requirements as veto criteria.</p>
              </div>
              <div class="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                <p class="font-semibold text-yellow-900 mb-1">Timeline:</p>
                <p class="text-yellow-800">Allow sufficient time for vendor responses (typically 2-4 weeks).</p>
              </div>
            </div>
          </div>

          <!-- Progress Summary Section -->
          <div>
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold">Progress Summary</h3>
              <div class="flex items-center gap-2">
                <div class="text-sm font-medium text-gray-600">Overall:</div>
                <div class="text-lg font-bold" :class="overallProgress === 100 ? 'text-green-600' : overallProgress >= 50 ? 'text-yellow-600' : 'text-red-600'">
                  {{ overallProgress }}%
                </div>
              </div>
            </div>
            
            <!-- Overall Progress Bar -->
            <div class="mb-6">
              <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                <div 
                  class="h-3 rounded-full transition-all duration-500"
                  :class="overallProgress === 100 ? 'bg-green-500' : overallProgress >= 50 ? 'bg-yellow-500' : 'bg-red-500'"
                  :style="{ width: `${overallProgress}%` }"
                ></div>
              </div>
            </div>

            <div class="space-y-2">
              <!-- Basic Information -->
              <div class="border rounded-lg overflow-hidden" :class="basicInfoComplete ? 'border-green-300 bg-green-50/50' : 'border-yellow-300 bg-yellow-50/50'">
                <div class="flex items-center gap-3 p-3">
                  <div class="flex-shrink-0">
                    <div class="h-8 w-8 rounded-full flex items-center justify-center" :class="basicInfoComplete ? 'bg-green-500' : 'bg-yellow-500'">
                      <Icons v-if="basicInfoComplete" name="check-circle" class="h-5 w-5 text-white" />
                      <span v-else class="text-white font-bold text-xs">{{ basicInfoCount }}/4</span>
                    </div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-sm text-gray-900">Basic Information</div>
                    <div v-if="!basicInfoComplete" class="text-xs text-gray-600 mt-1">
                      Missing: {{ getMissingBasicInfo().join(', ') }}
                    </div>
                  </div>
                  <div class="flex-shrink-0">
                    <span class="text-xs font-medium px-2 py-1 rounded-full" :class="basicInfoComplete ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">
                      {{ basicInfoComplete ? 'Complete' : 'Incomplete' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Timeline & Dates -->
              <div class="border rounded-lg overflow-hidden" :class="timelineComplete ? 'border-green-300 bg-green-50/50' : 'border-yellow-300 bg-yellow-50/50'">
                <div class="flex items-center gap-3 p-3">
                  <div class="flex-shrink-0">
                    <div class="h-8 w-8 rounded-full flex items-center justify-center" :class="timelineComplete ? 'bg-green-500' : 'bg-yellow-500'">
                      <Icons v-if="timelineComplete" name="check-circle" class="h-5 w-5 text-white" />
                      <span v-else class="text-white font-bold text-xs">{{ timelineCount }}/2</span>
                    </div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-sm text-gray-900">Timeline & Dates</div>
                    <div v-if="!timelineComplete" class="text-xs text-gray-600 mt-1">
                      Missing: {{ getMissingTimeline().join(', ') }}
                    </div>
                  </div>
                  <div class="flex-shrink-0">
                    <span class="text-xs font-medium px-2 py-1 rounded-full" :class="timelineComplete ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">
                      {{ timelineComplete ? 'Complete' : 'Incomplete' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Budget Information -->
              <div class="border rounded-lg overflow-hidden" :class="budgetComplete ? 'border-green-300 bg-green-50/50' : 'border-yellow-300 bg-yellow-50/50'">
                <div class="flex items-center gap-3 p-3">
                  <div class="flex-shrink-0">
                    <div class="h-8 w-8 rounded-full flex items-center justify-center" :class="budgetComplete ? 'bg-green-500' : 'bg-yellow-500'">
                      <Icons v-if="budgetComplete" name="check-circle" class="h-5 w-5 text-white" />
                      <Icons v-else name="dollar-sign" class="h-4 w-4 text-white" />
                    </div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-sm text-gray-900">Budget Information</div>
                    <div v-if="!budgetComplete" class="text-xs text-gray-600 mt-1">
                      Add estimated value or budget range
                    </div>
                  </div>
                  <div class="flex-shrink-0">
                    <span class="text-xs font-medium px-2 py-1 rounded-full" :class="budgetComplete ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">
                      {{ budgetComplete ? 'Complete' : 'Optional' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Evaluation Criteria -->
              <div class="border rounded-lg overflow-hidden" :class="evaluationComplete ? 'border-green-300 bg-green-50/50' : 'border-red-300 bg-red-50/50'">
                <div class="flex items-center gap-3 p-3">
                  <div class="flex-shrink-0">
                    <div class="h-8 w-8 rounded-full flex items-center justify-center" :class="evaluationComplete ? 'bg-green-500' : 'bg-red-500'">
                      <Icons v-if="evaluationComplete" name="check-circle" class="h-5 w-5 text-white" />
                      <span v-else class="text-white font-bold text-xs">{{ totalWeight }}%</span>
                    </div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-sm text-gray-900">Evaluation Criteria</div>
                    <div v-if="!evaluationComplete" class="text-xs text-gray-600 mt-1">
                      Total weight must equal 100% (currently {{ totalWeight }}%)
                    </div>
                  </div>
                  <div class="flex-shrink-0">
                    <span class="text-xs font-medium px-2 py-1 rounded-full" :class="evaluationComplete ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'">
                      {{ evaluationComplete ? 'Complete' : 'Required' }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- Process Settings -->
              <div class="border rounded-lg overflow-hidden" :class="processSettingsComplete ? 'border-green-300 bg-green-50/50' : 'border-yellow-300 bg-yellow-50/50'">
                <div class="flex items-center gap-3 p-3">
                  <div class="flex-shrink-0">
                    <div class="h-8 w-8 rounded-full flex items-center justify-center" :class="processSettingsComplete ? 'bg-green-500' : 'bg-yellow-500'">
                      <Icons v-if="processSettingsComplete" name="check-circle" class="h-5 w-5 text-white" />
                      <span v-else class="text-white font-bold text-xs">{{ processSettingsCount }}/2</span>
                    </div>
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="font-medium text-sm text-gray-900">Process Settings</div>
                    <div v-if="!processSettingsComplete" class="text-xs text-gray-600 mt-1">
                      Missing: {{ getMissingProcessSettings().join(', ') }}
                    </div>
                  </div>
                  <div class="flex-shrink-0">
                    <span class="text-xs font-medium px-2 py-1 rounded-full" :class="processSettingsComplete ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">
                      {{ processSettingsComplete ? 'Complete' : 'Incomplete' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Upload Progress (if uploading) -->
          <div v-if="isUploadingDocuments && uploadProgress.total > 0">
            <h3 class="text-lg font-semibold mb-4">Upload Progress</h3>
            <Card class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow duration-200">
              <CardContent class="pt-6">
                <div class="space-y-2">
                  <div class="flex justify-between text-sm text-gray-600">
                    <span>{{ uploadProgress.currentDocument }}</span>
                    <span>{{ uploadProgress.current }}/{{ uploadProgress.total }}</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      :style="{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }"
                    ></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <!-- Dialog Footer -->
        <div class="p-6 border-t bg-gray-50">
          <Button @click="showTipsDialog = false" class="w-full">
            Got it!
          </Button>
        </div>
      </div>
    </div>

  <!-- Vendor Portal Preview Modal -->
  <transition name="fade">
    <div
      v-if="showVendorPreview && vendorPreviewPayload"
      class="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 px-4 py-6"
    >
      <div class="flex h-full w-full max-w-7xl flex-col rounded-2xl border border-gray-200 bg-white shadow-2xl">
        <div class="flex items-start justify-between border-b border-gray-200 px-6 py-4">
          <div>
            <p class="text-base font-semibold text-gray-900">Vendor Portal Preview</p>
            <p class="text-sm text-gray-500">Live view of how vendors will experience this RFP</p>
          </div>
          <div class="flex items-center gap-3">
            <Button variant="outline" size="sm" @click="closeVendorPortalPreview" class="text-sm">
              Back to RFP Builder
            </Button>
            <button
              type="button"
              class="inline-flex h-9 w-9 items-center justify-center rounded-full border border-gray-200 text-gray-500 hover:text-gray-700"
              @click="closeVendorPortalPreview"
            >
              <Icons name="x" class="h-4 w-4" />
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-hidden bg-gray-50">
          <div class="h-full overflow-y-auto">
            <VendorPortal
              v-if="vendorPreviewPayload"
              :preview-payload="vendorPreviewPayload"
              @exit-preview="closeVendorPortalPreview"
              :key="vendorPreviewPayload.generatedAt || vendorPreviewPayload.rfpInfo?.rfpNumber || 'vendor-preview'"
            />
          </div>
        </div>
      </div>
    </div>
  </transition>

    <!-- Weight Adjustment Notification -->
    <div v-if="showWeightAdjustmentNotification" class="fixed top-4 right-4 bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md z-50 shadow-lg">
      <div class="flex items-start gap-3">
        <Icons name="info" class="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
        <div class="flex-1">
          <h4 class="text-sm font-semibold text-blue-900 mb-2">Weights Auto-Adjusted</h4>
          <div class="text-sm text-blue-800 space-y-1">
            <p class="mb-2">To maintain 100% total, the following adjustments were made:</p>
            <div v-for="adjustment in weightAdjustmentHistory" :key="adjustment.criterion" class="flex justify-between items-center">
              <span class="font-medium">{{ adjustment.criterion }}:</span>
              <span class="text-xs bg-blue-100 px-2 py-1 rounded">
                {{ adjustment.oldWeight }}% → {{ adjustment.newWeight }}%
              </span>
            </div>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          @click="showWeightAdjustmentNotification = false"
          class="text-blue-600 hover:text-blue-800 p-1"
        >
          <Icons name="x" class="h-4 w-4" />
        </Button>
      </div>
    </div>

    <!-- Draft Recovery Dialog -->
    <div v-if="showDraftRecovery" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-lg w-full mx-4">
        <div class="flex items-center gap-3 mb-4">
          <div class="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
            <Icons name="file-text" class="h-5 w-5 text-blue-600" />
          </div>
          <h3 class="text-lg font-semibold">Resume Previous Work?</h3>
        </div>
        
        <div class="space-y-3 mb-6">
          <p class="text-gray-600">
            We found an auto-saved draft from your previous session. Would you like to continue where you left off?
          </p>
          
          <div class="bg-gray-50 rounded-lg p-3 space-y-2">
            <div v-if="getDraftPreview().title" class="text-sm">
              <span class="font-medium">Title:</span> {{ getDraftPreview().title }}
            </div>
            <div v-if="getDraftPreview().rfpNumber" class="text-sm">
              <span class="font-medium">RFP Number:</span> {{ getDraftPreview().rfpNumber }}
            </div>
            <div v-if="getDraftPreview().lastSaved" class="text-sm text-gray-500">
              <span class="font-medium">Last saved:</span> {{ formatTime(new Date(getDraftPreview().lastSaved)) }}
            </div>
          </div>
        </div>
        
        <div class="flex gap-3">
          <Button
            variant="outline"
            @click="startFresh"
            class="flex-1"
          >
            <Icons name="refresh-cw" class="h-4 w-4 mr-2" />
            Start Fresh
          </Button>
          <Button @click="resumeDraft" class="flex-1">
            <Icons name="download" class="h-4 w-4 mr-2" />
            Resume Draft
          </Button>
        </div>
      </div>
    </div>
  </div>
  
  <!-- TPRM Consent Modal - Outside main content to ensure it's always rendered -->
  <Teleport to="body">
    <TPRMConsentModal
      ref="consentModalRef"
    />
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'
import { PopupService } from '@/popup/popupService'
import Card from '@/components_rfp/ui/Card.vue'
import CardHeader from '@/components_rfp/ui/CardHeader.vue'
import CardTitle from '@/components_rfp/ui/CardTitle.vue'
import CardDescription from '@/components_rfp/ui/CardDescription.vue'
import CardContent from '@/components_rfp/ui/CardContent.vue'
import Button from '@/components_rfp/ui/Button.vue'
import Input from '@/components_rfp/ui/Input.vue'
import Label from '@/components_rfp/ui/Label.vue'
import Textarea from '@/components_rfp/ui/Textarea.vue'
import Select from '@/components_rfp/ui/Select.vue'
import Checkbox from '@/components_rfp/ui/Checkbox.vue'
import Badge from '@/components_rfp/ui/Badge.vue'
import Progress from '@/components_rfp/ui/Progress.vue'
import Icons from '@/components_rfp/ui/Icons.vue'
import { rfpUseToast } from '@/composables/rfpUseToast.js'
import { useRFPStore } from '@/store/index_rfp'
import { useRfpApi } from '@/composables/useRfpApi'
import { buildApiUrl, apiCall } from '@/config/api.js'
import VendorPortal from '@/views/rfp/VendorPortal.vue'
import { getTprmApiV1BaseUrl, getTprmApiUrl, getApiOrigin } from '@/utils/backendEnv'
import TPRMConsentModal from '@/components/Consent/TPRMConsentModal.vue'
import { executeWithTPRMConsent, TPRM_CONSENT_ACTIONS } from '@/utils/tprmConsentManager.js'

// API base URL - use the Django backend endpoints
const API_BASE_URL = getTprmApiV1BaseUrl()
const VENDOR_PREVIEW_STORAGE_KEY = 'vendor_portal_preview_payload'

interface EvaluationCriteria {
  id: string
  name: string
  description: string
  weight: number
  isVeto: boolean
}


const { success, error } = rfpUseToast()
const rfpStore = useRFPStore()
const router = useRouter()
const route = useRoute()

const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Get authenticated headers for axios requests
const { getAuthHeaders } = useRfpApi()

const showDraftRecovery = ref(false)
const lastSaved = ref<Date | null>(null)
const isAutoSaving = ref(false)
const isSubmitting = ref(false)
const isGeneratingDocument = ref(false)
const isUploadingDocuments = ref(false)

// TPRM Consent Modal ref
const consentModalRef = ref(null)
const isMergingDocuments = ref(false)
const uploadProgress = ref({
  current: 0,
  total: 0,
  currentDocument: ''
})
// Track per-document upload state for individual save actions
const perDocUploading = ref<Record<number, boolean>>({})
// Merged document reference
const mergedDocument = ref(null)
// Drag and drop state for reordering documents
const draggedIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

const showVendorPreview = ref(false)
const vendorPreviewPayload = ref<Record<string, any> | null>(null)

const formTabs = [
  { value: 'basic', label: 'Basic Setup', description: 'Core details & custom fields', canHide: false },
  { value: 'documents', label: 'Documents', description: 'Upload and manage files', canHide: true },
  { value: 'budget', label: 'Budget & Timeline', description: 'Financials and schedule', canHide: true },
  { value: 'criteria', label: 'Evaluation Criteria', description: 'Weights & scoring', canHide: true },
  { value: 'process', label: 'Process Settings', description: 'Methods & compliance', canHide: true }
]
const activeTab = ref(formTabs[0].value)

// Track which tabs are hidden/removed
const hiddenTabs = ref<Set<string>>(new Set())
const showHiddenTabs = ref(false) // Toggle to show/hide the hidden tabs section

// Document upload functionality
const newDocument = ref({
  name: '',
  file: null,
  fileName: '',
  fileSize: 0
})

const uploadedDocuments = ref([])

// RFP Types from database
const rfpTypes = ref<string[]>([])
const loadingRfpTypes = ref(false)

// Custom Fields
const customFieldsSchema = ref<any[]>([])
const loadingCustomFields = ref(false)

// Categorized Custom Fields
const customFieldCategories = ref([
  { id: 'company', label: 'Company' },
  { id: 'financial', label: 'Financial' },
  { id: 'compliance', label: 'Compliance' },
  { id: 'documents', label: 'Documents' },
  { id: 'team', label: 'Team' },
  { id: 'other', label: 'Other' }
])

const activeCustomFieldCategory = ref('company')

// Track which optional fields are hidden/removed from the form
const hiddenFields = ref<Record<string, boolean>>({
  category: false,
  estimatedValue: false,
  currency: false,
  timeline: false,
  budgetMin: false,
  budgetMax: false,
  evaluationPeriodEnd: false,
  evaluationMethod: false,
  criticalityLevel: false,
  geographicalScope: false,
  complianceRequirements: false,
  allowLateSubmissions: false,
  autoApprove: false
})

// Track which custom fields are hidden/removed
const hiddenCustomFields = ref<Set<string>>(new Set())

// Computed properties for tab management
const visibleTabs = computed(() => {
  return formTabs.filter(tab => !hiddenTabs.value.has(tab.value))
})

const hiddenTabsList = computed(() => {
  return formTabs.filter(tab => hiddenTabs.value.has(tab.value))
})

// Get display index for tab (sequential numbering excluding hidden tabs)
const getTabDisplayIndex = (tabValue: string) => {
  const visible = visibleTabs.value
  const index = visible.findIndex(t => t.value === tabValue)
  return index >= 0 ? index + 1 : formTabs.findIndex(t => t.value === tabValue) + 1
}

// Store field definitions by category
const categoryCustomFields = ref<Record<string, Array<{
  id: string
  label: string
  type: string
  name: string
  order?: number
}>>>({
  company: [],
  financial: [],
  compliance: [],
  documents: [],
  team: [],
  other: []
})

// Store field values by category
const categoryCustomFieldData = ref<Record<string, Record<string, any>>>({
  company: {},
  financial: {},
  compliance: {},
  documents: {},
  team: {},
  other: {}
})

// New custom field form
const newCustomField = ref({
  label: '',
  type: 'text',
  value: '',
  category: 'company',
  fileData: null as { file: File, fileName: string } | null
})

// Custom field types
const customFieldTypes = ref([
  { value: 'text', label: 'Text' },
  { value: 'textarea', label: 'Textarea' },
  { value: 'number', label: 'Number' },
  { value: 'decimal', label: 'Decimal' },
  { value: 'date', label: 'Date' },
  { value: 'datetime', label: 'DateTime' },
  { value: 'email', label: 'Email' },
  { value: 'url', label: 'URL' },
  { value: 'file', label: 'File' }
])

// Drag and drop state for custom fields
const draggedCustomFieldIndex = ref<number | null>(null)
const draggedCustomFieldCategory = ref<string | null>(null)
const dragOverCustomFieldIndex = ref<number | null>(null)
const dragOverCustomFieldCategory = ref<string | null>(null)

const formData = ref({
  // Basic Information
  rfpNumber: '',
  title: '',
  description: '',
  type: '',
  category: '',
  
  // Financial Information
  estimatedValue: '',
  currency: 'USD',
  budgetMin: '',
  budgetMax: '',
  
  // Timeline Information
  issueDate: '',
  deadline: '',
  evaluationPeriodEnd: '',
  timeline: '',
  
  // Evaluation & Process
  evaluationMethod: 'weighted_scoring',
  criticalityLevel: 'medium',
  
  // Scope & Requirements
  geographicalScope: '',
  complianceRequirements: '',
  
  // Additional Options
  allowLateSubmissions: false,
  autoApprove: false,
  
  // Custom Fields (dynamic based on RFP type)
  customFields: {} as Record<string, any>
})

const criteria = ref<EvaluationCriteria[]>([
  {
    id: '1',
    name: 'Technical Capability',
    description: 'Vendor\'s technical expertise and infrastructure',
    weight: 30,
    isVeto: true,
  },
  {
    id: '2',
    name: 'Cost Effectiveness',
    description: 'Value for money and pricing structure',
    weight: 25,
    isVeto: false,
  },
  {
    id: '3',
    name: 'Experience & References',
    description: 'Previous experience and client references',
    weight: 20,
    isVeto: true,
  },
  {
    id: '4',
    name: 'Implementation Timeline',
    description: 'Proposed timeline and delivery schedule',
    weight: 15,
    isVeto: false,
  },
  {
    id: '5',
    name: 'Support & Maintenance',
    description: 'Ongoing support and maintenance capabilities',
    weight: 10,
    isVeto: false,
  },
])

// Data type classification for RFP fields
// Stores data types (personal, confidential, regular) for each field
const rfpFieldDataTypes = reactive({
  rfpNumber: 'regular',
  title: 'regular',
  description: 'regular',
  type: 'regular',
  category: 'regular',
  issueDate: 'regular',
  deadline: 'regular',
  evaluationPeriodEnd: 'regular',
  timeline: 'regular',
  estimatedValue: 'confidential',
  currency: 'regular',
  budgetMin: 'confidential',
  budgetMax: 'confidential',
  evaluationMethod: 'regular',
  criticalityLevel: 'regular',
  geographicalScope: 'regular',
  complianceRequirements: 'regular',
  allowLateSubmissions: 'regular',
  autoPublish: 'regular'
})

// Data type classification for evaluation criteria
// Stores data types for each field in each criterion: { criterion_id: { field_name: 'data_type' } }
const criteriaDataTypes = reactive({})

// Method to set data type for an RFP field
function setRFPDataType(fieldName: string, type: string) {
  if (rfpFieldDataTypes.hasOwnProperty(fieldName)) {
    rfpFieldDataTypes[fieldName] = type
    console.log(`Data type selected for RFP field ${fieldName}:`, type)
  }
}

// Get data type for an RFP field
function getRFPDataType(fieldName: string) {
  return rfpFieldDataTypes[fieldName] || 'regular'
}

// Method to set data type for a criterion field
function setCriteriaDataType(criterionId: string, fieldName: string, type: string) {
  if (!criteriaDataTypes[criterionId]) {
    criteriaDataTypes[criterionId] = reactive({})
  }
  criteriaDataTypes[criterionId][fieldName] = type
  console.log(`Data type selected for criterion ${criterionId}, field ${fieldName}:`, type)
}

// Get data type for a criterion field
function getCriteriaDataType(criterionId: string, fieldName: string) {
  return criteriaDataTypes[criterionId]?.[fieldName] || 'regular'
}

// Helper function to build data_inventory JSON for RFP
function buildRFPDataInventory() {
  const fieldLabelMap = {
    rfpNumber: 'RFP Number',
    title: 'RFP Title',
    description: 'Description',
    type: 'RFP Type',
    category: 'Category',
    issueDate: 'Issue Date',
    deadline: 'Submission Deadline',
    evaluationPeriodEnd: 'Evaluation Period End',
    timeline: 'Project Timeline',
    estimatedValue: 'Estimated Value',
    currency: 'Currency',
    budgetMin: 'Minimum Budget',
    budgetMax: 'Maximum Budget',
    evaluationMethod: 'Evaluation Method',
    criticalityLevel: 'Criticality Level',
    geographicalScope: 'Geographical Scope',
    complianceRequirements: 'Compliance Requirements',
    allowLateSubmissions: 'Allow Late Submissions',
    autoPublish: 'Auto Publish'
  }

  const dataInventory = {}
  
  // Build flat structure: {"Field Label": "data_type"}
  for (const [fieldName, dataType] of Object.entries(rfpFieldDataTypes)) {
    if (fieldLabelMap[fieldName]) {
      const fieldLabel = fieldLabelMap[fieldName]
      dataInventory[fieldLabel] = dataType
    }
  }
  
  console.log('📋 RFP Data Inventory JSON:', JSON.stringify(dataInventory, null, 2))
  return dataInventory
}

// Helper function to build data_inventory JSON for a criterion
function buildCriteriaDataInventory(criterion: EvaluationCriteria) {
  const fieldLabelMap = {
    name: 'Criteria Name',
    description: 'Criteria Description',
    weight: 'Weight Percentage',
    isVeto: 'Is Veto',
    evaluationType: 'Evaluation Type',
    minScore: 'Min Score',
    maxScore: 'Max Score'
  }
  
  const dataInventory = {}
  const criterionId = criterion.id
  
  if (criterionId && criteriaDataTypes[criterionId]) {
    for (const [fieldName, dataType] of Object.entries(criteriaDataTypes[criterionId])) {
      if (fieldLabelMap[fieldName]) {
        const fieldLabel = fieldLabelMap[fieldName]
        dataInventory[fieldLabel] = dataType
      }
    }
  }
  
  console.log(`📋 Criterion ${criterionId} Data Inventory JSON:`, JSON.stringify(dataInventory, null, 2))
  return Object.keys(dataInventory).length > 0 ? dataInventory : {}
}


const totalWeight = computed(() => {
  return criteria.value.reduce((sum, criterion) => sum + criterion.weight, 0)
})

// Tips & Progress Dialog
const showTipsDialog = ref(false)

// Check if there are incomplete sections
const hasIncompleteSections = computed(() => {
  return !(
    formData.value.rfpNumber && 
    formData.value.title && 
    formData.value.description && 
    formData.value.type &&
    formData.value.issueDate && 
    formData.value.deadline &&
    (formData.value.estimatedValue || (formData.value.budgetMin && formData.value.budgetMax)) &&
    totalWeight.value === 100 &&
    formData.value.evaluationMethod && 
    formData.value.criticalityLevel
  )
})

// Progress Summary Computed Properties
const basicInfoComplete = computed(() => {
  return !!(formData.value.rfpNumber && formData.value.title && formData.value.description && formData.value.type)
})

const basicInfoCount = computed(() => {
  let count = 0
  if (formData.value.rfpNumber) count++
  if (formData.value.title) count++
  if (formData.value.description) count++
  if (formData.value.type) count++
  return count
})

const timelineComplete = computed(() => {
  return !!(formData.value.issueDate && formData.value.deadline)
})

const timelineCount = computed(() => {
  let count = 0
  if (formData.value.issueDate) count++
  if (formData.value.deadline) count++
  return count
})

const budgetComplete = computed(() => {
  return !!(formData.value.estimatedValue || (formData.value.budgetMin && formData.value.budgetMax))
})

const evaluationComplete = computed(() => {
  return totalWeight.value === 100
})

const processSettingsComplete = computed(() => {
  return !!(formData.value.evaluationMethod && formData.value.criticalityLevel)
})

const processSettingsCount = computed(() => {
  let count = 0
  if (formData.value.evaluationMethod) count++
  if (formData.value.criticalityLevel) count++
  return count
})

const overallProgress = computed(() => {
  let completed = 0
  const total = 5
  
  if (basicInfoComplete.value) completed++
  if (timelineComplete.value) completed++
  if (budgetComplete.value) completed++
  if (evaluationComplete.value) completed++
  if (processSettingsComplete.value) completed++
  
  return Math.round((completed / total) * 100)
})

// Helper functions for missing fields
const getMissingBasicInfo = () => {
  const missing = []
  if (!formData.value.rfpNumber) missing.push('RFP Number')
  if (!formData.value.title) missing.push('Title')
  if (!formData.value.description) missing.push('Description')
  if (!formData.value.type) missing.push('Type')
  return missing
}

const getMissingTimeline = () => {
  const missing = []
  if (!formData.value.issueDate) missing.push('Issue Date')
  if (!formData.value.deadline) missing.push('Deadline')
  return missing
}

const getMissingProcessSettings = () => {
  const missing = []
  if (!formData.value.evaluationMethod) missing.push('Evaluation Method')
  if (!formData.value.criticalityLevel) missing.push('Criticality Level')
  return missing
}

// Check if there's an existing draft being edited
const hasExistingDraft = computed(() => {
  const rfpId = localStorage.getItem('current_rfp_id')
  return rfpId && rfpId !== 'null' && rfpId !== ''
})

// Track weight adjustments for notifications
const weightAdjustmentHistory = ref<Array<{criterion: string, oldWeight: number, newWeight: number}>>([])
const showWeightAdjustmentNotification = ref(false)


const isFormValid = computed(() => {
  // Check if we're in change request mode (updating existing RFP)
  const changeRequestMode = route.query.mode === 'change_request'
  const isUpdate = hasExistingDraft.value || changeRequestMode
  
  // Check required fields
  if (!formData.value.title || !formData.value.description || !formData.value.type) {
    return false
  }
  
  // In update mode, allow saving even if rfpNumber/deadline/issueDate are missing
  // (they might not be editable or already exist)
  if (!isUpdate) {
    if (!formData.value.rfpNumber || !formData.value.deadline || !formData.value.issueDate) {
      return false
    }
  }
  
  // Check evaluation criteria - be more lenient in update mode
  if (criteria.value.length > 0) {
    // If criteria exist, validate them
    if (totalWeight.value !== 100) {
      // In update mode, allow saving even if weights don't total 100 (can be fixed later)
      if (!isUpdate) {
        return false
      }
    }
    
    // Validate that all criteria have names and descriptions
    const hasInvalidCriteria = criteria.value.some(criterion => 
      !criterion.name?.trim() || !criterion.description?.trim()
    )
    
    if (hasInvalidCriteria) {
      return false
    }
  } else {
    // No criteria - allow in update mode (they might be added later or already exist in DB)
    // but require criteria for new RFPs
    if (!isUpdate) {
      return false
    }
  }
  
  return true
})

const canPreviewVendorPortal = computed(() => {
  return Boolean(
    formData.value.rfpNumber &&
    formData.value.title &&
    formData.value.description &&
    formData.value.type
  )
})

const cloneJson = (value: any, fallback: any = Array.isArray(value) ? [] : {}) => {
  try {
    return JSON.parse(JSON.stringify(value ?? fallback))
  } catch (err) {
    console.warn('cloneJson fallback triggered', err)
    return fallback
  }
}

let autoSaveInterval: any = null


// Fetch RFP types from database
const fetchRfpTypes = async () => {
  try {
    loadingRfpTypes.value = true
    console.log('📡 Fetching RFP types from API...')
    
    const response = await axios.get(`${API_BASE_URL}/rfp-types/types/`, {
      headers: getAuthHeaders()
    })
    
    if (response.data && response.data.success && response.data.rfp_types) {
      rfpTypes.value = response.data.rfp_types
      console.log('✅ Loaded RFP types:', rfpTypes.value)
    } else {
      console.warn('⚠️ No RFP types found in response, using empty array')
      rfpTypes.value = []
    }
  } catch (err) {
    console.error('❌ Error fetching RFP types:', err)
    // Fallback to empty array if API fails
    rfpTypes.value = []
    error('Load Error', 'Failed to load RFP types. Please refresh the page.')
  } finally {
    loadingRfpTypes.value = false
  }
}

// Fetch custom fields for selected RFP type
// Helper function to sanitize field names from labels/names
const sanitizeFieldName = (text: string): string => {
  if (!text) return ''
  // Convert to lowercase, replace spaces and special chars with underscores
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9_]/g, '_') // Replace non-alphanumeric (except underscore) with underscore
    .replace(/_+/g, '_') // Replace multiple underscores with single
    .replace(/^_|_$/g, '') // Remove leading/trailing underscores
}

// Helper function to generate a proper field name from field data
const generateFieldName = (field: any, key: string, index: number): string => {
  // Priority: 1. field.name, 2. field.label (sanitized), 3. key (sanitized), 4. sanitized label from name
  if (field?.name && typeof field.name === 'string' && field.name.trim()) {
    return sanitizeFieldName(field.name)
  }
  if (field?.label && typeof field.label === 'string' && field.label.trim()) {
    return sanitizeFieldName(field.label)
  }
  if (key && key.trim() && key !== 'field_' + index) {
    return sanitizeFieldName(key)
  }
  // Last resort: use index but with a descriptive prefix
  return `custom_field_${index}`
}

// Helper function to map old field names (field_0, field_1, etc.) to new field names
const mapOldFieldNamesToNew = (oldCustomFields: Record<string, any>, schema: any[]): Record<string, any> => {
  if (!oldCustomFields || !schema || schema.length === 0) {
    return oldCustomFields || {}
  }
  
  const mappedFields: Record<string, any> = {}
  const oldKeys = Object.keys(oldCustomFields)
  
  // Check if we have old-style field names (field_0, field_1, etc.)
  const hasOldStyleNames = oldKeys.some(key => /^field_\d+$/.test(key))
  
  if (hasOldStyleNames) {
    // Map old field names by index to new field names from schema
    oldKeys.forEach(oldKey => {
      const match = oldKey.match(/^field_(\d+)$/)
      if (match) {
        const index = parseInt(match[1], 10)
        if (index >= 0 && index < schema.length) {
          const newFieldName = schema[index]?.name
          if (newFieldName) {
            mappedFields[newFieldName] = oldCustomFields[oldKey]
          }
        }
      } else {
        // Keep non-old-style keys as-is
        mappedFields[oldKey] = oldCustomFields[oldKey]
      }
    })
    console.log('🔄 Mapped old field names to new names:', { old: oldCustomFields, new: mappedFields })
    return mappedFields
  }
  
  // No old-style names, return as-is
  return oldCustomFields
}

const fetchCustomFields = async (rfpType: string) => {
  if (!rfpType || !rfpType.trim()) {
    customFieldsSchema.value = []
    formData.value.customFields = {}
    return
  }
  
  try {
    loadingCustomFields.value = true
    console.log('📡 Fetching custom fields for RFP type:', rfpType)
    
    const response = await axios.get(`${API_BASE_URL}/rfp-types/custom_fields/?rfp_type=${encodeURIComponent(rfpType)}`, {
      headers: getAuthHeaders()
    })
    
    if (response.data && response.data.success) {
      const customFieldsData = response.data.custom_fields
      
      if (customFieldsData && typeof customFieldsData === 'object') {
        // Convert custom_fields JSON to array format for rendering
        // Expected format: { fields: [{ name, label, type, required, ... }] }
        if (Array.isArray(customFieldsData.fields)) {
          customFieldsSchema.value = customFieldsData.fields
        } else if (Array.isArray(customFieldsData)) {
          customFieldsSchema.value = customFieldsData
        } else {
          // If it's an object with field definitions, convert to array
          customFieldsSchema.value = Object.keys(customFieldsData).map((key, index) => {
            const field = customFieldsData[key]
            // Generate proper field name from actual field data
            const fieldName = generateFieldName(field, key, index)
            return {
              name: fieldName, // Use generated field name
              label: field?.label || field?.name || key,
              type: field?.type || 'text',
              required: field?.required || false,
              placeholder: field?.placeholder,
              help_text: field?.help_text || field?.description,
              options: field?.options,
              rows: field?.rows,
              default: field?.default,
              // Spread other properties but don't override name
              ...Object.fromEntries(
                Object.entries(field || {}).filter(([k]) => k !== 'name')
              )
            }
          })
        }
        
        // Ensure all fields have unique names based on actual field names/labels
        const nameSet = new Set<string>()
        customFieldsSchema.value = customFieldsSchema.value.map((field, index) => {
          // Generate proper field name if not already set or if it's a generic one
          let fieldName = field.name
          if (!fieldName || fieldName.startsWith('field_') || fieldName.match(/^custom_field_\d+$/)) {
            // Regenerate from label/name if current name is generic
            fieldName = generateFieldName(field, field.name || '', index)
          } else {
            // Sanitize existing name
            fieldName = sanitizeFieldName(fieldName)
          }
          
          // Ensure uniqueness - if duplicate, append index
          const originalName = fieldName
          let counter = 1
          while (nameSet.has(fieldName)) {
            fieldName = `${originalName}_${counter}`
            counter++
          }
          nameSet.add(fieldName)
          
          return {
            ...field,
            name: fieldName
          }
        })
        
        // Initialize custom fields values - ensure each field has its own unique property
        // First, map any old field names (field_0, field_1, etc.) to new field names
        const mappedCustomFields = mapOldFieldNamesToNew(
          formData.value.customFields || {},
          customFieldsSchema.value
        )
        
        // Create a new object to ensure Vue reactivity
        const newCustomFields: Record<string, any> = {}
        
        customFieldsSchema.value.forEach(field => {
          // Use the field name from schema (already validated as unique)
          const fieldName = String(field.name)
          
          // Check if we have an existing value for this field (from mapped fields or original)
          const existingValue = mappedCustomFields[fieldName] ?? formData.value.customFields?.[fieldName]
          
          // Initialize with existing value, default, or empty value
          if (existingValue !== undefined && existingValue !== null && existingValue !== '') {
            newCustomFields[fieldName] = existingValue
          } else if (field.default !== undefined) {
            newCustomFields[fieldName] = field.default
          } else if (field.type === 'checkbox') {
            newCustomFields[fieldName] = false
          } else {
            newCustomFields[fieldName] = ''
          }
        })
        
        // Ensure customFields object exists
        if (!formData.value.customFields) {
          formData.value.customFields = {}
        }
        
        // Set each property individually to ensure Vue tracks them separately
        Object.keys(newCustomFields).forEach(key => {
          // Use Vue's reactivity by directly assigning to the reactive object
          formData.value.customFields[key] = newCustomFields[key]
        })
        
        // Also ensure any fields in schema but not in values get initialized
        customFieldsSchema.value.forEach(field => {
          const fieldName = String(field.name)
          if (!(fieldName in formData.value.customFields)) {
            if (field.default !== undefined) {
              formData.value.customFields[fieldName] = field.default
            } else if (field.type === 'checkbox') {
              formData.value.customFields[fieldName] = false
            } else {
              formData.value.customFields[fieldName] = ''
            }
          }
        })
        
        console.log('✅ Loaded custom fields schema:', customFieldsSchema.value.map(f => ({ 
          name: f.name, 
          label: f.label, 
          type: f.type,
          required: f.required
        })))
        console.log('✅ Total fields in schema:', customFieldsSchema.value.length)
        console.log('✅ Initialized custom fields values:', Object.keys(formData.value.customFields).map(k => ({ 
          key: k, 
          value: formData.value.customFields[k],
          type: typeof formData.value.customFields[k],
          isEmpty: formData.value.customFields[k] === '' || formData.value.customFields[k] === null || formData.value.customFields[k] === undefined
        })))
        console.log('✅ Custom fields object structure:', formData.value.customFields)
        
        // Verify all schema fields are initialized
        const missingFields = customFieldsSchema.value.filter(field => {
          const fieldName = String(field.name)
          return !(fieldName in formData.value.customFields)
        })
        if (missingFields.length > 0) {
          console.warn('⚠️ Some schema fields are not initialized:', missingFields.map(f => f.name))
        }
      } else {
        customFieldsSchema.value = []
        formData.value.customFields = {}
        console.log('ℹ️ No custom fields defined for this RFP type')
      }
    } else {
      customFieldsSchema.value = []
      formData.value.customFields = {}
      console.warn('⚠️ No custom fields found in response')
    }
  } catch (err) {
    console.error('❌ Error fetching custom fields:', err)
    customFieldsSchema.value = []
    formData.value.customFields = {}
    // Don't show error toast for missing custom fields (it's optional)
    if (err.response?.status !== 404) {
      error('Load Error', 'Failed to load custom fields. Please try again.')
    }
  } finally {
    loadingCustomFields.value = false
  }
}

// Watch for RFP type changes to fetch custom fields
watch(() => formData.value.type, (newType, oldType) => {
  if (newType && newType !== oldType) {
    console.log('🔄 RFP type changed to:', newType)
    fetchCustomFields(newType).catch(err => {
      console.error('Error fetching custom fields:', err)
    })
  } else if (!newType) {
    // Clear custom fields if type is cleared
    customFieldsSchema.value = []
    formData.value.customFields = {}
  }
})

// Categorized Custom Fields Functions

// Load categorized custom fields from saved data
const loadCategorizedCustomFields = (categorizedFields: Record<string, Record<string, any>>) => {
  console.log('📥 Loading categorized custom fields:', categorizedFields)
  
  Object.keys(categorizedFields).forEach(category => {
    const categoryData = categorizedFields[category]
    
    if (!categoryData || typeof categoryData !== 'object') {
      return
    }
    
    // Initialize category if needed
    if (!categoryCustomFields.value[category]) {
      categoryCustomFields.value[category] = []
    }
    if (!categoryCustomFieldData.value[category]) {
      categoryCustomFieldData.value[category] = {}
    }
    
    // Reconstruct field definitions and values
    Object.keys(categoryData).forEach(fieldName => {
      const fieldValue = categoryData[fieldName]
      
      // Try to infer field type from value
      let fieldType = 'text'
      if (typeof fieldValue === 'number') {
        fieldType = Number.isInteger(fieldValue) ? 'number' : 'decimal'
      } else if (typeof fieldValue === 'boolean') {
        fieldType = 'text' // Store as text representation
      } else if (fieldValue && typeof fieldValue === 'object' && fieldValue.fileName) {
        fieldType = 'file'
      } else if (typeof fieldValue === 'string') {
        // Try to detect date format
        if (/^\d{4}-\d{2}-\d{2}$/.test(fieldValue)) {
          fieldType = 'date'
        } else if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(fieldValue)) {
          fieldType = 'datetime'
        } else if (fieldValue.includes('@')) {
          fieldType = 'email'
        } else if (fieldValue.startsWith('http://') || fieldValue.startsWith('https://')) {
          fieldType = 'url'
        } else if (fieldValue.length > 100) {
          fieldType = 'textarea'
        }
      }
      
      // Generate a label from field name (convert snake_case to Title Case)
      const fieldLabel = fieldName
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())
      
      // Create field definition
      const fieldId = `${category}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      const fieldDef = {
        id: fieldId,
        label: fieldLabel,
        type: fieldType,
        name: fieldName,
        order: categoryCustomFields.value[category].length
      }
      
      // Add to category fields
      categoryCustomFields.value[category].push(fieldDef)
      
      // Store field value
      categoryCustomFieldData.value[category][fieldName] = fieldValue
    })
    
    console.log(`✅ Loaded ${categoryCustomFields.value[category].length} fields for category: ${category}`)
  })
}

// Generate unique field name from label
const generateCustomFieldName = (label: string, category: string): string => {
  const baseName = sanitizeFieldName(label)
  const categoryFields = categoryCustomFields.value[category] || []
  const existingNames = categoryFields.map(field => field.name)
  
  let candidate = baseName || `custom_field_${categoryFields.length + 1}`
  let counter = 1
  while (existingNames.includes(candidate)) {
    candidate = `${baseName}_${counter}`
    counter++
  }
  return candidate
}

// Add custom field to category
const addCustomFieldToCategory = (category: string) => {
  if (!newCustomField.value.label?.trim()) {
    error('Validation Error', 'Field label is required.')
    return
  }
  
  if (!newCustomField.value.value && newCustomField.value.type !== 'file') {
    error('Validation Error', 'Field value is required.')
    return
  }
  
  if (newCustomField.value.type === 'file' && !newCustomField.value.fileData) {
    error('Validation Error', 'Please select a file.')
    return
  }
  
  const uniqueName = generateCustomFieldName(newCustomField.value.label, category)
  const fieldId = `${category}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  
  // Determine field value
  let fieldValue: any = newCustomField.value.value
  if (newCustomField.value.type === 'file' && newCustomField.value.fileData) {
    // For files, store file metadata
    fieldValue = {
      fileName: newCustomField.value.fileData.fileName,
      fileSize: newCustomField.value.fileData.file.size,
      fileType: newCustomField.value.fileData.file.type,
      uploaded: false,
      file: newCustomField.value.fileData.file
    }
  } else if (newCustomField.value.type === 'number' || newCustomField.value.type === 'decimal') {
    fieldValue = Number(newCustomField.value.value)
  }
  
  // Create field definition
  const newField = {
    id: fieldId,
    label: newCustomField.value.label.trim(),
    type: newCustomField.value.type,
    name: uniqueName,
    order: categoryCustomFields.value[category]?.length || 0
  }
  
  // Add to category fields
  if (!categoryCustomFields.value[category]) {
    categoryCustomFields.value[category] = []
  }
  categoryCustomFields.value[category].push(newField)
  
  // Store field value
  if (!categoryCustomFieldData.value[category]) {
    categoryCustomFieldData.value[category] = {}
  }
  categoryCustomFieldData.value[category][uniqueName] = fieldValue
  
  // Reset form
  newCustomField.value = {
    label: '',
    type: 'text',
    value: '',
    category: category,
    fileData: null
  }
  
  success('Field Added', `Custom field "${newField.label}" added to ${customFieldCategories.value.find(c => c.id === category)?.label || category} category.`)
}

// Remove custom field from category
const removeCustomFieldFromCategory = (fieldId: string, category: string) => {
  const categoryFields = categoryCustomFields.value[category] || []
  const index = categoryFields.findIndex(field => field.id === fieldId)
  
  if (index !== -1) {
    const field = categoryFields[index]
    const fieldName = field.name
    
    // Remove from fields array
    categoryCustomFields.value[category].splice(index, 1)
    
    // Remove from data
    if (categoryCustomFieldData.value[category] && fieldName) {
      delete categoryCustomFieldData.value[category][fieldName]
    }
    
    success('Field Removed', `Custom field "${field.label}" removed.`)
  }
}

// Get custom field value
const getCustomFieldValue = (field: any, category: string): any => {
  if (!field || !field.name) return null
  return categoryCustomFieldData.value[category]?.[field.name] || null
}

// Get custom field type label
const getCustomFieldTypeLabel = (type: string): string => {
  const typeObj = customFieldTypes.value.find(t => t.value === type)
  return typeObj?.label || type
}

// Handle custom field file change
const handleCustomFieldFileChange = (event: Event, category: string) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (file) {
    newCustomField.value.fileData = {
      file: file,
      fileName: file.name
    }
    newCustomField.value.category = category
  }
}

// Download custom field file
const downloadCustomFieldFile = async (field: any, category: string) => {
  const fileData = getCustomFieldValue(field, category)
  if (!fileData || !fileData.file) {
    error('Error', 'File not found.')
    return
  }
  
  // Create download link
  const url = window.URL.createObjectURL(fileData.file)
  const link = document.createElement('a')
  link.href = url
  link.download = fileData.fileName || 'file'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
  
  success('Download Started', `Downloading ${fileData.fileName}`)
}

// Drag and drop handlers for custom fields
const handleCustomFieldDragStart = (index: number, category: string, event: DragEvent) => {
  draggedCustomFieldIndex.value = index
  draggedCustomFieldCategory.value = category
  event.dataTransfer!.effectAllowed = 'move'
  event.dataTransfer!.setData('text/html', `${category}-${index}`)
}

const handleCustomFieldDragOver = (index: number, category: string, event: DragEvent) => {
  event.preventDefault()
  event.dataTransfer!.dropEffect = 'move'
  if (draggedCustomFieldIndex.value !== null && draggedCustomFieldCategory.value === category) {
    dragOverCustomFieldIndex.value = index
    dragOverCustomFieldCategory.value = category
  }
}

const handleCustomFieldDragLeave = (index: number, category: string, event: DragEvent) => {
  event.preventDefault()
  dragOverCustomFieldIndex.value = null
  dragOverCustomFieldCategory.value = null
}

const handleCustomFieldDrop = (index: number, category: string, event: DragEvent) => {
  event.preventDefault()
  
  if (draggedCustomFieldIndex.value === null || draggedCustomFieldCategory.value !== category) {
    draggedCustomFieldIndex.value = null
    draggedCustomFieldCategory.value = null
    dragOverCustomFieldIndex.value = null
    dragOverCustomFieldCategory.value = null
    return
  }
  
  if (draggedCustomFieldIndex.value === index) {
    draggedCustomFieldIndex.value = null
    draggedCustomFieldCategory.value = null
    dragOverCustomFieldIndex.value = null
    dragOverCustomFieldCategory.value = null
    return
  }
  
  // Reorder fields
  const fields = categoryCustomFields.value[category]
  const draggedField = fields[draggedCustomFieldIndex.value]
  
  // Remove from old position
  fields.splice(draggedCustomFieldIndex.value, 1)
  
  // Insert at new position
  fields.splice(index, 0, draggedField)
  
  // Update order values
  fields.forEach((field, idx) => {
    field.order = idx
  })
  
  // Reset drag state
  draggedCustomFieldIndex.value = null
  draggedCustomFieldCategory.value = null
  dragOverCustomFieldIndex.value = null
  dragOverCustomFieldCategory.value = null
  
  success('Field Reordered', 'Custom field order updated.')
}

// Auto-save functionality
onMounted(async () => {
  await loggingService.logPageView('RFP', 'Phase 1 - RFP Creation')
  
  // Verify consent modal is available after mount
  await nextTick()
  if (consentModalRef.value) {
    console.log('✅ [TPRM Consent] Consent modal ref is available after mount')
  } else {
    console.warn('⚠️ [TPRM Consent] Consent modal ref not available after mount - component may not be rendered')
  }
  
  // Fetch RFP types from database
  await fetchRfpTypes()
  
  // Check if we're editing from a change request FIRST - this takes priority
  const changeRequestMode = route.query.mode === 'change_request'
  const changeRequestId = route.query.changeRequest
  const rfpId = route.query.rfpId
  
  if (changeRequestMode && rfpId) {
    try {
      console.log('🔄 Loading RFP for change request editing:', rfpId)
      await loadRFPForChangeRequest(rfpId)
      // Skip draft recovery when in change request mode
      return // Exit early to prevent draft recovery dialog
    } catch (error) {
      console.error('❌ Error loading RFP for change request:', error)
      // If change request loading fails, continue to normal flow
    }
  }
  
  // Check if we're editing an existing draft from DraftManager
  const editDraft = localStorage.getItem('edit_rfp_draft')
  if (editDraft) {
    try {
      const draftData = JSON.parse(editDraft)
      console.log('📥 Loading draft for editing from DraftManager:')
      console.log('📋 Full draft data:', draftData)
      console.log('📋 Draft data keys:', Object.keys(draftData))
      console.log('📋 Field check:', {
        rfp_number: draftData.rfp_number,
        rfp_title: draftData.rfp_title,
        description: draftData.description,
        rfp_type: draftData.rfp_type,
        category: draftData.category,
        estimated_value: draftData.estimated_value,
        currency: draftData.currency,
        budget_range_min: draftData.budget_range_min,
        budget_range_max: draftData.budget_range_max,
        issue_date: draftData.issue_date,
        submission_deadline: draftData.submission_deadline,
        evaluation_period_end: draftData.evaluation_period_end,
        timeline: draftData.timeline,
        evaluation_method: draftData.evaluation_method,
        criticality_level: draftData.criticality_level,
        geographical_scope: draftData.geographical_scope,
        compliance_requirements: draftData.compliance_requirements,
        allow_late_submissions: draftData.allow_late_submissions,
        auto_approve: draftData.auto_approve,
        evaluation_criteria_count: draftData.evaluation_criteria?.length || 0
      })
      
      // Helper function to format date for input[type="date"]
      const formatDateForInput = (dateString) => {
        if (!dateString) return ''
        try {
          // Handle ISO format (2024-01-15T00:00:00Z) -> 2024-01-15
          return dateString.split('T')[0]
        } catch (e) {
          return dateString
        }
      }
      
      // Helper function to format datetime for input[type="datetime-local"]
      const formatDateTimeForInput = (dateString) => {
        if (!dateString) return ''
        try {
          // Handle ISO format (2024-01-15T14:30:00Z) -> 2024-01-15T14:30
          const date = new Date(dateString)
          const year = date.getFullYear()
          const month = String(date.getMonth() + 1).padStart(2, '0')
          const day = String(date.getDate()).padStart(2, '0')
          const hours = String(date.getHours()).padStart(2, '0')
          const minutes = String(date.getMinutes()).padStart(2, '0')
          return `${year}-${month}-${day}T${hours}:${minutes}`
        } catch (e) {
          console.error('Error formatting datetime:', e)
          return ''
        }
      }
      
      // Helper to convert number to string for input fields
      const toStringValue = (value) => {
        if (value === null || value === undefined) return ''
        return String(value)
      }
      
      // Load the draft data into the form
      formData.value = {
        rfpNumber: toStringValue(draftData.rfp_number || draftData.rfpNumber),
        title: toStringValue(draftData.rfp_title || draftData.title),
        description: toStringValue(draftData.description),
        type: toStringValue(draftData.rfp_type || draftData.type),
        category: toStringValue(draftData.category),
        estimatedValue: toStringValue(draftData.estimated_value || draftData.estimatedValue),
        currency: draftData.currency || 'USD',
        budgetMin: toStringValue(draftData.budget_range_min || draftData.budgetMin),
        budgetMax: toStringValue(draftData.budget_range_max || draftData.budgetMax),
        issueDate: formatDateForInput(draftData.issue_date || draftData.issueDate),
        deadline: formatDateTimeForInput(draftData.submission_deadline || draftData.deadline),
        evaluationPeriodEnd: formatDateForInput(draftData.evaluation_period_end || draftData.evaluationPeriodEnd),
        timeline: toStringValue(draftData.timeline),
        evaluationMethod: draftData.evaluation_method || draftData.evaluationMethod || 'weighted_scoring',
        criticalityLevel: draftData.criticality_level || draftData.criticalityLevel || 'medium',
        geographicalScope: toStringValue(draftData.geographical_scope || draftData.geographicalScope),
        complianceRequirements: Array.isArray(draftData.compliance_requirements) 
          ? draftData.compliance_requirements.join(', ') 
          : toStringValue(draftData.compliance_requirements || draftData.complianceRequirements),
        allowLateSubmissions: Boolean(draftData.allow_late_submissions || draftData.allowLateSubmissions),
        autoApprove: Boolean(draftData.auto_approve || draftData.autoApprove),
        customFields: draftData.custom_fields || draftData.customFields || {}
      }
      
      // Fetch custom fields schema if type is set
      if (formData.value.type) {
        await fetchCustomFields(formData.value.type)
        // If custom fields were loaded from draft, merge them properly
        // Note: fetchCustomFields already handles mapping old field names to new ones
        if (draftData.custom_fields || draftData.customFields) {
          const loadedFields = draftData.custom_fields || draftData.customFields
          // Separate RFP type fields from categorized fields
          const rfpTypeFields: Record<string, any> = {}
          const categorizedFields: Record<string, Record<string, any>> = {}
          
          Object.keys(loadedFields).forEach(key => {
            // Check if this is a category key (matches one of our categories)
            const isCategory = customFieldCategories.value.some(cat => cat.id === key)
            if (isCategory && typeof loadedFields[key] === 'object' && !Array.isArray(loadedFields[key])) {
              // This is a categorized field group
              categorizedFields[key] = loadedFields[key]
            } else {
              // This is a regular RFP type field
              rfpTypeFields[key] = loadedFields[key]
            }
          })
          
          // Map old field names to new ones based on schema for RFP type fields
          const mappedFields = mapOldFieldNamesToNew(rfpTypeFields, customFieldsSchema.value)
          // Merge each field individually to maintain reactivity
          Object.keys(mappedFields).forEach(key => {
            if (formData.value.customFields && key in formData.value.customFields) {
              formData.value.customFields[key] = mappedFields[key]
            }
          })
          
          // Load categorized fields
          loadCategorizedCustomFields(categorizedFields)
        }
      } else if (draftData.custom_fields || draftData.customFields) {
        // Even if no type, try to load categorized fields
        const loadedFields = draftData.custom_fields || draftData.customFields
        const categorizedFields: Record<string, Record<string, any>> = {}
        
        Object.keys(loadedFields).forEach(key => {
          const isCategory = customFieldCategories.value.some(cat => cat.id === key)
          if (isCategory && typeof loadedFields[key] === 'object' && !Array.isArray(loadedFields[key])) {
            categorizedFields[key] = loadedFields[key]
          }
        })
        
        if (Object.keys(categorizedFields).length > 0) {
          loadCategorizedCustomFields(categorizedFields)
        }
      }
      
      console.log('✅ Form data populated:', formData.value)
      console.log('📊 Field population status:', {
        rfpNumber: formData.value.rfpNumber ? '✅ Populated' : '❌ Empty',
        title: formData.value.title ? '✅ Populated' : '❌ Empty',
        description: formData.value.description ? '✅ Populated' : '❌ Empty',
        type: formData.value.type ? '✅ Populated' : '❌ Empty',
        category: formData.value.category ? '✅ Populated' : '❌ Empty',
        estimatedValue: formData.value.estimatedValue ? '✅ Populated' : '❌ Empty',
        currency: formData.value.currency ? '✅ Populated' : '❌ Empty',
        budgetMin: formData.value.budgetMin ? '✅ Populated' : '❌ Empty',
        budgetMax: formData.value.budgetMax ? '✅ Populated' : '❌ Empty',
        issueDate: formData.value.issueDate ? '✅ Populated' : '❌ Empty',
        deadline: formData.value.deadline ? '✅ Populated' : '❌ Empty',
        evaluationPeriodEnd: formData.value.evaluationPeriodEnd ? '✅ Populated' : '❌ Empty',
        timeline: formData.value.timeline ? '✅ Populated' : '❌ Empty',
        evaluationMethod: formData.value.evaluationMethod ? '✅ Populated' : '❌ Empty',
        criticalityLevel: formData.value.criticalityLevel ? '✅ Populated' : '❌ Empty',
        geographicalScope: formData.value.geographicalScope ? '✅ Populated (or intentionally empty)' : '⚠️ Empty',
        complianceRequirements: formData.value.complianceRequirements ? '✅ Populated' : '⚠️ Empty',
        allowLateSubmissions: formData.value.allowLateSubmissions !== undefined ? '✅ Set' : '❌ Not set',
        autoApprove: formData.value.autoApprove !== undefined ? '✅ Set' : '❌ Not set'
      })
      
      // Load evaluation criteria if available
      if (draftData.evaluation_criteria && Array.isArray(draftData.evaluation_criteria)) {
        criteria.value = draftData.evaluation_criteria.map((criterion, index) => ({
          id: criterion.id || `${Date.now()}-${index}`,
          name: criterion.criteria_name || criterion.name || '',
          description: criterion.criteria_description || criterion.description || '',
          weight: Number(criterion.weight_percentage || criterion.weight) || 0,
          isVeto: Boolean(criterion.veto_enabled || criterion.isVeto || criterion.is_mandatory)
        }))
        console.log('✅ Loaded evaluation criteria:', criteria.value.length, 'criteria')
      } else {
        console.warn('⚠️ No evaluation criteria found in draft data')
      }
      
      // Load uploaded documents if available
      console.log('📎 Checking for documents in draft...')
      if (draftData.documents && Array.isArray(draftData.documents) && draftData.documents.length > 0) {
        console.log('📎 Found documents array:', draftData.documents)
        
        // Fetch document details for each document ID
        const documentPromises = draftData.documents.map(async (docId) => {
          try {
            const docResponse = await axios.get(`${API_BASE_URL}/s3-files/${docId}/`, {
              headers: getAuthHeaders()
            })
            console.log(`✅ Fetched document ${docId}:`, docResponse.data)
            
            // Handle nested response structure: {success: true, s3_file: {...}}
            const fileData = docResponse.data.s3_file || docResponse.data
            console.log(`📋 File data for ${docId}:`, fileData)
            
            return {
              name: fileData.document_name || fileData.file_name || `Document ${docId}`,
              fileName: fileData.file_name || 'unknown',
              fileSize: fileData.file_size || 0,
              fileType: fileData.file_type || 'pdf',
              url: fileData.url, // Store S3 URL for direct download
              uploaded: true,
              s3Id: docId,
              file: null, // No file object needed for already uploaded docs
              isMerged: fileData.metadata?.is_merged || false
            }
          } catch (docError) {
            console.error(`❌ Error fetching document ${docId}:`, docError)
            return null
          }
        })
        
        // Wait for all document fetches to complete
        const documents = await Promise.all(documentPromises)
        uploadedDocuments.value = documents.filter(doc => doc !== null)
        
        console.log(`✅ Loaded ${uploadedDocuments.value.length} uploaded documents`)
      } else {
        console.log('📎 No documents found in draft')
        uploadedDocuments.value = []
      }
      
      success('Draft Loaded', 'Draft has been loaded for editing.')
      
      // Clear the edit draft flag
      localStorage.removeItem('edit_rfp_draft')
    } catch (error) {
      console.error('Error loading draft for editing:', error)
      error('Load Error', 'Failed to load draft. Starting fresh.')
      localStorage.removeItem('edit_rfp_draft')
    }
  } else {
    // Only check for existing local drafts if NOT in change request mode
    if (!changeRequestMode) {
      checkForExistingDraft()
    }
  }
  
  // Set up auto-save interval
  autoSaveInterval = setInterval(() => {
    autoSaveDraft()
  }, 30000)
})

// Function to check for existing drafts
const checkForExistingDraft = () => {
  try {
    const existingDraft = localStorage.getItem('rfp_draft_current')
    if (existingDraft) {
      const draftData = JSON.parse(existingDraft)
      
      // Check if there's meaningful content in the draft
      const hasContent = draftData.title?.trim() || 
                        draftData.description?.trim() || 
                        draftData.rfpNumber?.trim() ||
                        (draftData.criteria && draftData.criteria.length > 0)
      
      if (hasContent) {
        // Check if current form is empty (to avoid overwriting current work)
        const currentFormEmpty = !formData.value.title?.trim() && 
                                !formData.value.description?.trim() && 
                                !formData.value.rfpNumber?.trim() &&
                                criteria.value.length === 5 && // Default criteria count
                                criteria.value.every(c => c.weight === 0 || c.name === 'Technical Capability' || c.name === 'Cost Effectiveness' || c.name === 'Experience & References' || c.name === 'Implementation Timeline' || c.name === 'Support & Maintenance')
        
        if (currentFormEmpty) {
          console.log('Found existing draft with content, showing recovery dialog')
          showDraftRecovery.value = true
        }
      }
    }
  } catch (error) {
    console.error('Error checking for existing draft:', error)
    // If there's an error parsing the draft, remove it
    localStorage.removeItem('rfp_draft_current')
  }
}

// Function to auto-save draft
const autoSaveDraft = () => {
  try {
    // Check if there's meaningful content to save
    const hasContent = formData.value.title?.trim() || 
                      formData.value.description?.trim() || 
                      formData.value.rfpNumber?.trim() ||
                      criteria.value.some(c => c.name?.trim() && c.weight > 0)
    
    if (hasContent) {
      isAutoSaving.value = true
      const draftData = {
        ...formData.value,
        criteria: criteria.value,
        hiddenFields: { ...hiddenFields.value },
        hiddenCustomFields: Array.from(hiddenCustomFields.value),
        hiddenTabs: Array.from(hiddenTabs.value),
        lastSaved: new Date().toISOString(),
        version: '1.0' // Add version tracking
      }
      
      localStorage.setItem('rfp_draft_current', JSON.stringify(draftData))
      lastSaved.value = new Date()
      
      console.log('Auto-saved draft:', draftData)
      
      setTimeout(() => isAutoSaving.value = false, 1000)
    }
  } catch (error) {
    console.error('Error auto-saving draft:', error)
    isAutoSaving.value = false
  }
}

onUnmounted(() => {
  if (autoSaveInterval) {
    clearInterval(autoSaveInterval)
  }
})

const formatTime = (date: Date) => {
  return date.toLocaleTimeString()
}

// Document handling methods
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    newDocument.value.file = file
    newDocument.value.fileName = file.name
    newDocument.value.fileSize = file.size
  }
}

const addDocument = () => {
  if (!newDocument.value.name || !newDocument.value.file) {
    error('Validation Error', 'Please provide both document name and select a file.')
    return
  }

  // Check file size (max 10MB)
  if (newDocument.value.fileSize > 10 * 1024 * 1024) {
    error('File Size Error', 'File size must be less than 10MB.')
    return
  }

  // Add to uploaded documents list
  uploadedDocuments.value.push({
    name: newDocument.value.name,
    file: newDocument.value.file,
    fileName: newDocument.value.fileName,
    fileSize: newDocument.value.fileSize,
    uploaded: false,
    s3Id: null
  })

  // Clear form
  clearDocumentForm()
  
  success('Document Added', 'Document added to upload queue.')
}

const removeDocument = async (index) => {
  const doc = uploadedDocuments.value[index]
  
  if (doc.uploaded) {
    // For already uploaded documents, confirm deletion
    PopupService.confirm(
      `Are you sure you want to delete "${doc.name}"? This will remove it from the RFP.`,
      'Confirm Deletion',
      async () => {
        try {
          // Remove from RFP's documents array
          const rfpId = localStorage.getItem('current_rfp_id')
          if (rfpId) {
            const rfpResponse = await axios.get(`${API_BASE_URL}/rfps/${rfpId}/`, {
              headers: getAuthHeaders()
            })
            const currentDocuments = rfpResponse.data.documents || []
            const updatedDocuments = currentDocuments.filter(id => id !== doc.s3Id)
            
            await axios.post(`${API_BASE_URL}/rfps/${rfpId}/update-documents/`, {
              documents: updatedDocuments
            }, {
              headers: getAuthHeaders()
            })
            
            console.log(`✅ Removed document ${doc.s3Id} from RFP`)
          }
          
          // Remove from UI
          uploadedDocuments.value.splice(index, 1)
          success('Document Deleted', 'Document has been removed from the RFP.')
        } catch (error) {
          console.error('Error deleting document:', error)
          error('Delete Error', 'Failed to delete document. Please try again.')
        }
      },
      undefined
    )
  } else {
    // For pending documents, just remove from queue
    uploadedDocuments.value.splice(index, 1)
    success('Document Removed', 'Document removed from upload queue.')
  }
}

// Download document from S3
const downloadDocument = async (doc) => {
  try {
    console.log('📥 Downloading document:', doc.s3Id, doc.fileName)
    
    // Fetch document details to get the S3 URL
    const docDetails = await axios.get(`${API_BASE_URL}/s3-files/${doc.s3Id}/`, {
      headers: getAuthHeaders()
    })
    console.log('📋 Document details fetched:', docDetails.data)
    
    // Handle nested response structure: {success: true, s3_file: {...}}
    const fileData = docDetails.data.s3_file || docDetails.data
    console.log('📋 File data extracted:', fileData)
    
    // Check if we have a direct S3 URL (presigned URL)
    if (fileData.url) {
      console.log('✅ Using direct S3 URL for download:', fileData.url)
      
      // Download directly from S3 URL
      const response = await axios.get(fileData.url, {
        responseType: 'blob'
      })
      
      console.log('✅ Download response received, file size:', response.data.size, 'bytes')
      
      // Get file extension from URL or file_type
      const fileExtension = fileData.file_type || 'pdf'
      const downloadFileName = `${fileData.file_name || doc.fileName}.${fileExtension}`
      
      // Create download link
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = downloadFileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      success('Download Started', `Downloading ${downloadFileName}`)
    } else {
      // Fallback: Use backend download endpoint if no direct URL
      console.warn('⚠️ No direct S3 URL available, using backend endpoint')
      
      const s3Key = fileData.stored_s3_key || fileData.s3_key
      const fileName = fileData.file_name || doc.fileName
      
      console.log('📥 Requesting download via backend:', { s3_key: s3Key, file_name: fileName })
      
      const response = await axios.post(`${API_BASE_URL}/s3/download/`, {
        s3_key: s3Key,
        file_name: fileName,
        user_id: '1'
      }, {
        headers: getAuthHeaders(),
        responseType: 'blob'
      })
      
      console.log('✅ Download response received, file size:', response.data.size)
      
      const blob = new Blob([response.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      success('Download Started', `Downloading ${fileName}`)
    }
  } catch (err) {
    console.error('❌ Error downloading document:', err)
    if (err.response) {
      console.error('❌ Error response:', err.response.data)
      console.error('❌ Error status:', err.response.status)
    }
    error('Download Error', 'Failed to download document. Please try again.')
  }
}

const clearDocumentForm = () => {
  newDocument.value = {
    name: '',
    file: null,
    fileName: '',
    fileSize: 0
  }
  // Clear file input
  const fileInput = document.getElementById('documentFile') as HTMLInputElement
  if (fileInput) {
    fileInput.value = ''
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Save a single document immediately to S3 and update RFP documents
const saveSingleDocument = async (index: number) => {
  const rfpId = localStorage.getItem('current_rfp_id')
  if (!rfpId) {
    error('Error', 'Please save the RFP draft first to get an RFP ID.')
    return
  }

  const doc = uploadedDocuments.value[index]
  if (!doc || doc.uploaded) return

  try {
    perDocUploading.value[index] = true
    console.log(`📤 Saving single document: ${doc.name}`)

    // Create FormData for file upload
    const uploadFormData = new FormData()
    uploadFormData.append('file', doc.file)
    uploadFormData.append('document_name', doc.name)
    uploadFormData.append('rfp_id', rfpId)
    uploadFormData.append('user_id', '1') // Mock user ID for development

    console.log(`📋 FormData prepared for: ${doc.name}`)

    // Upload to S3 via backend API
    const authHeaders = getAuthHeaders()
    delete authHeaders['Content-Type']  // Remove any Content-Type to let axios set it for FormData
    const uploadResponse = await axios.post(`${API_BASE_URL}/upload-document/`, uploadFormData, {
      headers: authHeaders,
      timeout: 60000 // 60 second timeout for large files
    })

    console.log(`📊 Upload response for ${doc.name}:`, uploadResponse.data)

    if (uploadResponse.data.success) {
      // Mark document as uploaded
      uploadedDocuments.value[index].uploaded = true
      uploadedDocuments.value[index].s3Id = uploadResponse.data.document_id
      
      console.log(`✅ Document uploaded successfully: ${doc.name} (ID: ${uploadResponse.data.document_id})`)

      // Get current RFP documents and add the new one
      try {
        const rfpResponse = await axios.get(`${API_BASE_URL}/rfps/${rfpId}`, {
          headers: getAuthHeaders()
        })
        const currentDocuments = rfpResponse.data.documents || []
        
        // Add new document ID if not already present
        if (!currentDocuments.includes(uploadResponse.data.document_id)) {
          const updatedDocuments = [...currentDocuments, uploadResponse.data.document_id]
          
          // Update RFP with new document list
          await axios.post(`${API_BASE_URL}/rfps/${rfpId}/update-documents/`, {
            documents: updatedDocuments
          }, {
            headers: getAuthHeaders()
          })
          
          console.log(`✅ RFP updated with new document ID: ${uploadResponse.data.document_id}`)
        }
      } catch (updateError) {
        console.error('❌ Error updating RFP documents:', updateError)
        // Don't fail the entire operation if RFP update fails
      }

      success('Document Saved', `Document "${doc.name}" has been uploaded and saved successfully.`)
    } else {
      console.error(`❌ Failed to upload document: ${doc.name}`, uploadResponse.data.error)
      error('Upload Error', `Failed to upload document: ${doc.name} - ${uploadResponse.data.error}`)
    }
  } catch (uploadError) {
    console.error(`❌ Upload error for document: ${doc.name}`, uploadError)
    if (uploadError.response) {
      console.error(`❌ Response data:`, uploadError.response.data)
      console.error(`❌ Response status:`, uploadError.response.status)
    }
    error('Upload Error', `Failed to upload document: ${doc.name} - ${uploadError.message}`)
  } finally {
    perDocUploading.value[index] = false
  }
}

// Drag and drop handlers for reordering documents
const handleDragStart = (index: number, event: DragEvent) => {
  if (isMergingDocuments.value) {
    event.preventDefault()
    return
  }
  draggedIndex.value = index
  event.dataTransfer!.effectAllowed = 'move'
  event.dataTransfer!.setData('text/html', String(index))
}

const handleDragOver = (index: number, event: DragEvent) => {
  event.preventDefault()
  event.dataTransfer!.dropEffect = 'move'
  if (draggedIndex.value !== null && draggedIndex.value !== index) {
    dragOverIndex.value = index
  }
}

const handleDragLeave = (index: number, event: DragEvent) => {
  event.preventDefault()
  dragOverIndex.value = null
}

const handleDrop = (index: number, event: DragEvent) => {
  event.preventDefault()
  
  if (draggedIndex.value === null || draggedIndex.value === index) {
    draggedIndex.value = null
    dragOverIndex.value = null
    return
  }
  
  // Reorder documents
  const draggedDoc = uploadedDocuments.value[draggedIndex.value]
  
  // Remove dragged item from its current position
  uploadedDocuments.value.splice(draggedIndex.value, 1)
  
  // Insert at new position
  uploadedDocuments.value.splice(index, 0, draggedDoc)
  
  // Reset drag state
  draggedIndex.value = null
  dragOverIndex.value = null
  
  success('Document Moved', 'Document order updated.')
}

// Remove merged document
const removeMergedDocument = () => {
  mergedDocument.value = null
  success('Merged Document Removed', 'Merged document has been removed from view.')
}

// Merge documents function - works with or without RFP ID
const mergeDocuments = async (documentIds = null) => {
  // If documentIds not provided, get from uploadedDocuments in current order
  if (!documentIds) {
    const savedDocs = uploadedDocuments.value.filter(doc => doc.uploaded && doc.s3Id)
    if (savedDocs.length < 2) {
      // Try to merge from files if not uploaded yet
      const pendingDocs = uploadedDocuments.value.filter(doc => !doc.uploaded && doc.file)
      if (pendingDocs.length >= 2) {
        return await mergeDocumentsFromFiles(pendingDocs)
      } else {
        error('Error', 'At least 2 documents are required for merging.')
        return null
      }
    }
    documentIds = savedDocs.map(doc => doc.s3Id).filter(id => id !== null && id !== undefined)
  }

  const rfpId = localStorage.getItem('current_rfp_id') // Optional - can be null
  
  if (!documentIds || !Array.isArray(documentIds) || documentIds.length < 2) {
    console.error('❌ Invalid document IDs for merging:', documentIds)
    error('Error', 'At least 2 documents are required for merging.')
    return null
  }

  // Ensure all IDs are numbers
  const numericIds = documentIds.map(id => Number(id)).filter(id => !isNaN(id) && id > 0)
  if (numericIds.length < 2) {
    console.error('❌ Invalid numeric document IDs:', numericIds)
    error('Error', 'Invalid document IDs. Please ensure all documents are saved.')
    return null
  }

  try {
    isMergingDocuments.value = true
    console.log(`🔄 Merging ${numericIds.length} documents in order${rfpId ? ` for RFP ${rfpId}` : ' (standalone)'}:`, numericIds)

    // Use standalone merge endpoint (works without RFP ID)
    const mergeResponse = await axios.post(`${API_BASE_URL}/merge-documents/`, {
      document_ids: numericIds,
      document_order: numericIds, // Use the current order
      rfp_id: rfpId || null, // Optional
      user_id: '1'
    }, {
      headers: getAuthHeaders(),
      timeout: 120000 // 2 minute timeout for large merges
    })

    console.log('📊 Merge response:', mergeResponse.data)

    if (mergeResponse.data && mergeResponse.data.success) {
      console.log('✅ Documents merged successfully:', mergeResponse.data)
      
      // Fetch full document details from API
      try {
        const docResponse = await axios.get(`${API_BASE_URL}/s3-files/${mergeResponse.data.merged_document_id}/`, {
          headers: getAuthHeaders()
        })
        
        const fileData = docResponse.data.s3_file || docResponse.data
        console.log('✅ Fetched merged document details:', fileData)
        
        // Create merged document object and add to uploadedDocuments array
        const mergedDoc = {
          name: fileData.document_name || fileData.file_name || `Merged Document - ${formData.value.title || 'RFP'}`,
          fileName: fileData.file_name || 'merged_document.pdf',
          fileSize: fileData.file_size || 0,
          fileType: fileData.file_type || 'pdf',
          url: fileData.url || mergeResponse.data.merged_document_url,
          uploaded: true,
          s3Id: mergeResponse.data.merged_document_id,
          file: null,
          isMerged: true
        }
        
        // Add merged document to the uploadedDocuments array
        uploadedDocuments.value.push(mergedDoc)
        console.log('✅ Merged document added to document list:', mergedDoc)
        
        // Clear the separate merged document display
        mergedDocument.value = null
        
      } catch (fetchError) {
        console.error('❌ Error fetching merged document details:', fetchError)
        // Fallback: create document object from merge response
        const mergedDoc = {
          name: mergeResponse.data.merged_document_name || `Merged Document - ${formData.value.title || 'RFP'}`,
          fileName: mergeResponse.data.merged_document_name || 'merged_document.pdf',
          fileSize: 0,
          fileType: 'pdf',
          url: mergeResponse.data.merged_document_url,
          uploaded: true,
          s3Id: mergeResponse.data.merged_document_id,
          file: null,
          isMerged: true
        }
        uploadedDocuments.value.push(mergedDoc)
        mergedDocument.value = null
      }
      
      // Add merged document to RFP's documents list (if RFP exists)
      if (rfpId) {
        try {
          const rfpResponse = await axios.get(`${API_BASE_URL}/rfps/${rfpId}`, {
            headers: getAuthHeaders()
          })
          const currentDocuments = rfpResponse.data.documents || []
          
          // Add merged document ID if not already present
          if (!currentDocuments.includes(mergeResponse.data.merged_document_id)) {
            const updatedDocuments = [...currentDocuments, mergeResponse.data.merged_document_id]
            
            await axios.post(`${API_BASE_URL}/rfps/${rfpId}/update-documents/`, {
              documents: updatedDocuments
            }, {
              headers: getAuthHeaders()
            })
            
            console.log('✅ Merged document added to RFP documents list')
          }
        } catch (updateError) {
          console.error('❌ Error adding merged document to RFP:', updateError)
          // Don't fail the merge if this update fails
        }
      }
      
      success('Documents Merged', `Successfully merged ${mergeResponse.data.document_count || numericIds.length} documents.`)
      return mergeResponse.data.merged_document_id
    } else {
      const errorMsg = mergeResponse.data?.error || 'Failed to merge documents.'
      console.error('❌ Merge failed:', errorMsg)
      error('Merge Error', errorMsg)
      return null
    }
  } catch (mergeError) {
    console.error('❌ Error merging documents:', mergeError)
    if (mergeError.response) {
      console.error('❌ Response status:', mergeError.response.status)
      console.error('❌ Response data:', mergeError.response.data)
      const errorMsg = mergeError.response.data?.error || mergeError.response.data?.message || 'Failed to merge documents.'
      error('Merge Error', errorMsg)
    } else if (mergeError.request) {
      console.error('❌ No response received:', mergeError.request)
      error('Merge Error', 'Network error. Please check your connection and try again.')
    } else {
      console.error('❌ Error message:', mergeError.message)
      error('Merge Error', `Failed to merge documents: ${mergeError.message}`)
    }
    return null
  } finally {
    isMergingDocuments.value = false
  }
}

// Merge documents directly from files (before uploading to S3)
const mergeDocumentsFromFiles = async (docs) => {
  if (!docs || docs.length < 2) {
    error('Error', 'At least 2 documents are required for merging.')
    return null
  }

  const rfpId = localStorage.getItem('current_rfp_id') // Optional

  try {
    isMergingDocuments.value = true
    console.log(`🔄 Merging ${docs.length} files directly (before upload)`)

    // Create FormData with files in order
    const mergeFormData = new FormData()
    let fileCount = 0
    docs.forEach((doc, idx) => {
      if (doc.file) {
        console.log(`📎 Appending file ${idx + 1}:`, doc.file.name, `(${doc.file.size} bytes)`)
        mergeFormData.append('files', doc.file)
        fileCount++
      }
    })
    
    console.log(`📦 Total files appended: ${fileCount}`)
    
    if (rfpId) {
      mergeFormData.append('rfp_id', rfpId)
      console.log(`🔖 RFP ID: ${rfpId}`)
    }
    mergeFormData.append('user_id', '1')
    
    // Log FormData contents
    console.log('📋 FormData contents:')
    for (let pair of mergeFormData.entries()) {
      console.log(`  ${pair[0]}:`, pair[1])
    }

    // Get auth headers but remove Content-Type to let axios handle it for FormData
    const authHeaders = getAuthHeaders()
    delete authHeaders['Content-Type']  // Remove any Content-Type to let axios set it for FormData
    
    const mergeResponse = await axios.post(`${API_BASE_URL}/merge-documents/`, mergeFormData, {
      headers: authHeaders,
      timeout: 120000
    })

    console.log('📊 Merge response:', mergeResponse.data)

    if (mergeResponse.data && mergeResponse.data.success) {
      console.log('✅ Documents merged successfully from files:', mergeResponse.data)
      
      // Fetch full document details from API
      try {
        const docResponse = await axios.get(`${API_BASE_URL}/s3-files/${mergeResponse.data.merged_document_id}/`, {
          headers: getAuthHeaders()
        })
        
        const fileData = docResponse.data.s3_file || docResponse.data
        console.log('✅ Fetched merged document details:', fileData)
        
        // Create merged document object and add to uploadedDocuments array
        const mergedDoc = {
          name: fileData.document_name || fileData.file_name || `Merged Document - ${formData.value.title || 'RFP'}`,
          fileName: fileData.file_name || 'merged_document.pdf',
          fileSize: fileData.file_size || 0,
          fileType: fileData.file_type || 'pdf',
          url: fileData.url || mergeResponse.data.merged_document_url,
          uploaded: true,
          s3Id: mergeResponse.data.merged_document_id,
          file: null,
          isMerged: true
        }
        
        // Add merged document to the uploadedDocuments array
        uploadedDocuments.value.push(mergedDoc)
        console.log('✅ Merged document added to document list:', mergedDoc)
        
        // Clear the separate merged document display
        mergedDocument.value = null
        
      } catch (fetchError) {
        console.error('❌ Error fetching merged document details:', fetchError)
        // Fallback: create document object from merge response
        const mergedDoc = {
          name: mergeResponse.data.merged_document_name || `Merged Document - ${formData.value.title || 'RFP'}`,
          fileName: mergeResponse.data.merged_document_name || 'merged_document.pdf',
          fileSize: 0,
          fileType: 'pdf',
          url: mergeResponse.data.merged_document_url,
          uploaded: true,
          s3Id: mergeResponse.data.merged_document_id,
          file: null,
          isMerged: true
        }
        uploadedDocuments.value.push(mergedDoc)
        mergedDocument.value = null
      }
      
      success('Documents Merged', `Successfully merged ${mergeResponse.data.document_count || docs.length} documents.`)
      return mergeResponse.data.merged_document_id
    } else {
      const errorMsg = mergeResponse.data?.error || 'Failed to merge documents.'
      console.error('❌ Merge failed:', errorMsg)
      error('Merge Error', errorMsg)
      return null
    }
  } catch (mergeError) {
    console.error('❌ Error merging documents from files:', mergeError)
    if (mergeError.response) {
      console.error('❌ Response status:', mergeError.response.status)
      console.error('❌ Response data:', mergeError.response.data)
      const errorMsg = mergeError.response.data?.error || mergeError.response.data?.message || 'Failed to merge documents.'
      error('Merge Error', errorMsg)
    } else {
      error('Merge Error', `Failed to merge documents: ${mergeError.message}`)
    }
    return null
  } finally {
    isMergingDocuments.value = false
  }
}

// Save all pending documents
const saveAllDocuments = async () => {
  console.log('🚀 saveAllDocuments called')
  console.log('📋 Current uploadedDocuments:', uploadedDocuments.value.map((d, idx) => ({
    index: idx,
    name: d.name,
    uploaded: d.uploaded,
    s3Id: d.s3Id,
    hasFile: !!d.file
  })))
  
  const rfpId = localStorage.getItem('current_rfp_id')
  const hasRfpId = rfpId && rfpId !== 'null' && rfpId !== ''
  
  if (!hasRfpId) {
    console.log('ℹ️ No RFP ID found - will merge documents without RFP association')
    // Allow merging without RFP ID - merge documents directly from files
    const allDocs = uploadedDocuments.value
    if (allDocs.length < 2) {
      error('Error', 'At least 2 documents are required for merging.')
      return
    }
    
    // Check if we have files to merge (use documents in current order)
    const docsWithFiles = allDocs.filter(doc => doc.file)
    if (docsWithFiles.length >= 2) {
      console.log('🔄 Merging documents directly from files (no RFP ID needed)')
      console.log('📋 Documents to merge in order:', docsWithFiles.map((d, idx) => ({
        index: idx,
        name: d.name,
        fileName: d.fileName
      })))
      await mergeDocumentsFromFiles(docsWithFiles)
      return
    } else {
      // Check if documents are already uploaded
      const savedDocs = allDocs.filter(doc => doc.uploaded && doc.s3Id)
      if (savedDocs.length >= 2) {
        console.log('🔄 Documents already uploaded, merging by ID (no RFP ID needed)')
        const orderedDocumentIds = allDocs
          .filter(doc => doc.uploaded && doc.s3Id)
          .map(doc => Number(doc.s3Id))
          .filter(id => id !== null && id !== undefined && !isNaN(id) && id > 0)
        
        if (orderedDocumentIds.length >= 2) {
          await mergeDocuments(orderedDocumentIds)
          return
        }
      }
      
      error('Error', 'Please add at least 2 documents with files to merge.')
      return
    }
  }
  
  console.log('✅ RFP ID found:', rfpId)

  const pendingDocs = uploadedDocuments.value.filter(doc => !doc.uploaded)
  console.log('📊 Pending documents:', pendingDocs.length)
  console.log('📊 Pending docs details:', pendingDocs.map(d => ({ name: d.name, hasFile: !!d.file })))
  
  if (pendingDocs.length === 0) {
    // If all documents are saved, automatically merge them
    const savedDocs = uploadedDocuments.value.filter(doc => doc.uploaded && doc.s3Id)
    console.log('📋 All documents already saved. Checking for merge:', {
      totalDocs: uploadedDocuments.value.length,
      savedDocs: savedDocs.length,
      savedDocDetails: savedDocs.map(d => ({ name: d.name, s3Id: d.s3Id }))
    })
    
    if (savedDocs.length >= 2) {
      // Get document IDs in current order
      const orderedDocumentIds = uploadedDocuments.value
        .filter(doc => doc.uploaded && doc.s3Id)
        .map(doc => Number(doc.s3Id))
        .filter(id => id !== null && id !== undefined && !isNaN(id) && id > 0)
      
      console.log('🔄 All documents saved, auto-merging in order:', orderedDocumentIds)
      if (orderedDocumentIds.length >= 2) {
        try {
          const mergeResult = await mergeDocuments(orderedDocumentIds)
          if (mergeResult) {
            success('Documents Merged', `Successfully merged ${orderedDocumentIds.length} documents.`)
          }
        } catch (mergeErr) {
          console.error('❌ Merge error:', mergeErr)
          error('Merge Error', 'Failed to merge documents. Please try again.')
        }
      } else {
        console.warn('⚠️ Not enough valid document IDs for merging')
        success('All Saved', 'All documents are already saved.')
      }
    } else {
      success('All Saved', savedDocs.length === 0 ? 'No documents to merge.' : 'At least 2 documents are required for merging.')
    }
    return
  }

  try {
    isUploadingDocuments.value = true
    console.log(`📤 Saving ${pendingDocs.length} pending documents`)

    // Initialize progress
    uploadProgress.value = {
      current: 0,
      total: pendingDocs.length,
      currentDocument: ''
    }

    const documentIds = []
    const pendingIndices = uploadedDocuments.value
      .map((doc, index) => doc.uploaded ? -1 : index)
      .filter(index => index !== -1)

    for (let i = 0; i < pendingIndices.length; i++) {
      const index = pendingIndices[i]
      const doc = uploadedDocuments.value[index]
      
      console.log(`📤 Saving document ${i + 1}/${pendingIndices.length}: ${doc.name}`)
      
      // Update progress
      uploadProgress.value.current = i + 1
      uploadProgress.value.currentDocument = doc.name

      try {
        // Create FormData for file upload
        const uploadFormData = new FormData()
        uploadFormData.append('file', doc.file)
        uploadFormData.append('document_name', doc.name)
        uploadFormData.append('rfp_id', rfpId)
        uploadFormData.append('user_id', '1')

        // Upload to S3 via backend API
        const authHeaders = getAuthHeaders()
        delete authHeaders['Content-Type']  // Remove any Content-Type to let axios set it for FormData
        const uploadResponse = await axios.post(`${API_BASE_URL}/upload-document/`, uploadFormData, {
          headers: authHeaders,
          timeout: 60000
        })

        console.log(`📤 Upload response for ${doc.name}:`, uploadResponse.data)
        
        if (uploadResponse.data && uploadResponse.data.success) {
          const docId = uploadResponse.data.document_id || uploadResponse.data.id
          if (docId) {
            documentIds.push(docId)
            uploadedDocuments.value[index].uploaded = true
            uploadedDocuments.value[index].s3Id = docId
            console.log(`✅ Document saved: ${doc.name} (ID: ${docId})`)
          } else {
            console.error(`❌ No document ID in response for ${doc.name}:`, uploadResponse.data)
          }
        } else {
          const errorMsg = uploadResponse.data?.error || 'Unknown error'
          console.error(`❌ Failed to save document: ${doc.name}`, errorMsg)
          error('Upload Error', `Failed to save "${doc.name}": ${errorMsg}`)
        }
      } catch (uploadError) {
        console.error(`❌ Error saving document: ${doc.name}`, uploadError)
        if (uploadError.response) {
          console.error('❌ Response status:', uploadError.response.status)
          console.error('❌ Response data:', uploadError.response.data)
          error('Upload Error', `Failed to save "${doc.name}": ${uploadError.response.data?.error || uploadError.message}`)
        } else {
          error('Upload Error', `Failed to save "${doc.name}": ${uploadError.message}`)
        }
      }
    }

    console.log(`📊 Documents saved: ${documentIds.length} out of ${pendingIndices.length} attempted`)
    console.log(`📊 Document IDs collected:`, documentIds)
    
    // Update RFP with all document IDs
    if (documentIds.length > 0) {
      try {
        console.log('🔄 Updating RFP with document IDs...')
        const rfpResponse = await axios.get(`${API_BASE_URL}/rfps/${rfpId}`, {
          headers: getAuthHeaders()
        })
        const currentDocuments = rfpResponse.data.documents || []
        const updatedDocuments = [...new Set([...currentDocuments, ...documentIds])]
        
        await axios.post(`${API_BASE_URL}/rfps/${rfpId}/update-documents/`, {
          documents: updatedDocuments
        }, {
          headers: getAuthHeaders()
        })
        
        console.log(`✅ RFP updated with ${documentIds.length} new document IDs`)
        console.log(`✅ Total documents now: ${updatedDocuments.length}`)
      } catch (updateError) {
        console.error('❌ Error updating RFP documents:', updateError)
        if (updateError.response) {
          console.error('❌ Response status:', updateError.response.status)
          console.error('❌ Response data:', updateError.response.data)
        }
        error('Update Error', 'Documents were uploaded but failed to update RFP. Please try again.')
        // Continue to merge even if RFP update fails
      }
    } else {
      console.warn('⚠️ No documents were successfully saved')
      error('Save Error', 'No documents were saved. Please check the files and try again.')
      return
    }
    
    // After saving all documents, merge them in the current order
    // Wait a bit to ensure all uploads are complete
    console.log('⏳ Waiting 500ms before merging...')
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const allSavedDocs = uploadedDocuments.value.filter(doc => doc.uploaded && doc.s3Id)
    console.log('📋 All saved documents after save:', allSavedDocs.map((d, idx) => ({
      index: idx,
      name: d.name,
      s3Id: d.s3Id,
      uploaded: d.uploaded
    })))
    
    if (allSavedDocs.length >= 2) {
      // Get document IDs in current order (preserve the order from uploadedDocuments array)
      const orderedDocumentIds = uploadedDocuments.value
        .filter(doc => doc.uploaded && doc.s3Id)
        .map(doc => Number(doc.s3Id)) // Ensure IDs are numbers
        .filter(id => id !== null && id !== undefined && !isNaN(id) && id > 0)
      
      console.log('🔄 Auto-merging documents after save in order:', orderedDocumentIds)
      console.log('📊 Document order details:', uploadedDocuments.value.map((d, idx) => ({
        index: idx,
        name: d.name,
        s3Id: d.s3Id,
        uploaded: d.uploaded
      })))
      
      if (orderedDocumentIds.length >= 2) {
        console.log('✅ Starting merge process...')
        try {
          const mergeResult = await mergeDocuments(orderedDocumentIds)
          console.log('📊 Merge result:', mergeResult)
          if (mergeResult) {
            success('Documents Saved & Merged', `Successfully saved ${documentIds.length} document(s) and merged ${orderedDocumentIds.length} documents.`)
          } else {
            console.warn('⚠️ Merge returned null/undefined')
            success('Documents Saved', `Successfully saved ${documentIds.length} document(s). Merge failed - please try again.`)
          }
        } catch (mergeErr) {
          console.error('❌ Merge error caught:', mergeErr)
          console.error('❌ Merge error stack:', mergeErr.stack)
          success('Documents Saved', `Successfully saved ${documentIds.length} document(s). Merge failed - please try again.`)
        }
      } else {
        console.warn('⚠️ Not enough valid document IDs for merging:', orderedDocumentIds)
        success('Documents Saved', `Successfully saved ${documentIds.length} document(s). Need at least 2 valid document IDs to merge.`)
      }
    } else {
      console.log('ℹ️ Not enough documents to merge:', allSavedDocs.length)
      if (documentIds.length > 0) {
        success('Documents Saved', `Successfully saved ${documentIds.length} document(s). Need at least 2 documents to merge.`)
      }
    }

  } catch (error) {
    console.error('Error saving all documents:', error)
    error('Save Error', 'Failed to save some documents. Please try again.')
  } finally {
    isUploadingDocuments.value = false
    // Reset progress
    uploadProgress.value = {
      current: 0,
      total: 0,
      currentDocument: ''
    }
  }
}

// Function to get draft preview for the recovery dialog
const getDraftPreview = () => {
  try {
    const draftString = localStorage.getItem('rfp_draft_current')
    if (draftString) {
      const draftData = JSON.parse(draftString)
      return {
        title: draftData.title || '',
        rfpNumber: draftData.rfpNumber || '',
        lastSaved: draftData.lastSaved || null
      }
    }
  } catch (error) {
    console.error('Error getting draft preview:', error)
  }
  return {
    title: '',
    rfpNumber: '',
    lastSaved: null
  }
}

const addCriterion = () => {
  const newCriterion: EvaluationCriteria = {
    id: Date.now().toString(),
    name: '',
    description: '',
    weight: 0,
    isVeto: false,
  }
  criteria.value.push(newCriterion)
  
  // Normalize weights after adding a new criterion
  nextTick(() => {
    normalizeWeights()
  })
}

const removeCriterion = (id: string) => {
  criteria.value = criteria.value.filter(criterion => criterion.id !== id)
  // Auto-adjust weights after removal
  adjustWeightsAfterRemoval()
}

// Auto-adjust weights when total exceeds 100%
const adjustWeightsProportionally = (changedIndex: number) => {
  const total = totalWeight.value
  console.log(`adjustWeightsProportionally called - Total: ${total}, ChangedIndex: ${changedIndex}`)
  
  if (total <= 100) return // No adjustment needed
  
  const changedCriterion = criteria.value[changedIndex]
  const otherCriteria = criteria.value.filter((_, index) => index !== changedIndex)
  const otherTotal = otherCriteria.reduce((sum, criterion) => sum + criterion.weight, 0)
  
  console.log(`Changed criterion: ${changedCriterion.name} (${changedCriterion.weight}%), Other total: ${otherTotal}%`)
  
  // If the changed criterion alone exceeds 100%, cap it at 100%
  if (changedCriterion.weight > 100) {
    const oldWeight = changedCriterion.weight
    changedCriterion.weight = 100
    // Set all other criteria to 0
    otherCriteria.forEach(criterion => {
      criterion.weight = 0
    })
    showWeightNotification([{criterion: changedCriterion.name, oldWeight, newWeight: 100}])
    return
  }
  
  // Calculate how much needs to be reduced from other criteria
  const excess = total - 100
  const availableToReduce = otherTotal
  
  if (availableToReduce >= excess) {
    // Proportionally reduce other criteria
    const reductionRatio = excess / availableToReduce
    const adjustments: Array<{criterion: string, oldWeight: number, newWeight: number}> = []
    
    otherCriteria.forEach(criterion => {
      const oldWeight = criterion.weight
      const newWeight = Math.max(0, Math.round(criterion.weight * (1 - reductionRatio)))
      criterion.weight = newWeight
      if (oldWeight !== newWeight) {
        adjustments.push({criterion: criterion.name, oldWeight, newWeight})
      }
    })
    
    // Ensure total is exactly 100% by adjusting the last criterion if needed
    const currentTotal = totalWeight.value
    if (currentTotal !== 100 && otherCriteria.length > 0) {
      const lastCriterion = otherCriteria[otherCriteria.length - 1]
      const adjustment = 100 - currentTotal
      const oldWeight = lastCriterion.weight
      lastCriterion.weight = Math.max(0, lastCriterion.weight + adjustment)
      
      if (oldWeight !== lastCriterion.weight) {
        adjustments.push({criterion: lastCriterion.name, oldWeight, newWeight: lastCriterion.weight})
      }
    }
    
    if (adjustments.length > 0) {
      showWeightNotification(adjustments)
    }
  } else {
    // If we can't reduce enough, cap the changed criterion
    const maxAllowedForChanged = 100 - availableToReduce
    const oldWeight = changedCriterion.weight
    changedCriterion.weight = Math.max(0, maxAllowedForChanged)
    
    showWeightNotification([{criterion: changedCriterion.name, oldWeight, newWeight: changedCriterion.weight}])
  }
}

// Adjust weights after removing a criterion
const adjustWeightsAfterRemoval = () => {
  const total = totalWeight.value
  if (total <= 100) return // No adjustment needed
  
  // Proportionally increase remaining criteria to reach 100%
  const increaseRatio = 100 / total
  const adjustments: Array<{criterion: string, oldWeight: number, newWeight: number}> = []
  
  criteria.value.forEach((criterion, index) => {
    const oldWeight = criterion.weight
    let newWeight = Math.round(criterion.weight * increaseRatio)
    
    // For the last criterion, ensure total is exactly 100%
    if (index === criteria.value.length - 1) {
      const currentTotal = criteria.value.slice(0, -1).reduce((sum, c) => sum + c.weight, 0)
      newWeight = 100 - currentTotal
    }
    
    criterion.weight = Math.max(0, newWeight)
    if (oldWeight !== criterion.weight) {
      adjustments.push({criterion: criterion.name, oldWeight, newWeight: criterion.weight})
    }
  })
  
  if (adjustments.length > 0) {
    showWeightNotification(adjustments)
  }
}

// Show weight adjustment notification
const showWeightNotification = (adjustments: Array<{criterion: string, oldWeight: number, newWeight: number}>) => {
  weightAdjustmentHistory.value = adjustments
  showWeightAdjustmentNotification.value = true
  
  // Auto-hide notification after 5 seconds
  setTimeout(() => {
    showWeightAdjustmentNotification.value = false
  }, 5000)
}

// Watch for weight changes and auto-adjust
const handleWeightChange = (index: number, newValue: number) => {
  const oldWeight = criteria.value[index].weight
  criteria.value[index].weight = newValue
  
  console.log(`Weight changed for criterion ${index}: ${oldWeight} -> ${newValue}, Total: ${totalWeight.value}`)
  
  // Use nextTick to ensure reactivity has updated
  nextTick(() => {
    console.log(`After nextTick - Total: ${totalWeight.value}`)
    // Auto-adjust if total exceeds 100%
    if (totalWeight.value > 100) {
      console.log('Triggering weight adjustment...')
      adjustWeightsProportionally(index)
    }
  })
}

// Normalize weights to exactly 100%
const normalizeWeights = () => {
  const total = totalWeight.value
  console.log(`normalizeWeights called - Current total: ${total}%`)
  
  if (total === 0) return // No criteria to normalize
  
  const adjustments: Array<{criterion: string, oldWeight: number, newWeight: number}> = []
  
  if (total !== 100) {
    const ratio = 100 / total
    console.log(`Normalizing with ratio: ${ratio}`)
    
    criteria.value.forEach((criterion, index) => {
      const oldWeight = criterion.weight
      let newWeight = Math.round(criterion.weight * ratio)
      
      // For the last criterion, ensure total is exactly 100%
      if (index === criteria.value.length - 1) {
        const currentTotal = criteria.value.slice(0, -1).reduce((sum, c) => sum + c.weight, 0)
        newWeight = 100 - currentTotal
        console.log(`Last criterion adjustment: ${oldWeight} -> ${newWeight} (current total: ${currentTotal})`)
      }
      
      criterion.weight = Math.max(0, newWeight)
      if (oldWeight !== criterion.weight) {
        adjustments.push({criterion: criterion.name, oldWeight, newWeight: criterion.weight})
        console.log(`Adjusted ${criterion.name}: ${oldWeight}% -> ${criterion.weight}%`)
      }
    })
    
    console.log(`Final total after normalization: ${totalWeight.value}%`)
    
    if (adjustments.length > 0) {
      showWeightNotification(adjustments)
    }
  }
}

// Watch for changes in total weight and ensure it's exactly 100%
watch(totalWeight, (newTotal, oldTotal) => {
  if (newTotal > 100 && oldTotal <= 100) {
    // Find the last modified criterion and adjust
    const lastModifiedIndex = criteria.value.length - 1
    nextTick(() => {
      adjustWeightsProportionally(lastModifiedIndex)
    })
  }
})

const buildVendorPortalPreviewPayload = () => {
  const formatBudget = () => {
    if (formData.value.estimatedValue) {
      const numericValue = Number(formData.value.estimatedValue)
      const formatted = Number.isFinite(numericValue) ? numericValue.toLocaleString() : formData.value.estimatedValue
      return `${formData.value.currency || 'USD'} ${formatted}`
    }
    if (formData.value.budgetMin && formData.value.budgetMax) {
      const min = Number(formData.value.budgetMin)
      const max = Number(formData.value.budgetMax)
      const formattedMin = Number.isFinite(min) ? min.toLocaleString() : formData.value.budgetMin
      const formattedMax = Number.isFinite(max) ? max.toLocaleString() : formData.value.budgetMax
      return `${formData.value.currency || 'USD'} ${formattedMin} - ${formattedMax}`
    }
    return 'TBD'
  }

  const evaluationCriteriaPreview = criteria.value.map((criterion, index) => ({
    id: criterion.id || `preview-${index}`,
    title: criterion.name || `Criterion ${index + 1}`,
    description: criterion.description || '',
    weight: Number(criterion.weight) || 0,
    required: Boolean(criterion.isVeto),
    type: 'text'
  }))

  const timeline = {
    issueDate: formData.value.issueDate,
    deadline: formData.value.deadline,
    evaluationPeriodEnd: formData.value.evaluationPeriodEnd,
    timeline: formData.value.timeline
  }

  return {
    generatedAt: new Date().toISOString(),
    rfpInfo: {
      rfpTitle: formData.value.title,
      rfpNumber: formData.value.rfpNumber,
      deadline: timeline.deadline,
      budget: formatBudget(),
      description: formData.value.description,
      rfpType: formData.value.type,
      category: formData.value.category,
      criticality: formData.value.criticalityLevel
    },
    evaluationCriteria: evaluationCriteriaPreview,
    dynamicResponseFields: cloneJson(customFieldsSchema.value || []),
    categoryCustomFields: cloneJson(categoryCustomFields.value || {}),
    categoryCustomFieldData: cloneJson(categoryCustomFieldData.value || {}),
    hiddenFields: { ...hiddenFields.value },
    hiddenCustomFields: Array.from(hiddenCustomFields.value),
    documents: uploadedDocuments.value.map((doc, index) => ({
      id: doc.s3Id || `preview-doc-${index}`,
      name: doc.name,
      label: doc.name,
      fileName: doc.fileName || doc.file?.name || '',
      fileSize: doc.fileSize || doc.file?.size || 0,
      uploaded: Boolean(doc.uploaded),
      url: doc.url || null,
      content_type: doc.fileType || doc.mimeType || null
    })),
    customFieldsData: cloneJson(formData.value.customFields || {}),
    timeline
  }
}

const openVendorPortalPreview = () => {
  if (!canPreviewVendorPortal.value) {
    showWarning('Complete Required Fields', 'Please fill in RFP number, title, description, and type before previewing.')
    return
  }

  try {
    const payload = buildVendorPortalPreviewPayload()
    vendorPreviewPayload.value = payload
    showVendorPreview.value = true
    localStorage.setItem(VENDOR_PREVIEW_STORAGE_KEY, JSON.stringify(payload))
  } catch (err) {
    console.error('Error generating vendor preview:', err)
    error('Preview Error', 'Unable to open the vendor portal preview. Please try again.')
  }
}

const closeVendorPortalPreview = () => {
  showVendorPreview.value = false
}

const handleSaveDraft = async () => {
  try {
    isSubmitting.value = true
    
    // Check if we're updating an existing draft
    let existingRfpId = localStorage.getItem('current_rfp_id')
    const changeRequestMode = route.query.mode === 'change_request'
    const changeRequestId = route.query.changeRequest || localStorage.getItem('current_change_request_id')
    
    // In change request mode, we MUST be updating (never creating)
    let isUpdate = existingRfpId && existingRfpId !== 'null' && existingRfpId !== ''
    
    // Force update mode if in change request mode
    if (changeRequestMode && !isUpdate) {
      const rfpIdFromQuery = route.query.rfpId
      existingRfpId = (Array.isArray(rfpIdFromQuery) ? rfpIdFromQuery[0] : rfpIdFromQuery) || localStorage.getItem('current_rfp_id')
      isUpdate = !!existingRfpId
      if (existingRfpId) {
        localStorage.setItem('current_rfp_id', existingRfpId)
      }
    }
    
    // If updating, verify the RFP still exists
    if (isUpdate) {
      try {
        console.log(`Verifying RFP ${existingRfpId} exists...`)
        await axios.get(`${API_BASE_URL}/rfps/${existingRfpId}/`, {
          headers: getAuthHeaders()
        })
        console.log(`✅ RFP ${existingRfpId} exists - will update`)
      } catch (verifyError) {
        if (verifyError.response?.status === 404) {
          console.warn(`⚠️ RFP ${existingRfpId} not found - will create new instead`)
          localStorage.removeItem('current_rfp_id')
          existingRfpId = null
          isUpdate = false
        } else {
          throw verifyError
        }
      }
    }
    
    console.log(isUpdate ? `Updating existing draft RFP ID: ${existingRfpId}` : 'Creating new draft RFP')
    
    // Helper to sanitize empty strings to null
    const sanitizeValue = (value) => {
      if (value === '' || value === undefined) return null
      return value
    }
    
    // Prepare base RFP data - ensure all fields match Django backend expectations
    const baseRfpData = {
      rfp_title: formData.value.title,
      description: formData.value.description,
      rfp_type: formData.value.type || 'TECHNOLOGY',
      category: sanitizeValue(formData.value.category),
      estimated_value: formData.value.estimatedValue ? Number(formData.value.estimatedValue) : null,
      currency: formData.value.currency || 'USD',
      budget_range_min: formData.value.budgetMin ? Number(formData.value.budgetMin) : null,
      budget_range_max: formData.value.budgetMax ? Number(formData.value.budgetMax) : null,
      issue_date: formData.value.issueDate ? new Date(formData.value.issueDate).toISOString().split('T')[0] : null,
      submission_deadline: formData.value.deadline ? new Date(formData.value.deadline).toISOString() : null,
      evaluation_period_end: formData.value.evaluationPeriodEnd ? new Date(formData.value.evaluationPeriodEnd).toISOString().split('T')[0] : null,
      evaluation_method: formData.value.evaluationMethod || 'weighted_scoring',
      criticality_level: formData.value.criticalityLevel || 'medium',
      geographical_scope: sanitizeValue(formData.value.geographicalScope),
      compliance_requirements: formData.value.complianceRequirements && formData.value.complianceRequirements.trim() 
        ? [formData.value.complianceRequirements] 
        : null,
      allow_late_submissions: Boolean(formData.value.allowLateSubmissions),
      auto_approve: Boolean(formData.value.autoApprove),
      status: 'DRAFT',
      data_inventory: buildRFPDataInventory(),
      // Include custom fields - merge RFP type fields and categorized fields
      custom_fields: (() => {
        const mergedCustomFields: Record<string, any> = {}
        let hasAnyFields = false
        
        // 1. Add RFP type-specific custom fields (flat structure)
        if (customFieldsSchema.value && customFieldsSchema.value.length > 0 && formData.value.customFields) {
          const schemaFieldNames = new Set(
            customFieldsSchema.value.map(field => String(field.name))
          )
          
          Object.keys(formData.value.customFields).forEach(key => {
            // Only include if field is in schema
            if (schemaFieldNames.has(key)) {
              const value = formData.value.customFields[key]
              // Only include if value is not empty/null/undefined
              if (value !== null && value !== undefined && value !== '') {
                // For strings, also check if trimmed value is not empty
                if (typeof value === 'string' && value.trim() !== '') {
                  mergedCustomFields[key] = value.trim()
                  hasAnyFields = true
                } else if (typeof value !== 'string') {
                  // For non-string values (numbers, booleans, etc.), include them
                  mergedCustomFields[key] = value
                  hasAnyFields = true
                }
              }
            }
          })
        }
        
        // 2. Add categorized custom fields (nested structure by category)
        const categorizedFields: Record<string, Record<string, any>> = {}
        customFieldCategories.value.forEach(category => {
          const categoryData = categoryCustomFieldData.value[category.id]
          if (categoryData && Object.keys(categoryData).length > 0) {
            // Filter out empty values
            const filteredCategoryData: Record<string, any> = {}
            Object.keys(categoryData).forEach(key => {
              const value = categoryData[key]
              if (value !== null && value !== undefined && value !== '') {
                if (typeof value === 'string' && value.trim() !== '') {
                  filteredCategoryData[key] = value.trim()
                } else if (typeof value === 'object' && value !== null) {
                  // For file objects, keep the metadata but don't include the File object
                  if (value.fileName) {
                    filteredCategoryData[key] = {
                      fileName: value.fileName,
                      fileSize: value.fileSize,
                      fileType: value.fileType,
                      uploaded: value.uploaded || false
                    }
                  } else {
                    filteredCategoryData[key] = value
                  }
                } else {
                  filteredCategoryData[key] = value
                }
              }
            })
            
            if (Object.keys(filteredCategoryData).length > 0) {
              categorizedFields[category.id] = filteredCategoryData
              hasAnyFields = true
            }
          }
        })
        
        // Merge categorized fields into the main object
        if (Object.keys(categorizedFields).length > 0) {
          Object.keys(categorizedFields).forEach(category => {
            mergedCustomFields[category] = categorizedFields[category]
          })
        }
        
        console.log('📝 Custom fields being saved:', mergedCustomFields)
        console.log('📝 Includes categorized fields:', Object.keys(categorizedFields))
        
        // Return null if no valid fields, otherwise return the merged object
        return hasAnyFields ? mergedCustomFields : null
      })()
    }
    
    // Prepare evaluation criteria separately
    const evaluationCriteriaData = criteria.value.map((criterion, index) => ({
      criteria_name: criterion.name || 'Unnamed Criterion',
      criteria_description: criterion.description || 'No description provided',
      weight_percentage: Number(criterion.weight) || 0,
      evaluation_type: 'scoring', // Default to scoring type
      min_score: 0, // Default minimum score
      max_score: 100, // Default maximum score
      median_score: 50, // Default median score
      is_mandatory: Boolean(criterion.isVeto),
      veto_enabled: Boolean(criterion.isVeto),
      veto_threshold: criterion.isVeto ? 50 : null, // Set veto threshold if it's a veto criterion
      min_word_count: null, // Not applicable for scoring type
      expected_boolean_answer: null, // Not applicable for scoring type
      display_order: index, // Set display order based on array position
      data_inventory: buildCriteriaDataInventory(criterion) // Include data_inventory for each criterion
      // Note: created_by is set automatically by perform_create in the backend
    }))
    
    // For creation, include all fields including rfp_number (evaluation_criteria saved separately)
    const rfpData = isUpdate ? baseRfpData : {
      rfp_number: formData.value.rfpNumber,
      ...baseRfpData,
      created_by: 1 // Mock user ID - only for creation
      // Note: evaluation_criteria are saved separately after RFP creation
    }

    // Ensure submission_deadline is acceptable to backend validation for draft saves
    // If deadline is in the past or invalid, omit it for draft creation
    try {
      if (!isUpdate && rfpData.submission_deadline) {
        const deadlineDate = new Date(rfpData.submission_deadline)
        if (isNaN(deadlineDate.getTime()) || deadlineDate <= new Date()) {
          console.warn('⚠️ submission_deadline is past/invalid; omitting for draft creation')
          rfpData.submission_deadline = null
        }
      }
    } catch (e) {
      rfpData.submission_deadline = null
    }

    // Note: Evaluation criteria will be saved separately after RFP creation/update
    // This ensures they are properly saved to the rfp_evaluation_criteria table
    // We no longer include them in the RFP creation/update request
    
    console.log('Sending RFP data:', JSON.stringify(rfpData, null, 2))
    console.log('📊 Data being sent - field check:', {
      hasTitle: !!rfpData.rfp_title,
      hasDescription: !!rfpData.description,
      hasType: !!rfpData.rfp_type,
      hasDates: !!rfpData.issue_date,
      dataKeys: Object.keys(rfpData),
      complianceType: typeof rfpData.compliance_requirements,
      complianceValue: rfpData.compliance_requirements
    })
    
    console.log(`Evaluation criteria will be saved separately after RFP ${isUpdate ? 'update' : 'creation'}`)
    if (!isUpdate) {
      console.log('Evaluation criteria to save:', evaluationCriteriaData)
    } else {
      console.log('Update mode: Evaluation criteria will be handled separately')
      console.log('🔄 PATCH data keys:', Object.keys(rfpData))
      console.log('🔄 PATCH data:', rfpData)
    }
    
    // Validate minimum title length to satisfy backend validator
    if (!formData.value.title || String(formData.value.title).trim().length < 5) {
      error('Validation Error', 'RFP title must be at least 5 characters long.')
      isSubmitting.value = false
      return
    }
    
    // Validate description is present
    if (!formData.value.description || String(formData.value.description).trim().length === 0) {
      error('Validation Error', 'RFP description is required.')
      isSubmitting.value = false
      return
    }
    
    // Validate RFP type is present
    if (!formData.value.type) {
      error('Validation Error', 'RFP type is required.')
      isSubmitting.value = false
      return
    }

    // Validate criteria weights (creation only) to avoid backend 400
    if (!isUpdate && Array.isArray(evaluationCriteriaData) && evaluationCriteriaData.length > 0) {
      const total = evaluationCriteriaData.reduce((s, c) => s + (Number(c.weight_percentage) || 0), 0)
      if (Math.abs(total - 100) > 0.01) {
        error('Validation Error', `Evaluation criteria weights must total 100%. Current total: ${total.toFixed(2)}%`)
        isSubmitting.value = false
        return
      }
    }
    
    // For updates, log if criteria are missing but don't block
    if (isUpdate && (!evaluationCriteriaData || evaluationCriteriaData.length === 0)) {
      console.log('⚠️ Update mode: No evaluation criteria in form - existing criteria in database will be preserved')
    }

    // Send API request - either POST (create) or PATCH (update)
    let response
    if (isUpdate) {
      try {
        // Update existing draft
        console.log(`📤 Sending PATCH request to /api/v1/rfps/${existingRfpId}/`)
        console.log('📤 With data:', JSON.stringify(rfpData, null, 2))
        
        response = await axios.patch(`${API_BASE_URL}/rfps/${existingRfpId}/`, rfpData, {
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        })
        console.log('✅ Draft updated successfully:', response.data)
      } catch (patchError) {
        console.error('❌ PATCH request failed:', patchError)
        console.error('❌ Error response:', patchError.response?.data)
        console.error('❌ Error status:', patchError.response?.status)
        console.error('❌ Data that was sent:', rfpData)
        throw patchError
      }
      
      // Evaluation criteria will be saved separately after RFP update (see below)
      // This ensures they are properly saved to the rfp_evaluation_criteria table
      
    } else {
      // Create new draft - evaluation_criteria will be saved separately after RFP creation
      response = await axios.post(`${API_BASE_URL}/rfps/`, rfpData, {
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      })
      console.log('New draft created successfully:', response.data)
    }
    
    console.log('RFP save response:', response.data)
    
    // Save the RFP ID for future reference (Django backend returns 'rfp_id' field)
    const savedRfpId = response.data.rfp_id || existingRfpId
    localStorage.setItem('current_rfp_id', savedRfpId)
    localStorage.setItem('selectedRFP', JSON.stringify(response.data))
    
    // Update form data with the RFP number from the response (user input or auto-generated)
    if (response.data.rfp_number) {
      formData.value.rfpNumber = response.data.rfp_number
      console.log(`✅ RFP Number updated from backend: ${response.data.rfp_number}`)
    }
    
    console.log(`RFP ${isUpdate ? 'updated' : 'created'} successfully with ID:`, savedRfpId)
    
    // Save evaluation criteria separately after RFP is created/updated
    // This ensures they are properly saved to the rfp_evaluation_criteria table
    if (evaluationCriteriaData && evaluationCriteriaData.length > 0) {
      try {
        console.log(`💾 Saving ${evaluationCriteriaData.length} evaluation criteria for RFP:`, savedRfpId)
        
        // For updates, delete existing criteria first (to replace them with new ones)
        if (isUpdate) {
          try {
            const existingCriteriaResponse = await axios.get(`${API_BASE_URL}/evaluation-criteria/?rfp=${savedRfpId}`, {
              headers: getAuthHeaders()
            })
            const existingCriteria = existingCriteriaResponse.data.results || existingCriteriaResponse.data || []
            
            // Delete existing criteria
            for (const criterion of existingCriteria) {
              const criteriaId = criterion.criteria_id || criterion.id
              if (criteriaId) {
                await axios.delete(`${API_BASE_URL}/evaluation-criteria/${criteriaId}/`, {
                  headers: getAuthHeaders()
                })
              }
            }
            console.log(`🗑️ Deleted ${existingCriteria.length} existing criteria`)
          } catch (deleteError) {
            console.warn('⚠️ Error deleting existing criteria (may not exist):', deleteError)
            // Continue even if delete fails (criteria might not exist yet)
          }
        }
        
        // Create/save all evaluation criteria
        for (const criterionData of evaluationCriteriaData) {
          try {
            // Prepare payload - rfp should be the RFP ID (primary key value)
            // created_by will be set automatically by perform_create in the backend
            const criteriaPayload = {
              criteria_name: criterionData.criteria_name,
              criteria_description: criterionData.criteria_description,
              weight_percentage: Number(criterionData.weight_percentage) || 0,
              evaluation_type: criterionData.evaluation_type || 'scoring',
              min_score: Number(criterionData.min_score) || 0,
              max_score: Number(criterionData.max_score) || 100,
              median_score: Number(criterionData.median_score) || 50,
              is_mandatory: Boolean(criterionData.is_mandatory),
              veto_enabled: Boolean(criterionData.veto_enabled),
              veto_threshold: criterionData.veto_threshold ? Number(criterionData.veto_threshold) : null,
              min_word_count: criterionData.min_word_count || null,
              expected_boolean_answer: criterionData.expected_boolean_answer || null,
              display_order: Number(criterionData.display_order) || 0,
              rfp: Number(savedRfpId), // ForeignKey field - pass RFP ID as integer
              data_inventory: criterionData.data_inventory || {} // Include data_inventory for each criterion
              // Note: created_by is set automatically by perform_create in views.py
            }
            
            console.log('📤 Creating evaluation criterion:', criteriaPayload.criteria_name)
            console.log('📋 Criterion payload:', JSON.stringify(criteriaPayload, null, 2))
            
            const criteriaResponse = await axios.post(`${API_BASE_URL}/evaluation-criteria/`, criteriaPayload, {
              headers: {
                ...getAuthHeaders(),
                'Content-Type': 'application/json',
                'Accept': 'application/json'
              }
            })
            
            console.log('✅ Criterion created successfully:', criteriaResponse.data)
          } catch (criterionError) {
            console.error('❌ Error creating criterion:', criterionData.criteria_name)
            console.error('❌ Error:', criterionError)
            if (criterionError.response) {
              console.error('❌ Response status:', criterionError.response.status)
              console.error('❌ Response data:', criterionError.response.data)
              // Log detailed validation errors if available
              if (criterionError.response.data?.errors) {
                console.error('❌ Validation errors:', criterionError.response.data.errors)
              }
              if (criterionError.response.data?.debug_info) {
                console.error('❌ Debug info:', criterionError.response.data.debug_info)
              }
            }
            // Log error but continue with other criteria
            error('Warning', `Failed to save criterion "${criterionData.criteria_name}". Other criteria will still be saved.`)
          }
        }
        
        console.log(`✅ Successfully saved ${evaluationCriteriaData.length} evaluation criteria`)
      } catch (criteriaError) {
        console.error('❌ Error saving evaluation criteria:', criteriaError)
        if (criteriaError.response) {
          console.error('❌ Response status:', criteriaError.response.status)
          console.error('❌ Response data:', criteriaError.response.data)
        }
        // Don't fail the entire operation if criteria save fails, but log it
        error('Warning', 'RFP saved but there was an error saving evaluation criteria. Please check and save them again.')
      }
    } else {
      if (isUpdate) {
        console.log('⚠️ No evaluation criteria in form - preserving existing criteria in database')
      } else {
        console.log('⚠️ No evaluation criteria to save')
      }
    }
    
    // Handle documents: upload pending documents and update RFP's documents list
    try {
      console.log('📎 Processing documents for RFP:', savedRfpId)
      console.log('📋 Current uploadedDocuments:', uploadedDocuments.value.map((d, idx) => ({
        index: idx,
        name: d.name,
        uploaded: d.uploaded,
        s3Id: d.s3Id,
        hasFile: !!d.file,
        isMerged: d.isMerged
      })))
      
      // Step 1: Upload any pending documents (documents with files but not yet uploaded)
      const pendingDocs = uploadedDocuments.value.filter(doc => !doc.uploaded && doc.file)
      console.log(`📤 Found ${pendingDocs.length} pending documents to upload`)
      
      const uploadedDocIds = []
      
      for (const doc of pendingDocs) {
        try {
          const docIndex = uploadedDocuments.value.findIndex(d => d === doc)
          console.log(`📤 Uploading document: ${doc.name}`)
          
          const uploadFormData = new FormData()
          uploadFormData.append('file', doc.file)
          uploadFormData.append('document_name', doc.name)
          uploadFormData.append('rfp_id', savedRfpId)
          uploadFormData.append('user_id', '1')
          
          const authHeaders = getAuthHeaders()
          delete authHeaders['Content-Type']  // Remove any Content-Type to let axios set it for FormData
          const uploadResponse = await axios.post(`${API_BASE_URL}/upload-document/`, uploadFormData, {
            headers: authHeaders,
            timeout: 60000
          })
          
          if (uploadResponse.data.success) {
            const docId = uploadResponse.data.document_id
            uploadedDocIds.push(docId)
            
            // Update the document in the array
            uploadedDocuments.value[docIndex].uploaded = true
            uploadedDocuments.value[docIndex].s3Id = docId
            
            console.log(`✅ Document uploaded: ${doc.name} (ID: ${docId})`)
          } else {
            console.error(`❌ Failed to upload document: ${doc.name}`, uploadResponse.data)
          }
        } catch (uploadError) {
          console.error(`❌ Error uploading document ${doc.name}:`, uploadError)
          // Continue with other documents even if one fails
        }
      }
      
      // Step 2: Collect all document IDs (already uploaded + newly uploaded + merged documents)
      const allDocumentIds = uploadedDocuments.value
        .filter(doc => doc.uploaded && doc.s3Id)
        .map(doc => Number(doc.s3Id))
        .filter(id => !isNaN(id) && id > 0)
      
      console.log(`📋 All document IDs to save:`, allDocumentIds)
      console.log(`   - Already uploaded: ${allDocumentIds.length - uploadedDocIds.length}`)
      console.log(`   - Newly uploaded: ${uploadedDocIds.length}`)
      console.log(`   - Total: ${allDocumentIds.length}`)
      
      // Step 3: Update RFP's documents field with all document IDs
      if (allDocumentIds.length > 0) {
        try {
          const updateResponse = await axios.post(`${API_BASE_URL}/rfps/${savedRfpId}/update-documents/`, {
            documents: allDocumentIds
          }, {
            headers: getAuthHeaders()
          })
          
          console.log('✅ RFP documents updated successfully:', updateResponse.data)
          console.log(`✅ Saved ${allDocumentIds.length} documents to RFP (including ${uploadedDocuments.value.filter(d => d.isMerged).length} merged document(s))`)
        } catch (updateError) {
          console.error('❌ Error updating RFP documents:', updateError)
          // Don't fail the entire save if document update fails
        }
      } else {
        console.log('ℹ️ No documents to save for this RFP')
      }
    } catch (docError) {
      console.error('❌ Error processing documents:', docError)
      // Don't fail the entire save if document processing fails
    }
    
    success(
      isUpdate ? 'Draft Updated' : 'Draft Saved', 
      `Your RFP has been ${isUpdate ? 'updated' : 'saved'} as a draft with ${criteria.value.length} evaluation criteria${uploadedDocuments.value.filter(d => d.uploaded).length > 0 ? ` and ${uploadedDocuments.value.filter(d => d.uploaded).length} document(s)` : ''}.`
    )

  // If editing due to a change request, complete the change request and resume the same stage
  try {
    const changeRequestMode = route.query.mode === 'change_request'
    const changeRequestId = route.query.changeRequest || localStorage.getItem('current_change_request_id')
    const approvalId = route.query.approvalId || localStorage.getItem('current_approval_id')
    const stageId = route.query.stageId || localStorage.getItem('current_stage_id')
    if (changeRequestMode && changeRequestId && approvalId && stageId) {
      const respondUrl = getTprmApiUrl('rfp-approval/change-requests/respond/')
      const payload = {
        change_request_id: changeRequestId,
        approval_id: approvalId,
        stage_id: stageId,
        rfp_id: savedRfpId,
        status: 'completed',
        // Persist the latest RFP JSON so reviewers see the updated context
        json_payload: {
          rfp_id: savedRfpId,
          rfp_number: formData.value.rfpNumber,
          rfp_title: formData.value.title,
          description: formData.value.description,
          rfp_type: formData.value.type,
          category: formData.value.category,
          estimated_value: formData.value.estimatedValue,
          currency: formData.value.currency,
          budget_range_min: formData.value.budgetMin,
          budget_range_max: formData.value.budgetMax,
          issue_date: formData.value.issueDate,
          submission_deadline: formData.value.deadline,
          evaluation_period_end: formData.value.evaluationPeriodEnd,
          evaluation_method: formData.value.evaluationMethod,
          criticality_level: formData.value.criticalityLevel,
          geographical_scope: formData.value.geographicalScope,
          compliance_requirements: formData.value.complianceRequirements,
          allow_late_submissions: formData.value.allowLateSubmissions,
          auto_approve: formData.value.autoApprove,
          evaluation_criteria: criteria.value.map((c, idx) => ({
            id: c.id,
            criteria_name: c.name,
            criteria_description: c.description,
            weight_percentage: c.weight,
            evaluation_type: 'scoring',
            min_score: 0,
            max_score: 100,
            median_score: 50,
            is_mandatory: c.isVeto,
            veto_enabled: c.isVeto,
            veto_threshold: c.isVeto ? 50 : null,
            display_order: idx
          }))
        }
      }
      await axios.post(respondUrl, payload, { headers: getAuthHeaders() })
      console.log('✅ Change request completed and workflow resumed from same stage')
    }
  } catch (crErr) {
    console.warn('⚠️ Failed to complete change request automatically:', crErr?.response?.data || crErr.message)
  }
    
    // If this save is in response to change requests, also record an RFP version snapshot server-side
    // This creates a version in rfp_version_history (rfp_versions table)
    try {
      const isChangeRequestSave = changeRequestMode || changeRequestId
      if (isChangeRequestSave && savedRfpId && isUpdate) {
        console.log('📝 Recording RFP version due to change request for RFP:', savedRfpId)
        const changeReason = changeRequestId 
          ? `Addressed change request ${changeRequestId}`
          : 'RFP updated after change request'
        
        // Prepare complete RFP data for versioning
        const completeRfpData = {
          ...baseRfpData,
          rfp_id: Number(savedRfpId),
          rfp_number: formData.value.rfpNumber,
          evaluation_criteria: evaluationCriteriaData
        }
        
        const versioningPayload = {
          rfp_id: Number(savedRfpId),
          rfp_data: completeRfpData,
          change_reason: changeReason,
          change_request_id: changeRequestId || undefined,
          fields_changed: [],
          user_id: 1, // Get from auth if available
          user_name: 'RFP Creator',
          user_role: 'Creator'
        }
        
        await axios.post(`${API_BASE_URL}/rfps/${savedRfpId}/edit_with_versioning/`, versioningPayload, {
          headers: getAuthHeaders()
        })
        console.log('✅ RFP version recorded in rfp_version_history successfully')
      }
    } catch (verr) {
      console.warn('⚠️ Failed to record RFP version:', verr?.response?.data || verr.message)
      // Don't fail the entire save if versioning fails
    }

    // Create notification (use 'draft_saved' for both create and update since status is still DRAFT)
    await notificationService.createRFPNotification('draft_saved', {
      rfp_id: savedRfpId,
      rfp_title: formData.value.title
    })
    
    // Clear the current draft from localStorage since it's now saved as a real RFP
    localStorage.removeItem('rfp_draft_current')
    console.log('Draft cleared from localStorage after successful RFP save')
    
    // Don't reset form when updating - keep the data for continued editing
    if (!isUpdate) {
      resetFormData()
    }
    
    // Update the store with the new RFP
    try {
      await rfpStore.fetchRFPs() // Refresh the store
      console.log('Store updated with new RFP')
    } catch (storeErr) {
      console.error('Error updating store:', storeErr)
    }
    
    // Verify the RFP was saved by fetching it and check criteria
    try {
      const verifyResponse = await axios.get(`${API_BASE_URL}/rfps/${savedRfpId}`, {
        headers: getAuthHeaders()
      })
      console.log('Verification: RFP exists in database:', verifyResponse.data)
      
      // Check if evaluation criteria were saved
      if (verifyResponse.data.evaluation_criteria && verifyResponse.data.evaluation_criteria.length > 0) {
        console.log('✅ Evaluation criteria successfully saved:', verifyResponse.data.evaluation_criteria)
        console.log(`✅ Total criteria saved: ${verifyResponse.data.evaluation_criteria.length}`)
        
        // Log each criterion for verification
        verifyResponse.data.evaluation_criteria.forEach((criterion, index) => {
          console.log(`Criterion ${index + 1}:`, {
            name: criterion.criteria_name,
            weight: criterion.weight_percentage,
            veto: criterion.veto_enabled,
            mandatory: criterion.is_mandatory,
            evaluation_type: criterion.evaluation_type
          })
        })
      } else {
        console.warn('⚠️ No evaluation criteria found in saved RFP')
      }
    } catch (verifyErr) {
      console.error('Error verifying RFP save:', verifyErr)
    }
  } catch (err) {
    console.error('Error saving RFP:', err)
    if (err.response && err.response.data) {
      console.error('Error details:', err.response.data)
      error('Error', `Failed to save RFP: ${JSON.stringify(err.response.data)}`)
    } else {
      error('Error', 'Failed to save RFP. Please try again.')
    }
    
    // Create error notification
    await notificationService.createRFPErrorNotification('save_draft', err.message, {
      title: 'Failed to Save Draft',
      rfp_title: formData.value.title
    })
  } finally {
    isSubmitting.value = false
  }
}

// Show TPRM Consent Modal
async function showTPRMConsentModal(actionType, config) {
  console.log('[TPRM Consent] Showing consent modal for action:', actionType, 'config:', config)
  
  // Wait for component to mount with retry mechanism
  let retries = 0
  const maxRetries = 10
  while (!consentModalRef.value && retries < maxRetries) {
    if (retries === 0) {
      await nextTick()
    } else {
      // Wait progressively longer on subsequent retries (50ms, 100ms, 150ms, etc.)
      await new Promise(resolve => setTimeout(resolve, 50 * retries))
    }
    retries++
    
    if (consentModalRef.value) {
      console.log(`[TPRM Consent] Consent modal ref available after ${retries} retries`)
      break
    }
  }
  
  if (!consentModalRef.value) {
    console.error('[TPRM Consent] Consent modal ref not available after', maxRetries, 'retries')
    console.error('[TPRM Consent] Modal component may not be mounted. Check template.')
    console.error('[TPRM Consent] consentModalRef:', consentModalRef)
    console.error('[TPRM Consent] consentModalRef.value:', consentModalRef.value)
    
    // For security, don't proceed without consent modal - show error and prevent submission
    error('Consent Modal Error', 'Consent modal is not available. Please refresh the page and try again. If the problem persists, contact your administrator.')
    // Return false to prevent submission
    return false
  }
  
  try {
    console.log('[TPRM Consent] Calling consentModalRef.value.show()')
    // Show the modal and wait for user response
    // The modal component handles its own visibility internally
    const accepted = await consentModalRef.value.show(actionType, config)
    
    console.log('[TPRM Consent] Consent modal result:', accepted, 'type:', typeof accepted)
    
    // Ensure boolean return value
    const result = accepted === true || accepted === 'true'
    console.log('[TPRM Consent] Final consent result:', result)
    return result
  } catch (error) {
    console.error('[TPRM Consent] Error showing consent modal:', error)
    console.error('[TPRM Consent] Error stack:', error.stack)
    // If modal was cancelled/rejected, return false
    if (error.message && error.message.includes('cancelled')) {
      return false
    }
    // On any error, don't proceed (fail closed for security)
    error('Consent Error', 'An error occurred while showing the consent modal. Please try again.')
    return false
  }
}

// Helper function to actually proceed to approval workflow (called after consent is obtained)
const proceedToApprovalWorkflowAction = async (consentConfig) => {
  console.log('[TPRM Consent] Proceeding to approval workflow, consentConfig:', consentConfig)
  
  try {
    // Add consent data to RFP data if consent was provided
    // This will be stored when saving the RFP
    if (consentConfig) {
      // Store consent info in formData or pass it along when saving
      formData.value.consent_accepted = true
      formData.value.consent_config_id = consentConfig.config_id
      formData.value.framework_id = 1 // Default TPRM framework
    }

    // Detect change request mode early
    const changeRequestMode = route.query.mode === 'change_request'

    // Check auto-approve BEFORE saving to handle it correctly
    const shouldAutoApprove = Boolean(formData.value.autoApprove)
    console.log('🔍 Checking auto-approve status before saving:', shouldAutoApprove)

    // First save the RFP as draft (this already responds to the change request and records version)
    await handleSaveDraft()

    // In change request mode, do NOT create new approval requests/versions or reassign reviewers
    if (changeRequestMode) {
      success('Changes Submitted', 'Updated RFP has been saved. Reviewers at the same stage can continue the approval process.')
      // Optionally navigate back to Change Request Manager
      setTimeout(() => {
        router.push({ name: 'ChangeRequestManager' })
      }, 800)
      isSubmitting.value = false
      return { success: true }
    }
    
    // Get the RFP ID
    const rfpId = localStorage.getItem('current_rfp_id')
    console.log('Retrieved RFP ID from localStorage:', rfpId)
    
    if (!rfpId) {
      error('Error', 'Could not find RFP ID. Please try again.')
      isSubmitting.value = false
      throw new Error('Could not find RFP ID')
    }

    // Verify auto-approve status from saved RFP
    let rfpAutoApprove = shouldAutoApprove
    try {
      const rfpCheckResponse = await axios.get(`${API_BASE_URL}/rfps/${rfpId}/`, {
        headers: getAuthHeaders()
      })
      rfpAutoApprove = Boolean(rfpCheckResponse.data.auto_approve || rfpCheckResponse.data.autoApprove || shouldAutoApprove)
      console.log('✅ Verified auto-approve status from saved RFP:', rfpAutoApprove)
      console.log('✅ RFP data auto_approve field:', rfpCheckResponse.data.auto_approve)
      console.log('✅ Current RFP status:', rfpCheckResponse.data.status)
    } catch (checkError) {
      console.warn('⚠️ Could not verify auto-approve status from RFP, using form value:', shouldAutoApprove)
      rfpAutoApprove = shouldAutoApprove
    }

    // If auto-approve is enabled, skip approval workflow and directly approve
    if (rfpAutoApprove) {
      console.log('✅ Auto-approve enabled - bypassing approval workflow and directly approving RFP')
      
      try {
        // Use the approve endpoint which now handles auto-approve from any status (except CANCELLED/ARCHIVED)
        const approveResponse = await axios.post(`${API_BASE_URL}/rfps/${rfpId}/approve/`, {}, {
          headers: getAuthHeaders()
        })
        
        console.log('✅ RFP auto-approved successfully:', approveResponse.data)
        
        // Verify the status was updated correctly
        const verifyResponse = await axios.get(`${API_BASE_URL}/rfps/${rfpId}/`, {
          headers: getAuthHeaders()
        })
        console.log('✅ Verified RFP status after approval:', verifyResponse.data.status)
        console.log('✅ RFP approved_by:', verifyResponse.data.approved_by)
        console.log('✅ RFP approval_workflow_id:', verifyResponse.data.approval_workflow_id)
        
        // Ensure approval_workflow_id is null for auto-approved RFPs
        if (verifyResponse.data.approval_workflow_id) {
          console.log('⚠️ approval_workflow_id is not null, clearing it...')
          await axios.patch(`${API_BASE_URL}/rfps/${rfpId}/`, {
            approval_workflow_id: null
          }, {
            headers: getAuthHeaders()
          })
        }
        
        // Clear draft from localStorage
        localStorage.removeItem('rfp_draft_current')
        localStorage.removeItem('rfp_for_approval_workflow') // Clear any approval workflow data
        resetFormData()
        
        success('RFP Auto-Approved', 'RFP has been automatically approved by the creator. No approval workflow required.')
        
        isSubmitting.value = false
        
        // Navigate to RFP list
        setTimeout(() => {
          router.push('/rfp-list')
        }, 1000)
        
        return
      } catch (approveError) {
        console.error('❌ Error auto-approving RFP:', approveError)
        if (approveError.response) {
          console.error('❌ Error response:', approveError.response.data)
          console.error('❌ Error status:', approveError.response.status)
          
          // If approve endpoint fails, try direct PATCH as fallback
          try {
            console.log('⚠️ Trying fallback: direct status update to APPROVED')
            const fallbackResponse = await axios.patch(`${API_BASE_URL}/rfps/${rfpId}/`, {
              status: 'APPROVED',
              approved_by: 1,
              approval_workflow_id: null // Ensure no approval workflow is assigned
            }, {
              headers: getAuthHeaders()
            })
            console.log('✅ Fallback successful - RFP status set to APPROVED via PATCH')
            
            // Verify the status was updated correctly
            const verifyResponse = await axios.get(`${API_BASE_URL}/rfps/${rfpId}/`, {
              headers: getAuthHeaders()
            })
            console.log('✅ Verified RFP status after fallback:', verifyResponse.data.status)
            
            localStorage.removeItem('rfp_draft_current')
            localStorage.removeItem('rfp_for_approval_workflow')
            resetFormData()
            success('RFP Auto-Approved', 'RFP has been automatically approved by the creator.')
            isSubmitting.value = false
            setTimeout(() => {
              router.push('/rfp-list')
            }, 1000)
            return
          } catch (fallbackError) {
            console.error('❌ Fallback also failed:', fallbackError)
            error('Auto-Approval Error', `Failed to auto-approve RFP. Please try again or proceed through normal approval workflow.`)
            isSubmitting.value = false
            return
          }
        } else {
          error('Auto-Approval Error', `Failed to auto-approve RFP: ${approveError.message || 'Unknown error'}. Please try again or proceed through normal approval workflow.`)
          isSubmitting.value = false
          return
        }
      }
    }
    
    console.log('ℹ️ Auto-approve not enabled, proceeding with normal approval workflow')

    // Upload documents to S3 if any are selected
    let documentIds = []
    if (uploadedDocuments.value.length > 0) {
      console.log('Uploading documents to S3...')
      isUploadingDocuments.value = true
      
      try {
        console.log(`📤 Starting upload of ${uploadedDocuments.value.length} documents`)
        
        // Initialize progress
        uploadProgress.value = {
          current: 0,
          total: uploadedDocuments.value.length,
          currentDocument: ''
        }
        
        for (let i = 0; i < uploadedDocuments.value.length; i++) {
          const doc = uploadedDocuments.value[i]
          
          // Skip already uploaded documents
          if (doc.uploaded) {
            console.log(`⏭️ Skipping already uploaded document: ${doc.name}`)
            documentIds.push(doc.s3Id)
            continue
          }
          
          console.log(`📤 Uploading document ${i + 1}/${uploadedDocuments.value.length}: ${doc.name}`)
          console.log(`📁 File details: ${doc.fileName} (${doc.fileSize} bytes)`) 
          
          // Update progress
          uploadProgress.value.current = i + 1
          uploadProgress.value.currentDocument = doc.name
         
          // Create FormData for file upload
          const formData = new FormData()
          formData.append('file', doc.file)
          formData.append('document_name', doc.name)
          formData.append('rfp_id', rfpId)
          formData.append('user_id', '1') // Mock user ID for development
          
          console.log(`📋 FormData prepared for: ${doc.name}`)
          
          try {
            // Upload to S3 via backend API
            const authHeaders = getAuthHeaders()
            delete authHeaders['Content-Type']  // Remove any Content-Type to let axios set it for FormData
            const uploadResponse = await axios.post(`${API_BASE_URL}/upload-document/`, formData, {
              headers: authHeaders,
              timeout: 60000 // 60 second timeout for large files
            })
            
            console.log(`📊 Upload response for ${doc.name}:`, uploadResponse.data)
            
            if (uploadResponse.data.success) {
              documentIds.push(uploadResponse.data.document_id)
              uploadedDocuments.value[i].uploaded = true
              uploadedDocuments.value[i].s3Id = uploadResponse.data.document_id
              console.log(`✅ Document uploaded successfully: ${doc.name} (ID: ${uploadResponse.data.document_id})`)
            } else {
              console.error(`❌ Failed to upload document: ${doc.name}`, uploadResponse.data.error)
              error('Upload Error', `Failed to upload document: ${doc.name} - ${uploadResponse.data.error}`)
            }
          } catch (uploadError) {
            console.error(`❌ Upload error for document: ${doc.name}`, uploadError)
            if (uploadError.response) {
              console.error(`❌ Response data:`, uploadError.response.data)
              console.error(`❌ Response status:`, uploadError.response.status)
            }
            error('Upload Error', `Failed to upload document: ${doc.name} - ${uploadError.message}`)
          }
        }
        
        console.log(`📊 Upload Summary: ${documentIds.length}/${uploadedDocuments.value.length} documents uploaded successfully`)
        console.log('📋 Document IDs collected:', documentIds)
        
        // Update RFP with document IDs using a dedicated endpoint
        if (documentIds.length > 0) {
          console.log(`💾 Updating RFP ${rfpId} with ${documentIds.length} document IDs...`)
          
          try {
            const updateResponse = await axios.post(`${API_BASE_URL}/rfps/${rfpId}/update-documents/`, {
              documents: documentIds
            }, {
              headers: getAuthHeaders()
            })
            
            console.log('📊 RFP update response:', updateResponse.data)
            
            if (updateResponse.data.success) {
              console.log('✅ RFP updated with document IDs:', documentIds)
              success('Documents Uploaded', `Successfully uploaded ${documentIds.length} document(s) to S3.`)
              
              // Clear uploaded documents after successful upload
              uploadedDocuments.value = []
            } else {
              console.error('❌ RFP update failed:', updateResponse.data.error)
              error('Update Error', `Failed to update RFP with documents: ${updateResponse.data.error}`)
            }
          } catch (updateError) {
            console.error('❌ RFP update error:', updateError)
            if (updateError.response) {
              console.error('❌ Update response data:', updateError.response.data)
            }
            error('Update Error', `Failed to update RFP with documents: ${updateError.message}`)
          }
        } else {
          console.warn('⚠️ No documents were uploaded successfully')
          error('Upload Failed', 'No documents were uploaded successfully. Please check the files and try again.')
        }
        
      } catch (uploadError) {
        console.error('Error uploading documents:', uploadError)
        error('Upload Error', 'Failed to upload documents to S3. Please try again.')
        return
      } finally {
        isUploadingDocuments.value = false
        // Reset progress
        uploadProgress.value = {
          current: 0,
          total: 0,
          currentDocument: ''
        }
      }
    }
    
    // For non-change-request flow, continue with versioning and navigation
    // Store RFP data for the approval workflow (using Django backend field names)
    const rfpData = {
      rfp_id: rfpId,
      rfp_number: formData.value.rfpNumber,
      rfp_title: formData.value.title,
      title: formData.value.title, // Keep both for compatibility
      description: formData.value.description,
      rfp_type: formData.value.type,
      type: formData.value.type, // Keep both for compatibility
      category: formData.value.category,
      estimated_value: formData.value.estimatedValue,
      estimatedValue: formData.value.estimatedValue, // Keep both for compatibility
      currency: formData.value.currency,
      budget_range_min: formData.value.budgetMin,
      budgetMin: formData.value.budgetMin, // Keep both for compatibility
      budget_range_max: formData.value.budgetMax,
      budgetMax: formData.value.budgetMax, // Keep both for compatibility
      issue_date: formData.value.issueDate,
      issueDate: formData.value.issueDate, // Keep both for compatibility
      submission_deadline: formData.value.deadline,
      deadline: formData.value.deadline, // Keep both for compatibility
      evaluation_period_end: formData.value.evaluationPeriodEnd,
      evaluationPeriodEnd: formData.value.evaluationPeriodEnd, // Keep both for compatibility
      timeline: formData.value.timeline,
      evaluation_method: formData.value.evaluationMethod,
      evaluationMethod: formData.value.evaluationMethod, // Keep both for compatibility
      criticality_level: formData.value.criticalityLevel,
      criticalityLevel: formData.value.criticalityLevel, // Keep both for compatibility
      geographical_scope: formData.value.geographicalScope,
      geographicalScope: formData.value.geographicalScope, // Keep both for compatibility
      compliance_requirements: formData.value.complianceRequirements,
      complianceRequirements: formData.value.complianceRequirements, // Keep both for compatibility
      allow_late_submissions: formData.value.allowLateSubmissions,
      allowLateSubmissions: formData.value.allowLateSubmissions, // Keep both for compatibility
      // Note: auto_approve should be false here since we already handled auto-approve case above
      auto_approve: false,
      autoApprove: false, // Keep both for compatibility
      criteria: criteria.value.map((criterion, index) => ({
        id: criterion.id,
        name: criterion.name,
        description: criterion.description,
        weight: criterion.weight,
        isVeto: criterion.isVeto,
        isMandatory: criterion.isVeto,
        evaluationType: 'scoring',
        minScore: 0,
        maxScore: 100,
        medianScore: 50,
        vetoThreshold: criterion.isVeto ? 50 : null,
        displayOrder: index
      }))
    }
    
    // Store the RFP data in localStorage for the approval workflow
    console.log('Storing RFP data in localStorage:', rfpData)
    console.log('RFP data keys:', Object.keys(rfpData))
    localStorage.setItem('rfp_for_approval_workflow', JSON.stringify(rfpData))
    localStorage.setItem('selectedRFP', JSON.stringify(rfpData))
    
    // Create version for the RFP (initial or revision)
    try {
      // Check if this is a resubmission after change request
      const isResubmission = localStorage.getItem('current_change_requests')
      const changeRequests = isResubmission ? JSON.parse(isResubmission) : []
      
      if (isResubmission && changeRequests.length > 0) {
        console.log('🔄 Creating revision version for RFP after change request:', rfpId)
        
        // Get the latest version number
        const versionHistoryResponse = await axios.get(getTprmApiUrl(`rfp-approval/approval-request-versions/${rfpId}/`), {
          headers: getAuthHeaders()
        })
        
        let nextVersionNumber = 1
        if (versionHistoryResponse.data.success && versionHistoryResponse.data.versions) {
          const maxVersion = Math.max(...versionHistoryResponse.data.versions.map(v => v.version_number))
          nextVersionNumber = maxVersion + 1
        }
        
        const versionData = {
          approval_id: rfpId, // Use rfp_id as approval_id for now
          version_number: nextVersionNumber,
          version_label: `Revision ${nextVersionNumber} - After Change Request`,
          version_type: 'REVISION',
          changes_summary: `RFP revised after ${changeRequests.length} change request(s)`,
          change_reason: `Resubmitted after addressing change requests from reviewers`,
          created_by: '1', // Mock user ID for development
          created_by_name: 'RFP Creator',
          created_by_role: 'Creator',
          is_current: true,
          is_approved: false
        }
        
        const versionResponse = await axios.post(getTprmApiUrl('rfp-approval/approval-request-versions/'), versionData, {
          headers: getAuthHeaders()
        })
        
        if (versionResponse.data.success) {
          console.log('✅ Revision version created successfully:', versionResponse.data.version_id)
          localStorage.setItem('current_rfp_version_id', versionResponse.data.version_id)
          
          // Clear change requests after successful resubmission
          localStorage.removeItem('current_change_requests')
        } else {
          console.warn('⚠️ Failed to create revision version:', versionResponse.data.error)
        }
      } else {
        console.log('🔄 Creating initial version for RFP:', rfpId)
        
        const versionData = {
          approval_id: rfpId, // Use rfp_id as approval_id for now
          version_number: 1,
          version_label: 'Initial Submission',
          version_type: 'INITIAL',
          changes_summary: 'Initial RFP creation and submission for approval',
          change_reason: 'RFP created and submitted for review',
          created_by: '1', // Mock user ID for development
          created_by_name: 'RFP Creator',
          created_by_role: 'Creator',
          is_current: true,
          is_approved: false
        }
        
        const versionResponse = await axios.post(getTprmApiUrl('rfp-approval/approval-request-versions/'), versionData, {
          headers: getAuthHeaders()
        })
        
        if (versionResponse.data.success) {
          console.log('✅ Initial version created successfully:', versionResponse.data.version_id)
          localStorage.setItem('current_rfp_version_id', versionResponse.data.version_id)
        } else {
          console.warn('⚠️ Failed to create initial version:', versionResponse.data.error)
        }
      }
    } catch (versionError) {
      console.error('❌ Error creating version:', versionError)
      // Don't fail the entire process if version creation fails
    }
    
    // Clear the current draft from localStorage since it's now saved as a real RFP
    localStorage.removeItem('rfp_draft_current')
    console.log('Draft cleared from localStorage after proceeding to approval workflow')
    
    // Reset form data to initial state for fresh start
    resetFormData()
    
    success('RFP Saved', 'RFP has been saved. Proceeding to approval workflow creation.')
    
    // Navigate to the approval workflow creator using Vue Router
    setTimeout(() => {
      router.push('/approval-management')
    }, 1000)
    
    return { success: true }
  } catch (err) {
    console.error('Error in proceedToApprovalWorkflowAction:', err)
    if (err.response && err.response.data) {
      console.error('Error details:', err.response.data)
      error('Error', `Failed to save RFP: ${JSON.stringify(err.response.data)}`)
    } else {
      error('Error', `Failed to save RFP: ${err.message || 'Unknown error'}`)
    }
    throw err // Re-throw to be caught by outer handler
  } finally {
    isSubmitting.value = false
  }
}

const handleProceedToApprovalWorkflow = async () => {
  if (!isFormValid.value) {
    error('Validation Error', 'Please fill in all required fields and ensure evaluation criteria weights total 100%.')
    return
  }
  
  try {
    isSubmitting.value = true
    console.log('[TPRM Consent] ========== Starting consent flow for: tprm_create_rfp')
    
    // Wrap proceed to approval workflow with consent check
    // The consent modal will be shown by executeWithTPRMConsent if consent is required
    const result = await executeWithTPRMConsent(
      TPRM_CONSENT_ACTIONS.CREATE_RFP,
      proceedToApprovalWorkflowAction,
      showTPRMConsentModal
    )
    
    // Check if proceeding was cancelled due to consent rejection
    if (result === null) {
      console.log('[RFP Submit] Proceeding to approval cancelled - consent not accepted')
      error('Consent Required', 'Submission cancelled. You must accept the consent to proceed to approval workflow.')
      isSubmitting.value = false
      return
    }
    
    // Success is already handled in proceedToApprovalWorkflowAction
  } catch (err) {
    console.error('Error in handleProceedToApprovalWorkflow:', err)
    
    // Check if error is due to consent rejection
    if (err.message && (err.message.includes('consent') || err.message.includes('Consent') || err.message.includes('cancelled'))) {
      error('Consent Required', 'Submission cancelled. You must accept the consent to proceed to approval workflow.')
      isSubmitting.value = false
      return
    }
    
    // Other errors are already handled in proceedToApprovalWorkflowAction
    isSubmitting.value = false
  }
}

const startFresh = () => {
  try {
    // Don't allow starting fresh if we're in change request mode
    const changeRequestMode = route.query.mode === 'change_request'
    if (changeRequestMode) {
      console.warn('⚠️ Cannot start fresh in change request mode - preserving loaded RFP data')
      showDraftRecovery.value = false
      return
    }
    
    localStorage.removeItem('rfp_draft_current')
    localStorage.removeItem('current_rfp_id') // Clear RFP ID to ensure fresh creation
    localStorage.removeItem('edit_rfp_draft') // Clear edit flag
    showDraftRecovery.value = false
    console.log('Started fresh - removed existing draft and RFP ID')
    
    // Reset form to ensure clean state
    resetFormData()
    
    success('Started Fresh', 'Starting with a clean form.')
  } catch (error) {
    console.error('Error starting fresh:', error)
    error('Error', 'Failed to start fresh. Please refresh the page.')
  }
}

// Function to clear draft state and start fresh (for button in header)
const clearDraftAndStartFresh = () => {
  PopupService.confirm(
    'Are you sure you want to start a new RFP? Any unsaved changes will be lost.',
    'Start Fresh',
    () => {
      startFresh()
    },
    undefined
  )
}

// Function to hide/remove an entire section/tab
const hideTab = (tabValue: string) => {
  const tab = formTabs.find(t => t.value === tabValue)
  if (!tab) return
  
  // Only allow hiding tabs that can be hidden
  if (!tab.canHide) {
    PopupService.warning('This section cannot be removed as it contains required fields.', 'Cannot Remove Section')
    return
  }
  
  // Confirm before hiding
  const confirmMessage = `Are you sure you want to remove the "${tab.label}" section? You can restore it later if needed.`
  const confirmHeading = 'Remove Section'
  const onConfirmRemove = () => {
    hiddenTabs.value.add(tabValue)
    
    // If the hidden tab is currently active, switch to the first visible tab
    if (activeTab.value === tabValue) {
      const nextVisibleTab = visibleTabs.value.find(t => t.value !== tabValue)
      if (nextVisibleTab) {
        activeTab.value = nextVisibleTab.value
      } else {
        // If no other visible tabs, switch to basic (which cannot be hidden)
        activeTab.value = 'basic'
      }
    }
    
    console.log(`Tab ${tabValue} hidden from form`)
    PopupService.success('Section Removed', `The "${tab.label}" section has been removed. You can restore it from the hidden sections area.`)
  }
  const onCancelRemove = undefined
  
  PopupService.confirm(confirmMessage, confirmHeading, onConfirmRemove, onCancelRemove)
}

// Function to restore a hidden section/tab
const restoreTab = (tabValue: string) => {
  const tab = formTabs.find(t => t.value === tabValue)
  if (!tab) return
  
  hiddenTabs.value.delete(tabValue)
  
  // Switch to the restored tab
  activeTab.value = tabValue
  
  console.log(`Tab ${tabValue} restored`)
  PopupService.success('Section Restored', `The "${tab.label}" section has been restored.`)
}

// Function to hide/remove a specific form field from the UI
const hideField = (fieldName: string) => {
  if (fieldName in hiddenFields.value) {
    hiddenFields.value[fieldName] = true
    // Clear the field value as well when hiding
    if (fieldName in formData.value) {
      if (fieldName === 'currency') {
        formData.value[fieldName] = 'USD'
      } else if (fieldName === 'evaluationMethod') {
        formData.value[fieldName] = 'weighted_scoring'
      } else if (fieldName === 'criticalityLevel') {
        formData.value[fieldName] = 'medium'
      } else if (fieldName === 'allowLateSubmissions' || fieldName === 'autoApprove') {
        formData.value[fieldName] = false
      } else {
        formData.value[fieldName] = ''
      }
    }
    console.log(`Field ${fieldName} hidden from form`)
    success('Field Removed', `The ${fieldName} field has been removed from the form.`)
  }
}

// Function to hide/remove a custom field from the UI
const hideCustomField = (fieldName: string) => {
  hiddenCustomFields.value.add(fieldName)
  // Clear the field value as well when hiding
  if (formData.value.customFields && fieldName in formData.value.customFields) {
    const fieldSchema = customFieldsSchema.value.find(f => f.name === fieldName)
    if (fieldSchema) {
      if (fieldSchema.type === 'checkbox') {
        formData.value.customFields[fieldName] = false
      } else if (fieldSchema.default !== undefined) {
        formData.value.customFields[fieldName] = fieldSchema.default
      } else {
        formData.value.customFields[fieldName] = ''
      }
    } else {
      formData.value.customFields[fieldName] = ''
    }
  }
  console.log(`Custom field ${fieldName} hidden from form`)
  success('Field Removed', `The custom field has been removed from the form.`)
}

// Function to clear a specific form field (kept for backward compatibility if needed)
const clearField = (fieldName: string, defaultValue: any = '') => {
  if (fieldName in formData.value) {
    // Handle different field types
    if (typeof defaultValue === 'boolean') {
      formData.value[fieldName] = defaultValue
    } else if (typeof defaultValue === 'string' && defaultValue !== '') {
      formData.value[fieldName] = defaultValue
    } else {
      // Clear to empty string for text fields, or appropriate default
      if (fieldName === 'currency') {
        formData.value[fieldName] = 'USD'
      } else if (fieldName === 'evaluationMethod') {
        formData.value[fieldName] = 'weighted_scoring'
      } else if (fieldName === 'criticalityLevel') {
        formData.value[fieldName] = 'medium'
      } else {
        formData.value[fieldName] = ''
      }
    }
    console.log(`Field ${fieldName} cleared`)
  }
}

// Function to clear a custom field value (kept for backward compatibility if needed)
const clearCustomField = (fieldName: string) => {
  if (formData.value.customFields && fieldName in formData.value.customFields) {
    // Get the field type to determine default value
    const fieldSchema = customFieldsSchema.value.find(f => f.name === fieldName)
    if (fieldSchema) {
      if (fieldSchema.type === 'checkbox') {
        formData.value.customFields[fieldName] = false
      } else if (fieldSchema.default !== undefined) {
        formData.value.customFields[fieldName] = fieldSchema.default
      } else {
        formData.value.customFields[fieldName] = ''
      }
    } else {
      formData.value.customFields[fieldName] = ''
    }
    console.log(`Custom field ${fieldName} cleared`)
  }
}

// Function to reset form data to initial state
const resetFormData = () => {
  formData.value = {
    // Basic Information
    rfpNumber: '',
    title: '',
    description: '',
    type: '',
    category: '',
    
    // Financial Information
    estimatedValue: '',
    currency: 'USD',
    budgetMin: '',
    budgetMax: '',
    
    // Timeline Information
    issueDate: '',
    deadline: '',
    evaluationPeriodEnd: '',
    timeline: '',
    
    // Evaluation & Process
    evaluationMethod: 'weighted_scoring',
    criticalityLevel: 'medium',
    
    // Scope & Requirements
    geographicalScope: '',
    complianceRequirements: '',
    
    // Additional Options
    allowLateSubmissions: false,
    autoApprove: false,
    
    // Custom Fields
    customFields: {}
  }
  
  // Clear custom fields schema
  customFieldsSchema.value = []
  
  // Reset hidden fields - make all fields visible again
  hiddenFields.value = {
    category: false,
    estimatedValue: false,
    currency: false,
    timeline: false,
    budgetMin: false,
    budgetMax: false,
    evaluationPeriodEnd: false,
    evaluationMethod: false,
    criticalityLevel: false,
    geographicalScope: false,
    complianceRequirements: false,
    allowLateSubmissions: false,
    autoApprove: false
  }
  hiddenCustomFields.value.clear()
  
  // Reset hidden tabs - make all tabs visible again
  hiddenTabs.value.clear()
  showHiddenTabs.value = false
  
  // Reset criteria to default values
  criteria.value = [
    {
      id: '1',
      name: 'Technical Capability',
      description: 'Vendor\'s technical expertise and infrastructure',
      weight: 30,
      isVeto: true,
    },
    {
      id: '2',
      name: 'Cost Effectiveness',
      description: 'Value for money and pricing structure',
      weight: 25,
      isVeto: false,
    },
    {
      id: '3',
      name: 'Experience & References',
      description: 'Previous experience and client references',
      weight: 20,
      isVeto: true,
    },
    {
      id: '4',
      name: 'Implementation Timeline',
      description: 'Proposed timeline and delivery schedule',
      weight: 15,
      isVeto: false,
    },
    {
      id: '5',
      name: 'Support & Maintenance',
      description: 'Ongoing support and maintenance capabilities',
      weight: 10,
      isVeto: false,
    },
  ]
  
  console.log('Form data reset to initial state')
}

// Load realistic sample data into the form
const loadSampleData = () => {
  const today = new Date()
  const inTwoWeeks = new Date(today.getTime() + 14 * 24 * 60 * 60 * 1000)
  const inOneMonth = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000)

  const formatDate = (d: Date) => d.toISOString().split('T')[0]
  const formatDateTimeLocal = (d: Date) => {
    const iso = d.toISOString()
    return iso.slice(0, 16)
  }
  const pad = (n: number, size = 2) => String(n).padStart(size, '0')

  // Generate a mostly-unique RFP number to avoid backend UNIQUE constraint errors
  const year = today.getFullYear()
  const month = pad(today.getMonth() + 1)
  const day = pad(today.getDate())
  const hours = pad(today.getHours())
  const minutes = pad(today.getMinutes())
  const randomSuffix = Math.floor(Math.random() * 900 + 100) // 3‑digit random
  const generatedRfpNumber = `RFP-${year}${month}${day}-${hours}${minutes}-${randomSuffix}`

  // Try to pick a realistic RFP type from loaded types if available
  const sampleType = rfpTypes.value[0] || 'Technology Services'

  formData.value = {
    // Basic Information
    rfpNumber: generatedRfpNumber,
    title: 'Enterprise Cloud Security & Compliance Platform',
    description:
      'We are seeking proposals for an enterprise-grade cloud security and compliance platform to monitor, detect, and remediate risks across multi-cloud environments (AWS, Azure, GCP). The solution should provide real-time visibility, automated controls, and evidence collection to support SOC 2, ISO 27001, and other regulatory frameworks.',
    type: sampleType,
    category: 'security',

    // Financial Information
    estimatedValue: '750000',
    currency: 'USD',
    budgetMin: '500000',
    budgetMax: '900000',

    // Timeline Information
    issueDate: formatDate(today),
    deadline: formatDateTimeLocal(inTwoWeeks),
    evaluationPeriodEnd: formatDate(inOneMonth),
    timeline: '12-month implementation with phased rollout across business units',

    // Evaluation & Process
    evaluationMethod: 'weighted_scoring',
    criticalityLevel: 'high',

    // Scope & Requirements
    geographicalScope: 'North America & Europe (remote delivery allowed)',
    complianceRequirements:
      'SOC 2 Type II, ISO 27001, GDPR readiness, data residency controls for EU customers.',

    // Additional Options
    allowLateSubmissions: false,
    autoApprove: false,

    // Custom Fields
    customFields: { ...formData.value.customFields }
  }

  // Sample evaluation criteria (must total 100%)
  criteria.value = [
    {
      id: 'crit-tech',
      name: 'Technical Capability & Architecture',
      description:
        'Depth of security features, scalability, integration options (APIs, SIEM, ticketing), and support for multi-cloud environments.',
      weight: 35,
      isVeto: true
    },
    {
      id: 'crit-risk',
      name: 'Risk, Compliance & Reporting',
      description:
        'Support for regulatory frameworks (SOC 2, ISO 27001, GDPR), audit-ready reporting, evidence collection, and control monitoring.',
      weight: 25,
      isVeto: true
    },
    {
      id: 'crit-price',
      name: 'Commercials & Total Cost of Ownership',
      description:
        'Pricing model, transparency of costs over 3 years, and overall value for money.',
      weight: 20,
      isVeto: false
    },
    {
      id: 'crit-experience',
      name: 'Experience, References & Support',
      description:
        'Relevant customer references in financial services, implementation experience, and quality of ongoing support.',
      weight: 10,
      isVeto: false
    },
    {
      id: 'crit-delivery',
      name: 'Implementation Timeline & Delivery Approach',
      description:
        'Realistic implementation plan, milestones, change management, and knowledge transfer.',
      weight: 10,
      isVeto: false
    }
  ]

  activeTab.value = 'basic'
  showTipsDialog.value = true

  success('Sample Data Loaded', 'Realistic sample data has been loaded into the RFP form.')
}

const resumeDraft = async () => {
  try {
    // Don't allow resuming draft if we're in change request mode
    const changeRequestMode = route.query.mode === 'change_request'
    if (changeRequestMode) {
      console.warn('⚠️ Cannot resume draft in change request mode - preserving loaded RFP data')
      showDraftRecovery.value = false
      return
    }
    
    const draftString = localStorage.getItem('rfp_draft_current')
    if (!draftString) {
      error('No Draft Found', 'No draft found to restore.')
      return
    }

    const draftData = JSON.parse(draftString)
    console.log('Resuming draft with data:', draftData)
    
    // Restore form data with proper fallbacks
    formData.value = {
      // Basic Information
      rfpNumber: draftData.rfpNumber || '',
      title: draftData.title || '',
      description: draftData.description || '',
      type: draftData.type || '',
      category: draftData.category || '',
      
      // Financial Information
      estimatedValue: draftData.estimatedValue || '',
      currency: draftData.currency || 'USD',
      budgetMin: draftData.budgetMin || '',
      budgetMax: draftData.budgetMax || '',
      
      // Timeline Information
      issueDate: draftData.issueDate || '',
      deadline: draftData.deadline || '',
      evaluationPeriodEnd: draftData.evaluationPeriodEnd || '',
      timeline: draftData.timeline || '',
      
      // Evaluation & Process
      evaluationMethod: draftData.evaluationMethod || 'weighted_scoring',
      criticalityLevel: draftData.criticalityLevel || 'medium',
      
      // Scope & Requirements
      geographicalScope: draftData.geographicalScope || '',
      complianceRequirements: draftData.complianceRequirements || '',
      
      // Additional Options
      allowLateSubmissions: Boolean(draftData.allowLateSubmissions),
      autoApprove: Boolean(draftData.autoApprove),
      
      // Custom Fields
      customFields: draftData.customFields || {}
    }
    
    // Fetch custom fields schema if type is set
    if (formData.value.type) {
      await fetchCustomFields(formData.value.type)
      // Merge any existing custom fields values properly
      // Note: fetchCustomFields already handles mapping old field names to new ones
      if (draftData.customFields) {
        // Map old field names to new ones based on schema
        const mappedFields = mapOldFieldNamesToNew(draftData.customFields, customFieldsSchema.value)
        // Merge each field individually to maintain reactivity
        Object.keys(mappedFields).forEach(key => {
          if (formData.value.customFields && key in formData.value.customFields) {
            formData.value.customFields[key] = mappedFields[key]
          }
        })
      }
    }

    // Restore criteria with validation
    if (draftData.criteria && Array.isArray(draftData.criteria)) {
      criteria.value = draftData.criteria.map(criterion => ({
        id: criterion.id || Date.now().toString(),
        name: criterion.name || '',
        description: criterion.description || '',
        weight: Number(criterion.weight) || 0,
        isVeto: Boolean(criterion.isVeto)
      }))
    } else {
      // If no criteria in draft, keep default criteria
      console.log('No criteria found in draft, keeping defaults')
    }
    
    // Restore hidden fields
    if (draftData.hiddenFields) {
      hiddenFields.value = { ...hiddenFields.value, ...draftData.hiddenFields }
    }
    
    // Restore hidden custom fields
    if (draftData.hiddenCustomFields && Array.isArray(draftData.hiddenCustomFields)) {
      hiddenCustomFields.value = new Set(draftData.hiddenCustomFields)
    }
    
    // Restore hidden tabs
    if (draftData.hiddenTabs && Array.isArray(draftData.hiddenTabs)) {
      hiddenTabs.value = new Set(draftData.hiddenTabs)
      // If the active tab is hidden, switch to first visible tab
      if (hiddenTabs.value.has(activeTab.value)) {
        const firstVisible = visibleTabs.value[0]
        if (firstVisible) {
          activeTab.value = firstVisible.value
        }
      }
    }

    showDraftRecovery.value = false
    
    // Update last saved time if available
    if (draftData.lastSaved) {
      lastSaved.value = new Date(draftData.lastSaved)
    }
    
    success('Draft Restored', 'Your previous work has been restored successfully.')
    console.log('Draft restored successfully')
    
  } catch (error) {
    console.error('Error resuming draft:', error)
    error('Restore Failed', 'Failed to restore draft. Starting fresh instead.')
    
    // Clean up corrupted draft
    localStorage.removeItem('rfp_draft_current')
    showDraftRecovery.value = false
  }
}

// Document generation functions
const generateDocument = async (format: 'word' | 'pdf') => {
  try {
    isGeneratingDocument.value = true
    
    // Validate required fields before generating document
    if (!formData.value.rfpNumber || !formData.value.title || !formData.value.description || !formData.value.type) {
      error('Validation Error', 'Please fill in all required fields (RFP Number, Title, Description, and Type) before generating a document.')
      return
    }
    
    // Prepare RFP data for document generation
    const rfpData = {
      rfpNumber: formData.value.rfpNumber,
      title: formData.value.title,
      description: formData.value.description,
      type: formData.value.type || 'technology',
      category: formData.value.category || '',
      estimatedValue: formData.value.estimatedValue ? Number(formData.value.estimatedValue) : null,
      currency: formData.value.currency || 'USD',
      budgetMin: formData.value.budgetMin ? Number(formData.value.budgetMin) : null,
      budgetMax: formData.value.budgetMax ? Number(formData.value.budgetMax) : null,
      issueDate: formData.value.issueDate ? new Date(formData.value.issueDate).toISOString().split('T')[0] : null,
      deadline: formData.value.deadline ? new Date(formData.value.deadline).toISOString() : null,
      evaluationPeriodEnd: formData.value.evaluationPeriodEnd ? new Date(formData.value.evaluationPeriodEnd).toISOString().split('T')[0] : null,
      evaluationMethod: formData.value.evaluationMethod || 'weighted_scoring',
      criticalityLevel: formData.value.criticalityLevel || 'medium',
      geographicalScope: formData.value.geographicalScope || '',
      complianceRequirements: formData.value.complianceRequirements || '',
      allowLateSubmissions: Boolean(formData.value.allowLateSubmissions),
      autoApprove: Boolean(formData.value.autoApprove),
      status: 'DRAFT',
      criteria: criteria.value.map((criterion, index) => ({
        name: criterion.name || 'Unnamed Criterion',
        description: criterion.description || 'No description provided',
        weight: Number(criterion.weight) || 0,
        isVeto: Boolean(criterion.isVeto),
        isMandatory: Boolean(criterion.isVeto),
        evaluationType: 'scoring',
        minScore: 0,
        maxScore: 100,
        medianScore: 50,
        vetoThreshold: criterion.isVeto ? 50 : null,
        displayOrder: index
      }))
    }
    
    console.log('Generating document with data:', rfpData)
    
    // Call the document generation API (using Django backend)
    const response = await axios.post(`${API_BASE_URL}/generate-document/`, {
      rfp_number: rfpData.rfpNumber,
      rfp_title: rfpData.title,
      description: rfpData.description,
      rfp_type: rfpData.type.toUpperCase(),
      category: rfpData.category,
      estimated_value: rfpData.estimatedValue,
      currency: rfpData.currency,
      budget_range_min: rfpData.budgetMin,
      budget_range_max: rfpData.budgetMax,
      issue_date: rfpData.issueDate,
      submission_deadline: rfpData.deadline,
      evaluation_period_end: rfpData.evaluationPeriodEnd,
      evaluation_method: rfpData.evaluationMethod,
      criticality_level: rfpData.criticalityLevel,
      geographical_scope: rfpData.geographicalScope,
      compliance_requirements: rfpData.complianceRequirements ? [rfpData.complianceRequirements] : null,
      allow_late_submissions: rfpData.allowLateSubmissions,
      auto_approve: rfpData.autoApprove,
      status: 'DRAFT',
      evaluation_criteria: rfpData.criteria.map((criterion, index) => ({
        criteria_name: criterion.name,
        criteria_description: criterion.description,
        weight_percentage: criterion.weight,
        evaluation_type: criterion.evaluationType || 'scoring',
        min_score: 0, // Default minimum score
        max_score: 100, // Default maximum score
        median_score: 50, // Default median score
        is_mandatory: criterion.isMandatory,
        veto_enabled: criterion.isVeto,
        veto_threshold: criterion.isVeto ? 50 : null,
        min_word_count: null,
        expected_boolean_answer: null,
        display_order: index
      })),
      format: format
    }, {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      responseType: 'blob' // Important for file downloads
    })
    
    // Create download link
    const blob = new Blob([response.data], {
      type: format === 'word' 
        ? 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        : 'application/pdf'
    })
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    const filename = `${formData.value.rfpNumber || 'RFP'}_${timestamp}.${format === 'word' ? 'docx' : 'pdf'}`
    link.download = filename
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    success('Document Generated', `${format.toUpperCase()} document has been generated and downloaded.`)
    
  } catch (err) {
    console.error('Error generating document:', err)
    
    let errorMessage = `Failed to generate ${format.toUpperCase()} document.`
    
    if (err.response) {
      // Server responded with error status
      if (err.response.status === 401) {
        errorMessage = 'Authentication required. Please log in and try again.'
      } else if (err.response.status === 400) {
        errorMessage = 'Invalid data provided. Please check all required fields.'
      } else if (err.response.status === 500) {
        errorMessage = 'Server error occurred. Please try again later.'
      } else {
        errorMessage = `Server error (${err.response.status}). Please try again.`
      }
      
      console.error('Server response:', err.response.data)
    } else if (err.request) {
      // Request was made but no response received
      errorMessage = 'Network error. Please check your connection and try again.'
      console.error('No response received:', err.request)
    } else {
      // Something else happened
      errorMessage = `Unexpected error: ${err.message}`
      console.error('Error message:', err.message)
    }
    
    error('Document Generation Error', errorMessage)
  } finally {
    isGeneratingDocument.value = false
  }
}

const loadRFPForChangeRequest = async (rfpId) => {
  try {
    console.log('🔄 Loading RFP for change request editing:', rfpId)
    
    // Try the change request specific endpoint first, fallback to regular endpoint
    let response
    let rfpData
    
    try {
      const url = buildApiUrl(`/rfp-details-for-change-request/${rfpId}/`)
      response = await apiCall(url)
      
      if (response.success && response.rfp) {
        rfpData = response.rfp
      } else {
        throw new Error('Change request endpoint failed')
      }
    } catch (error) {
      console.warn('⚠️ Change request endpoint failed, using regular endpoint:', error)
      // Fallback to regular RFP details endpoint
      const fallbackUrl = buildApiUrl(`/rfp-details/${rfpId}/`)
      const fallbackResponse = await apiCall(fallbackUrl)
      
      // Handle both response formats
      if (fallbackResponse.rfp_id || fallbackResponse.rfp_title) {
        rfpData = fallbackResponse
        // Wrap it in the expected format
        response = {
          success: true,
          rfp: fallbackResponse,
          change_requests_count: 0,
          change_requests: []
        }
      } else {
        throw new Error('Failed to load RFP data from both endpoints')
      }
    }
    
    if (response && (response.success || rfpData)) {
      console.log('✅ RFP data loaded for change request editing:', response.rfp || rfpData)
      console.log('📋 Change requests found:', response.change_requests_count)
      
      // Use rfpData if available, otherwise use response.rfp
      const dataToUse = rfpData || response.rfp
      
      // DEBUG: Log the full response structure
      console.log('🔍 FULL RESPONSE STRUCTURE:', JSON.stringify(response, null, 2))
      console.log('🔍 dataToUse keys:', Object.keys(dataToUse || {}))
      console.log('🔍 dataToUse.evaluation_criteria:', dataToUse?.evaluation_criteria)
      console.log('🔍 dataToUse.criteria:', dataToUse?.criteria)
      console.log('🔍 response.rfp?.evaluation_criteria:', response?.rfp?.evaluation_criteria)
      console.log('🔍 response.rfp?.criteria:', response?.rfp?.criteria)
      
      // Helper function to format date for input[type="date"]
      const formatDateForInput = (dateString) => {
        if (!dateString) return ''
        try {
          return dateString.split('T')[0]
        } catch (e) {
          return dateString
        }
      }
      
      // Helper function to format datetime for input[type="datetime-local"]
      const formatDateTimeForInput = (dateString) => {
        if (!dateString) return ''
        try {
          const date = new Date(dateString)
          const year = date.getFullYear()
          const month = String(date.getMonth() + 1).padStart(2, '0')
          const day = String(date.getDate()).padStart(2, '0')
          const hours = String(date.getHours()).padStart(2, '0')
          const minutes = String(date.getMinutes()).padStart(2, '0')
          return `${year}-${month}-${day}T${hours}:${minutes}`
        } catch (e) {
          console.error('Error formatting datetime:', e)
          return ''
        }
      }
      
      // Helper to convert number to string for input fields
      const toStringValue = (value) => {
        if (value === null || value === undefined) return ''
        return String(value)
      }
      
      // Load the RFP data into the form
      formData.value = {
        rfpNumber: toStringValue(dataToUse.rfp_number || dataToUse.rfpNumber),
        title: toStringValue(dataToUse.rfp_title || dataToUse.title),
        description: toStringValue(dataToUse.description || ''),
        type: toStringValue(dataToUse.rfp_type || dataToUse.type || 'TECHNOLOGY'),
        category: toStringValue(dataToUse.category || ''),
        estimatedValue: toStringValue(dataToUse.estimated_value || dataToUse.estimatedValue),
        currency: dataToUse.currency || 'USD',
        budgetMin: toStringValue(dataToUse.budget_range_min || dataToUse.budgetMin),
        budgetMax: toStringValue(dataToUse.budget_range_max || dataToUse.budgetMax),
        issueDate: formatDateForInput(dataToUse.issue_date || dataToUse.issueDate),
        deadline: formatDateTimeForInput(dataToUse.submission_deadline || dataToUse.deadline),
        evaluationPeriodEnd: formatDateForInput(dataToUse.evaluation_period_end || dataToUse.evaluationPeriodEnd),
        timeline: toStringValue(dataToUse.timeline || ''),
        evaluationMethod: dataToUse.evaluation_method || dataToUse.evaluationMethod || 'weighted_scoring',
        criticalityLevel: dataToUse.criticality_level || dataToUse.criticalityLevel || 'medium',
        geographicalScope: toStringValue(dataToUse.geographical_scope || dataToUse.geographicalScope || ''),
        complianceRequirements: Array.isArray(dataToUse.compliance_requirements) 
          ? dataToUse.compliance_requirements.join(', ') 
          : toStringValue(dataToUse.compliance_requirements || dataToUse.complianceRequirements || ''),
        allowLateSubmissions: Boolean(dataToUse.allow_late_submissions || dataToUse.allowLateSubmissions),
        autoApprove: Boolean(dataToUse.auto_approve || dataToUse.autoApprove),
        customFields: dataToUse.custom_fields || dataToUse.customFields || {}
      }
      
      // Fetch custom fields schema if type is set
      if (formData.value.type) {
        await fetchCustomFields(formData.value.type)
        // If custom fields were loaded from RFP, merge them properly
        // Note: fetchCustomFields already handles mapping old field names to new ones
        if (dataToUse.custom_fields || dataToUse.customFields) {
          const loadedFields = dataToUse.custom_fields || dataToUse.customFields
          // Separate RFP type fields from categorized fields
          const rfpTypeFields: Record<string, any> = {}
          const categorizedFields: Record<string, Record<string, any>> = {}
          
          Object.keys(loadedFields).forEach(key => {
            // Check if this is a category key (matches one of our categories)
            const isCategory = customFieldCategories.value.some(cat => cat.id === key)
            if (isCategory && typeof loadedFields[key] === 'object' && !Array.isArray(loadedFields[key])) {
              // This is a categorized field group
              categorizedFields[key] = loadedFields[key]
            } else {
              // This is a regular RFP type field
              rfpTypeFields[key] = loadedFields[key]
            }
          })
          
          // Map old field names to new ones based on schema for RFP type fields
          const mappedFields = mapOldFieldNamesToNew(rfpTypeFields, customFieldsSchema.value)
          // Merge each field individually to maintain reactivity
          Object.keys(mappedFields).forEach(key => {
            if (formData.value.customFields && key in formData.value.customFields) {
              formData.value.customFields[key] = mappedFields[key]
            }
          })
          
          // Load categorized fields
          loadCategorizedCustomFields(categorizedFields)
        }
      } else if (dataToUse.custom_fields || dataToUse.customFields) {
        // Even if no type, try to load categorized fields
        const loadedFields = dataToUse.custom_fields || dataToUse.customFields
        const categorizedFields: Record<string, Record<string, any>> = {}
        
        Object.keys(loadedFields).forEach(key => {
          const isCategory = customFieldCategories.value.some(cat => cat.id === key)
          if (isCategory && typeof loadedFields[key] === 'object' && !Array.isArray(loadedFields[key])) {
            categorizedFields[key] = loadedFields[key]
          }
        })
        
        if (Object.keys(categorizedFields).length > 0) {
          loadCategorizedCustomFields(categorizedFields)
        }
      }
      
      // Load evaluation criteria if available - check multiple possible locations
      let criteriaList = null
      
      // Try multiple possible locations in the response (check in order of priority)
      if (response?.evaluation_criteria && Array.isArray(response.evaluation_criteria) && response.evaluation_criteria.length > 0) {
        criteriaList = response.evaluation_criteria
        console.log('✅ Found criteria in response.evaluation_criteria (top-level):', criteriaList.length)
      } else if (dataToUse?.evaluation_criteria && Array.isArray(dataToUse.evaluation_criteria) && dataToUse.evaluation_criteria.length > 0) {
        criteriaList = dataToUse.evaluation_criteria
        console.log('✅ Found criteria in dataToUse.evaluation_criteria:', criteriaList.length)
      } else if (dataToUse?.criteria && Array.isArray(dataToUse.criteria) && dataToUse.criteria.length > 0) {
        criteriaList = dataToUse.criteria
        console.log('✅ Found criteria in dataToUse.criteria:', criteriaList.length)
      } else if (response?.rfp?.evaluation_criteria && Array.isArray(response.rfp.evaluation_criteria) && response.rfp.evaluation_criteria.length > 0) {
        criteriaList = response.rfp.evaluation_criteria
        console.log('✅ Found criteria in response.rfp.evaluation_criteria:', criteriaList.length)
      } else if (response?.rfp?.criteria && Array.isArray(response.rfp.criteria) && response.rfp.criteria.length > 0) {
        criteriaList = response.rfp.criteria
        console.log('✅ Found criteria in response.rfp.criteria:', criteriaList.length)
      }
      
      // If still no criteria found, fetch directly from evaluation-criteria endpoint
      if (!criteriaList || (Array.isArray(criteriaList) && criteriaList.length === 0)) {
        console.warn('⚠️ No criteria in response, fetching directly from evaluation-criteria API...')
        try {
          const rfpIdForQuery = dataToUse?.rfp_id || dataToUse?.id || rfpId
          console.log(`📡 Fetching criteria directly for rfp_id=${rfpIdForQuery}`)
          
          const criteriaResponse = await axios.get(`${API_BASE_URL}/evaluation-criteria/?rfp=${rfpIdForQuery}`, {
            headers: getAuthHeaders()
          })
          
          const directCriteria = criteriaResponse.data.results || criteriaResponse.data || []
          console.log(`📡 Direct API fetch returned ${Array.isArray(directCriteria) ? directCriteria.length : 0} criteria`)
          
          if (Array.isArray(directCriteria) && directCriteria.length > 0) {
            criteriaList = directCriteria
            console.log('✅ SUCCESS: Loaded criteria from direct API call')
          } else {
            console.error('❌ Direct API also returned empty results')
            criteriaList = []
          }
        } catch (directErr) {
          console.error('❌ Error fetching criteria directly:', directErr)
          criteriaList = []
        }
      }
      
      console.log('📋 Evaluation criteria from response:', criteriaList)
      console.log('📋 Criteria list type:', Array.isArray(criteriaList) ? 'Array' : typeof criteriaList)
      console.log('📋 Criteria list length:', Array.isArray(criteriaList) ? criteriaList.length : 'N/A')
      
      if (Array.isArray(criteriaList) && criteriaList.length > 0) {
        console.log('🔄 Processing', criteriaList.length, 'criteria items...')
        criteria.value = criteriaList.map((criterion, index) => {
          // Handle both object and direct field access
          const criterionObj = criterion || {}
          
          const mappedCriterion = {
            id: criterionObj.id || criterionObj.criteria_id || `${Date.now()}-${index}`,
            name: criterionObj.name || criterionObj.criteria_name || '',
            description: criterionObj.description || criterionObj.criteria_description || '',
            weight: Number(criterionObj.weight || criterionObj.weight_percentage || 0),
            isVeto: Boolean(criterionObj.isVeto || criterionObj.veto_enabled || criterionObj.isMandatory || criterionObj.is_mandatory || false)
          }
          console.log(`  ✅ [${index + 1}] Mapped criterion:`, {
            id: mappedCriterion.id,
            name: mappedCriterion.name,
            description: mappedCriterion.description ? mappedCriterion.description.substring(0, 50) + '...' : '',
            weight: mappedCriterion.weight,
            isVeto: mappedCriterion.isVeto,
            raw: criterionObj
          })
          return mappedCriterion
        })
        console.log('✅ SUCCESS: Loaded evaluation criteria:', criteria.value.length, 'criteria')
        console.log('📊 Final criteria array:', criteria.value)
      } else {
        console.error('❌ FAILED: No evaluation criteria found')
        console.error('❌ dataToUse:', dataToUse)
        console.error('❌ response:', response)
        criteria.value = []
      }
      
      // Load uploaded documents if available
      const documentsList = dataToUse.documents || []
      console.log('📎 Documents from response:', documentsList)
      
      if (Array.isArray(documentsList) && documentsList.length > 0) {
        console.log('📎 Loading documents for change request editing:', documentsList.length)
        
        // Fetch document details for each document ID or object
        const documentPromises = documentsList.map(async (docItem) => {
          // Handle both document IDs (numbers) and document objects
          const docId = typeof docItem === 'object' ? (docItem.id || docItem.s3Id || docItem.s3_id) : docItem
          
          if (!docId) {
            console.warn('⚠️ Document item has no ID:', docItem)
            return null
          }
          
          // If it's already a full document object, use it directly
          if (typeof docItem === 'object' && (docItem.url || docItem.file_name || docItem.document_name)) {
            console.log(`📄 Using document object directly: ${docId}`)
            return {
              name: docItem.document_name || docItem.file_name || `Document ${docId}`,
              fileName: docItem.file_name || 'unknown',
              fileSize: docItem.file_size || 0,
              fileType: docItem.file_type || 'pdf',
              url: docItem.url || null,
              uploaded: true,
              s3Id: docId,
              file: null,
              isMerged: docItem.metadata?.is_merged || false
            }
          }
          
          // Otherwise, fetch from API
          try {
            console.log(`📥 Fetching document ${docId} from API...`)
            const docResponse = await axios.get(`${API_BASE_URL}/s3-files/${docId}/`, {
              headers: getAuthHeaders()
            })
            
            const fileData = docResponse.data.s3_file || docResponse.data
            console.log(`✅ Fetched document ${docId}:`, fileData)
            
            return {
              name: fileData.document_name || fileData.file_name || `Document ${docId}`,
              fileName: fileData.file_name || 'unknown',
              fileSize: fileData.file_size || 0,
              fileType: fileData.file_type || 'pdf',
              url: fileData.url || null,
              uploaded: true,
              s3Id: docId,
              file: null,
              isMerged: fileData.metadata?.is_merged || false
            }
          } catch (docError) {
            console.error(`❌ Error fetching document ${docId}:`, docError)
            return null
          }
        })
        
        const documents = await Promise.all(documentPromises)
        uploadedDocuments.value = documents.filter(doc => doc !== null)
        
        console.log(`✅ Loaded ${uploadedDocuments.value.length} uploaded documents`)
        console.log('📄 Document details:', uploadedDocuments.value.map(d => ({
          name: d.name,
          s3Id: d.s3Id,
          uploaded: d.uploaded
        })))
      } else {
        console.log('📎 No documents found in response')
        uploadedDocuments.value = []
      }
      
      // Show change requests if any
      const changeRequests = response.change_requests || dataToUse.change_requests || []
      if (changeRequests.length > 0) {
        console.log('📋 Change requests found:', changeRequests)
        
        // Show a notification about change requests
        showInfo('Change Requests Found', `Found ${changeRequests.length} change request(s) for this RFP. Please review and make necessary changes.`)
        
        // Store change requests for display
        localStorage.setItem('current_change_requests', JSON.stringify(changeRequests))
      }
      
      // Store the RFP ID for future reference
      const finalRfpId = dataToUse.rfp_id || dataToUse.id || rfpId
      localStorage.setItem('current_rfp_id', String(finalRfpId))
      
      // Clear any draft recovery dialog if it's showing
      showDraftRecovery.value = false
      
      // Clear any existing local draft to prevent conflicts
      localStorage.removeItem('rfp_draft_current')
      
      console.log('✅ Form data after loading:', {
        rfpNumber: formData.value.rfpNumber,
        title: formData.value.title,
        description: formData.value.description,
        type: formData.value.type,
        hasCriteria: criteria.value.length > 0,
        hasDocuments: uploadedDocuments.value.length > 0
      })
      
      success('RFP Loaded for Editing', 'RFP has been loaded successfully. You can now edit the fields and resubmit.')
      
    } else {
      console.error('❌ Failed to load RFP data for change request:', response?.error || 'Unknown error')
      showError('Load Error', 'Failed to load RFP data for change request editing. Please try again.')
    }
  } catch (error) {
    console.error('❌ Error loading RFP for change request:', error)
    showError('Load Error', 'Failed to load RFP data for change request editing.')
  }
}

const previewDocument = async () => {
  try {
    isGeneratingDocument.value = true
    
    // Validate required fields before generating preview
    if (!formData.value.rfpNumber || !formData.value.title || !formData.value.description || !formData.value.type) {
      error('Validation Error', 'Please fill in all required fields (RFP Number, Title, Description, and Type) before generating a preview.')
      return
    }
    
    // Prepare RFP data for document generation
    const rfpData = {
      rfpNumber: formData.value.rfpNumber,
      title: formData.value.title,
      description: formData.value.description,
      type: formData.value.type || 'technology',
      category: formData.value.category || '',
      estimatedValue: formData.value.estimatedValue ? Number(formData.value.estimatedValue) : null,
      currency: formData.value.currency || 'USD',
      budgetMin: formData.value.budgetMin ? Number(formData.value.budgetMin) : null,
      budgetMax: formData.value.budgetMax ? Number(formData.value.budgetMax) : null,
      issueDate: formData.value.issueDate ? new Date(formData.value.issueDate).toISOString().split('T')[0] : null,
      deadline: formData.value.deadline ? new Date(formData.value.deadline).toISOString() : null,
      evaluationPeriodEnd: formData.value.evaluationPeriodEnd ? new Date(formData.value.evaluationPeriodEnd).toISOString().split('T')[0] : null,
      evaluationMethod: formData.value.evaluationMethod || 'weighted_scoring',
      criticalityLevel: formData.value.criticalityLevel || 'medium',
      geographicalScope: formData.value.geographicalScope || '',
      complianceRequirements: formData.value.complianceRequirements || '',
      allowLateSubmissions: Boolean(formData.value.allowLateSubmissions),
      autoApprove: Boolean(formData.value.autoApprove),
      status: 'DRAFT',
      criteria: criteria.value.map((criterion, index) => ({
        name: criterion.name || 'Unnamed Criterion',
        description: criterion.description || 'No description provided',
        weight: Number(criterion.weight) || 0,
        isVeto: Boolean(criterion.isVeto),
        isMandatory: Boolean(criterion.isVeto),
        evaluationType: 'scoring',
        minScore: 0,
        maxScore: 100,
        medianScore: 50,
        vetoThreshold: criterion.isVeto ? 50 : null,
        displayOrder: index
      }))
    }
    
    // Call the document generation API for preview (PDF only) - using Django backend
    const response = await axios.post(`${API_BASE_URL}/generate-document/`, {
      rfp_number: rfpData.rfpNumber,
      rfp_title: rfpData.title,
      description: rfpData.description,
      rfp_type: rfpData.type.toUpperCase(),
      category: rfpData.category,
      estimated_value: rfpData.estimatedValue,
      currency: rfpData.currency,
      budget_range_min: rfpData.budgetMin,
      budget_range_max: rfpData.budgetMax,
      issue_date: rfpData.issueDate,
      submission_deadline: rfpData.deadline,
      evaluation_period_end: rfpData.evaluationPeriodEnd,
      evaluation_method: rfpData.evaluationMethod,
      criticality_level: rfpData.criticalityLevel,
      geographical_scope: rfpData.geographicalScope,
      compliance_requirements: rfpData.complianceRequirements ? [rfpData.complianceRequirements] : null,
      allow_late_submissions: rfpData.allowLateSubmissions,
      auto_approve: rfpData.autoApprove,
      status: 'DRAFT',
      evaluation_criteria: rfpData.criteria.map((criterion, index) => ({
        criteria_name: criterion.name,
        criteria_description: criterion.description,
        weight_percentage: criterion.weight,
        evaluation_type: criterion.evaluationType || 'scoring',
        min_score: 0, // Default minimum score
        max_score: 100, // Default maximum score
        median_score: 50, // Default median score
        is_mandatory: criterion.isMandatory,
        veto_enabled: criterion.isVeto,
        veto_threshold: criterion.isVeto ? 50 : null,
        min_word_count: null,
        expected_boolean_answer: null,
        display_order: index
      })),
      format: 'pdf'
    }, {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      responseType: 'blob'
    })
    
    // Create preview in new window
    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    
    // Open in new window
    const previewWindow = window.open(url, '_blank')
    if (previewWindow) {
      previewWindow.document.title = `RFP Preview - ${formData.value.rfpNumber || 'RFP'}`
    } else {
      // Fallback: download the file
      const link = document.createElement('a')
      link.href = url
      link.download = `${formData.value.rfpNumber || 'RFP'}_preview.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
    
    // Clean up URL after a delay
    setTimeout(() => {
      window.URL.revokeObjectURL(url)
    }, 1000)
    
    success('Document Preview', 'Document preview has been opened in a new window.')
    
  } catch (err) {
    console.error('Error generating preview:', err)
    
    let errorMessage = 'Failed to generate document preview.'
    
    if (err.response) {
      // Server responded with error status
      if (err.response.status === 401) {
        errorMessage = 'Authentication required. Please log in and try again.'
      } else if (err.response.status === 400) {
        errorMessage = 'Invalid data provided. Please check all required fields.'
      } else if (err.response.status === 500) {
        errorMessage = 'Server error occurred. Please try again later.'
      } else {
        errorMessage = `Server error (${err.response.status}). Please try again.`
      }
      
      console.error('Server response:', err.response.data)
    } else if (err.request) {
      // Request was made but no response received
      errorMessage = 'Network error. Please check your connection and try again.'
      console.error('No response received:', err.request)
    } else {
      // Something else happened
      errorMessage = `Unexpected error: ${err.message}`
      console.error('Error message:', err.message)
    }
    
    error('Preview Generation Error', errorMessage)
  } finally {
    isGeneratingDocument.value = false
  }
}

</script>

<style scoped>
/* Hide scrollbar for Chrome, Safari and Opera */
nav::-webkit-scrollbar {
  display: none;
}

.phase-card {
  @apply shadow-sm border border-gray-200;
}

.text-primary {
  @apply text-purple-600;
}

.text-muted-foreground {
  @apply text-gray-500;
}

.text-success {
  @apply text-green-500;
}

.text-warning {
  @apply text-yellow-500;
}

.text-destructive {
  @apply text-red-500;
}

.border-border {
  @apply border-gray-200;
}

.bg-card {
  @apply bg-white;
}

.text-card-foreground {
  @apply text-gray-900;
}

.bg-background {
  @apply bg-white;
}

.border-input {
  @apply border-gray-300;
}

.ring-offset-background {
  @apply ring-offset-white;
}

.focus-visible\:ring-ring:focus-visible {
  @apply ring-purple-500;
}

.bg-primary {
  @apply bg-purple-600;
}

.text-primary-foreground {
  @apply text-white;
}

.hover\:bg-primary\/90:hover {
  @apply bg-purple-700;
}

.bg-secondary {
  @apply bg-gray-100;
}

.text-secondary-foreground {
  @apply text-gray-900;
}

.hover\:bg-secondary\/80:hover {
  @apply bg-gray-200;
}

.bg-destructive {
  @apply bg-red-600;
}

.text-destructive-foreground {
  @apply text-white;
}

.hover\:bg-destructive\/90:hover {
  @apply bg-red-700;
}

.bg-accent {
  @apply bg-gray-100;
}

.text-accent-foreground {
  @apply text-gray-900;
}

.hover\:bg-accent:hover {
  @apply bg-gray-100;
}

.hover\:text-accent-foreground:hover {
  @apply text-gray-900;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Drag and drop styles */
.cursor-grab {
  cursor: grab;
}

.cursor-grab:active {
  cursor: grabbing;
}

.cursor-move {
  cursor: move;
}

/* Drag handle hover effect */
.cursor-grab:hover svg {
  transform: scale(1.1);
  transition: transform 0.2s ease;
}

/* Dragging state */
[draggable="true"]:hover {
  border-color: #93c5fd;
}

/* Drag over state */
.border-blue-500 {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Data Type Classification Toggle Styles */
.rfp-data-type-circle-toggle-wrapper {
  align-items: center !important;
  margin-left: 12px !important;
  padding: 4px 8px !important;
  background-color: white !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 16px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
  visibility: visible !important;
  opacity: 1 !important;
  position: relative !important;
  z-index: 1 !important;
  flex-shrink: 0 !important;
}

.rfp-data-type-circle-toggle {
  display: flex !important;
  align-items: center !important;
  gap: 4px !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.rfp-circle-option {
  width: 14px !important;
  height: 14px !important;
  border-radius: 50% !important;
  border: 1.5px solid #d1d5db !important;
  background-color: white !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.3s ease !important;
  position: relative !important;
  visibility: visible !important;
  opacity: 1 !important;
  flex-shrink: 0 !important;
}

.rfp-circle-option:hover {
  transform: scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12) !important;
}

.rfp-circle-inner {
  width: 0 !important;
  height: 0 !important;
  border-radius: 50% !important;
  transition: all 0.3s ease !important;
  background-color: transparent !important;
}

.rfp-circle-option.active .rfp-circle-inner {
  width: 9px !important;
  height: 9px !important;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.2) !important;
}

/* Personal Circle - Blue */
.rfp-circle-option.rfp-personal-circle {
  border: 1.5px solid #4f7cff !important;
}

.rfp-circle-option.rfp-personal-circle.active {
  border: 1.5px solid #4f7cff !important;
  background-color: rgba(79, 124, 255, 0.1) !important;
  box-shadow: 0 0 6px rgba(79, 124, 255, 0.2) !important;
}

.rfp-circle-option.rfp-personal-circle.active .rfp-circle-inner {
  background-color: #4f7cff !important;
  box-shadow: 0 0 4px rgba(79, 124, 255, 0.35) !important;
}

/* Confidential Circle - Red */
.rfp-circle-option.rfp-confidential-circle {
  border: 1.5px solid #e63946 !important;
}

.rfp-circle-option.rfp-confidential-circle.active {
  border: 1.5px solid #e63946 !important;
  background-color: rgba(230, 57, 70, 0.1) !important;
  box-shadow: 0 0 6px rgba(230, 57, 70, 0.2) !important;
}

.rfp-circle-option.rfp-confidential-circle.active .rfp-circle-inner {
  background-color: #e63946 !important;
  box-shadow: 0 0 4px rgba(230, 57, 70, 0.35) !important;
}

/* Regular Circle - Grey */
.rfp-circle-option.rfp-regular-circle {
  border: 1.5px solid #6c757d !important;
}

.rfp-circle-option.rfp-regular-circle.active {
  border: 1.5px solid #6c757d !important;
  background-color: rgba(108, 117, 125, 0.1) !important;
  box-shadow: 0 0 6px rgba(108, 117, 125, 0.2) !important;
}

.rfp-circle-option.rfp-regular-circle.active .rfp-circle-inner {
  background-color: #6c757d !important;
  box-shadow: 0 0 4px rgba(108, 117, 125, 0.35) !important;
}
/* Auto-adjusting tabs container */
.tab-container {
  width: 100%;
  gap: 0;
  min-width: 0;
}

/* Tab button auto-adjustment - distributes evenly based on available space */
.tab-button {
  flex: 1 1 0%;
  min-width: 0;
  /* Dynamically calculate minimum width based on tab count to ensure cross button visibility */
  /* Formula: (100% container - padding) / tab count, with minimum of 120px */
  min-width: clamp(120px, calc((100% - 16px) / max(var(--tab-count, 6), 1)), 220px);
  max-width: 100%;
  box-sizing: border-box;
  transition: min-width 0.2s ease;
}

/* Ensure cross button is always visible */
.tab-close {
  min-width: 24px;
  min-height: 24px;
  flex-shrink: 0;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.tab-button:hover .tab-close {
  opacity: 1;
}

/* Text truncation for auto-adjusting tabs */
.tab-text {
  min-width: 0;
  flex: 1 1 auto;
}

.tab-label,
.tab-description {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .tab-button {
    min-width: clamp(100px, calc((100% - 12px) / max(var(--tab-count, 6), 1)), 180px);
    padding-left: 0.5rem;
    padding-right: 0.5rem;
  }
  
  .tab-number {
    min-width: 24px;
    min-height: 24px;
  }
  
  .tab-label {
    font-size: 0.75rem;
  }
  
  .tab-description {
    font-size: 0.625rem;
  }
}

/* Ensure tabs don't overflow container */
.tab-container {
  max-width: 100%;
  overflow: hidden;
}

/* When tabs are too many, allow horizontal scroll with smooth behavior */
@media (max-width: 768px) {
  nav {
    overflow-x: auto;
    scroll-behavior: smooth;
  }
  
  .tab-button {
    flex: 0 0 auto;
    min-width: 120px;
  }
}

/* Fine-tune for very wide screens */
@media (min-width: 1536px) {
  .tab-button {
    max-width: 280px;
  }
}
</style>
