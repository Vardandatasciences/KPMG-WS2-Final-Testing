<template>
  <div class="vendor-portal-standalone">
    <div class="w-full space-y-6 px-4 sm:px-6 lg:px-8">
    <!-- Test Mode Navigation (only shown on test routes) -->
    <div v-if="isTestMode" class="min-h-screen bg-gray-50 flex items-center justify-center">
      <div class="max-w-md mx-auto bg-white rounded-lg shadow-lg p-8">
        <div class="text-center">
          <h1 class="text-2xl font-bold text-gray-900 mb-4">Vendor Portal Test</h1>
          <p class="text-gray-600 mb-6">
            Click the button below to view the Vendor Portal UI
          </p>
          
          <div class="space-y-4">
            <router-link 
              to="/test-vendor-portal" 
              class="block w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              View Vendor Portal (Direct)
            </router-link>
            
            <router-link 
              to="/vendor-portal/test-token-123" 
              class="block w-full bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors"
            >
              View Vendor Portal (With Token)
            </router-link>
            
            <div class="text-sm text-gray-500 mt-4">
              <p><strong>Direct URL:</strong> <code>/test-vendor-portal</code></p>
              <p><strong>With Token:</strong> <code>/vendor-portal/test-token-123</code></p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Vendor Portal Content (hidden in test mode) -->
    <div v-else>
      <!-- Loading overlay -->
      <div v-if="isLoading" class="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        <div class="text-center">
          <Loader2 class="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p class="text-gray-600">Loading RFP details...</p>
        </div>
      </div>
      
      <!-- Floating Action Buttons -->
      <div class="fixed right-6 top-24 z-40 flex flex-col gap-3">
        <div class="relative">
          <button
            type="button"
            @click="toggleRightPanel"
            class="bg-white border-2 border-blue-500 text-blue-600 rounded-full p-3 shadow-lg hover:bg-blue-50 transition-all hover:scale-110"
            :title="rightPanelOpen ? 'Close Panel' : 'View RFP Details & Documents'"
          >
            <FileText v-if="!rightPanelOpen" class="h-6 w-6" />
            <X v-else class="h-6 w-6" />
          </button>
          <!-- Badge for document count -->
          <span 
            v-if="!rightPanelOpen && rfpDocTabs.length > 0"
            class="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center"
          >
            {{ rfpDocTabs.length }}
          </span>
        </div>
        <!-- Tooltip -->
        <div 
          v-if="!rightPanelOpen"
          class="absolute right-16 top-2 bg-gray-900 text-white text-sm px-3 py-2 rounded-lg shadow-lg whitespace-nowrap opacity-0 hover:opacity-100 transition-opacity pointer-events-none"
        >
          📄 View RFP Details & Documents
        </div>
      </div>

      <!-- Preview Mode Banner -->
      <div
        v-if="previewMode"
        class="mt-6 mb-6 flex items-start gap-3 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-blue-900"
      >
        <AlertCircle class="h-5 w-5 text-blue-600 mt-0.5" />
        <div>
          <p class="text-sm font-semibold">Vendor Preview Mode</p>
          <p class="text-xs text-blue-800">
            This read-only view mirrors the vendor portal experience. Uploads and submissions are disabled.
          </p>
        </div>
        <button
          v-if="props.previewPayload"
          type="button"
          class="ml-auto inline-flex items-center rounded-md border border-blue-200 bg-white px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-50"
          @click="emit('exit-preview')"
        >
          <Icons name="arrow-left" class="mr-1 h-3.5 w-3.5" />
          Back to Builder
        </button>
      </div>

      <!-- Custom Fields for Team Section -->
      <div v-if="categoryCustomFieldPanelOpen.team" class="mt-6 border border-blue-200 rounded-lg p-5 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h5 class="text-sm font-semibold text-blue-900">Custom Team Fields</h5>
            <p class="text-xs text-blue-800">Capture extra details about your team.</p>
          </div>
        </div>
        <div class="bg-white border border-blue-300 rounded-lg p-4 space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
            <div class="md:col-span-3 space-y-1">
              <label class="text-xs font-medium text-blue-900">Field Label *</label>
              <input v-model="newCustomField.label" type="text" placeholder="e.g., Team Certification" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'team'" />
            </div>
            <div class="md:col-span-2 space-y-1">
              <label class="text-xs font-medium text-blue-900">Data Type *</label>
              <select v-model="newCustomField.type" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @change="newCustomField.value = newCustomField.type === 'file' ? null : ''; newCustomField.category = 'team'">
                <option v-for="type in customFieldTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
              </select>
            </div>
            <div class="md:col-span-6 space-y-1">
              <label class="text-xs font-medium text-blue-900">Value *</label>
              <input v-if="newCustomField.type === 'text'" v-model="newCustomField.value" type="text" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'team'" />
              <textarea v-else-if="newCustomField.type === 'textarea'" v-model="newCustomField.value" rows="2" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none" @focus="newCustomField.category = 'team'" />
              <input v-else-if="newCustomField.type === 'number' || newCustomField.type === 'decimal'" v-model.number="newCustomField.value" type="number" :step="newCustomField.type === 'decimal' ? 0.01 : 1" placeholder="Enter number" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'team'" />
              <input v-else-if="newCustomField.type === 'date'" v-model="newCustomField.value" type="date" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'team'" />
              <input v-else-if="newCustomField.type === 'email'" v-model="newCustomField.value" type="email" placeholder="Enter email" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'team'" />
              <input v-else-if="newCustomField.type === 'url'" v-model="newCustomField.value" type="url" placeholder="Enter URL" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'team'" />
              <div v-else-if="newCustomField.type === 'file'" class="space-y-2">
                <input type="file" @change="(e) => handleNewCustomFieldFileChange(e, 'team')" class="block w-full text-sm text-gray-900 border border-blue-200 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                <div v-if="newCustomField.fileData" class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded p-2">
                  <span class="text-xs text-gray-700">{{ newCustomField.fileData.fileName }}</span>
                  <button type="button" @click="newCustomField.fileData = null; newCustomField.value = null" class="text-xs text-red-600 hover:text-red-800">Remove</button>
                </div>
              </div>
              <input v-else v-model="newCustomField.value" type="text" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus-border-blue-500 text-sm" @focus="newCustomField.category = 'team'" />
            </div>
            <div class="md:col-span-1">
              <button type="button" @click="addCustomFieldWithValue('team')" class="w-full px-4 py-2.5 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors">Add</button>
            </div>
          </div>
        </div>
        <div v-if="categoryCustomFields.team.length > 0" class="space-y-2">
          <p class="text-xs font-semibold text-blue-900">Custom fields added:</p>
          <div class="space-y-2">
            <template v-for="field in categoryCustomFields.team" :key="field.id">
              <div v-if="!isCategoryFieldHidden(field.id, 'team')" class="bg-white border border-blue-200 rounded-lg p-3">
                <div class="flex items-start justify-between gap-3">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <p class="text-sm font-semibold text-gray-900">{{ field.label }}</p>
                      <span class="text-xs text-gray-500">({{ getCustomFieldTypeLabel(field.type) }})</span>
                      <span class="text-xs text-blue-600 font-mono">Key: {{ field.name }}</span>
                    </div>
                    <div class="mt-2">
                      <p v-if="field.type !== 'file'" class="text-sm text-gray-700"><span class="font-medium">Value:</span> <span class="ml-1">{{ formatCustomFieldValue(field, 'team') }}</span></p>
                      <div v-else-if="getCustomFieldValue(field, 'team')" class="flex items-center gap-2">
                        <span class="text-sm text-gray-700 font-medium">File:</span>
                        <span class="text-sm text-gray-600">{{ getCustomFieldValue(field, 'team')?.fileName || 'File uploaded' }}</span>
                        <button type="button" @click="downloadCustomFieldFile(field, 'team')" class="text-xs text-blue-600 hover:text-blue-800">Download</button>
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <!-- X button to hide field (for non-mandatory fields) -->
                    <button
                      v-if="!field.required"
                      type="button"
                      @click="hideCategoryField(field.id, 'team')"
                      class="text-red-600 hover:text-red-800 transition-colors"
                      title="Remove this field"
                    >
                      <X class="h-4 w-4" :class="{ 'opacity-50': !getCustomFieldValue(field, 'team'), 'opacity-100': getCustomFieldValue(field, 'team') }" />
                    </button>
                    <!-- Remove button to delete field completely -->
                    <button type="button" @click="removeCustomField(field.id, 'team')" class="text-xs text-red-600 hover:text-red-800 font-medium px-2 py-1">Delete</button>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Full-Width Progress Bar -->
      <div class="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden mb-6">
        <div class="px-6 py-4 bg-gradient-to-r from-purple-50 to-indigo-50 border-b border-gray-100">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-lg font-semibold text-gray-900">Submission Progress</h3>
            <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
              {{ overallProgress }}% Complete
            </span>
          </div>
          <!-- Main Progress Bar -->
          <div class="relative w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-r from-purple-600 via-purple-500 to-indigo-600 rounded-full transition-all duration-500 ease-out" 
                 :style="{ width: overallProgress + '%' }"></div>
            <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-full"></div>
          </div>
        </div>
        <!-- Horizontal Progress Items -->
        <div class="px-6 py-4">
          <div class="flex items-center justify-between gap-6">
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-green-500"></div>
                <span class="text-sm font-medium text-gray-700">Company</span>
                <span class="text-sm font-bold text-green-600">{{ completionStatus.company }}%</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-blue-500"></div>
                <span class="text-sm font-medium text-gray-700">Financial</span>
                <span class="text-sm font-bold text-blue-600">{{ completionStatus.financial }}%</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-orange-500"></div>
                <span class="text-sm font-medium text-gray-700">Responses</span>
                <span class="text-sm font-bold text-orange-600">{{ completionStatus.responses }}%</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-gray-500"></div>
                <span class="text-sm font-medium text-gray-700">Documents</span>
                <span class="text-sm font-bold text-gray-600">{{ completionStatus.documents }}%</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-purple-500"></div>
                <span class="text-sm font-medium text-gray-700">Team</span>
                <span class="text-sm font-bold text-purple-600">{{ completionStatus.personnel }}%</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-2">
                <div class="w-3 h-3 rounded-full bg-indigo-500"></div>
                <span class="text-sm font-medium text-gray-700">Compliance</span>
                <span class="text-sm font-bold text-indigo-600">{{ completionStatus.compliance }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Full-Width Form Layout -->
      <div class="max-w-7xl mx-auto">
        <!-- Form Content -->
      <!-- Header -->
    <div class="text-center space-y-4 mb-6">
      <div class="flex justify-center">
        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 border border-green-200">
          {{ rfpInfo.rfpNumber }}
        </span>
          </div>
      <h1 class="text-3xl font-bold tracking-tight text-gray-900">{{ rfpInfo.rfpTitle }}</h1>
      <p class="text-gray-600">
        Please complete all sections below to submit your proposal.
      </p>
      <div class="flex items-center justify-center gap-4 text-sm">
        <div class="flex items-center gap-1">
          <Clock class="h-4 w-4 text-yellow-600" />
          <span class="text-gray-700">Deadline: {{ rfpInfo.deadline }}</span>
            </div>
        <div class="flex items-center gap-1">
          <Building2 class="h-4 w-4 text-gray-500" />
          <span class="text-gray-700">Budget: {{ rfpInfo.budget }}</span>
        </div>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm mb-6 overflow-hidden">
      <div class="flex border-b border-gray-200 overflow-x-auto">
        <button
          v-for="tab in formTabs"
          :key="tab.id"
          type="button"
          @click="goToTab(tab.id)"
          :class="[
            'flex-1 min-w-[140px] px-4 py-3 text-sm font-medium transition-colors relative',
            activeFormTab === tab.id
              ? 'text-blue-600 bg-blue-50 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
          ]"
        >
          <div class="flex items-center justify-center gap-2">
            <span class="text-lg">{{ tab.icon }}</span>
            <span>{{ tab.label }}</span>
            <CheckCircle2 
              v-if="isTabCompleted(tab.id)" 
              class="h-4 w-4 text-green-600 ml-1" 
            />
          </div>
          <div 
            v-if="activeFormTab === tab.id"
            class="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"
          ></div>
        </button>
      </div>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
    <!-- Company Information -->
    <div v-show="activeFormTab === 'company'">
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center gap-2">
          <Building2 class="h-5 w-5 text-gray-700" />
          <h3 class="text-lg font-semibold text-gray-900">Company Information</h3>
          <CheckCircle2 v-if="completionStatus.company === 100" class="h-4 w-4 text-green-600 ml-auto" />
          <AlertCircle v-else class="h-4 w-4 text-yellow-600" />
          <button
            type="button"
            @click="toggleCategoryFieldPanel('company')"
            class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
          >
            <span class="text-base leading-none">+</span>
            Add Field
          </button>
        </div>
      </div>
      <div class="p-6 space-y-6">
        <!-- Basic Company Details -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Basic Company Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2">
            <label class="text-sm font-medium text-gray-700">Company Name *</label>
              <input 
              v-model="formData.companyName"
              class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter company name"
                required
              />
            </div>
          <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Legal Name *</label>
              <input 
                v-model="formData.legalName"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter legal company name"
                required
              />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Business Type *</label>
              <select 
                v-model="formData.businessType"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Select business type</option>
                <option value="Corporation">Corporation</option>
                <option value="LLC">LLC</option>
                <option value="Partnership">Partnership</option>
                <option value="Sole Proprietorship">Sole Proprietorship</option>
                <option value="Non-Profit">Non-Profit</option>
                <option value="Government">Government</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Industry Sector *</label>
              <input 
                v-model="formData.industrySector"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Technology, Healthcare, Finance"
                required
              />
            </div>
          </div>
        </div>

        <!-- Contact Information -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Contact Information</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Primary Contact Name *</label>
              <input 
              v-model="formData.contactName"
              class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter contact name"
                required
              />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Contact Title *</label>
              <input 
                v-model="formData.contactTitle"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., CEO, Project Manager"
                required
              />
            </div>
          <div class="space-y-2">
            <label class="text-sm font-medium text-gray-700">Email Address *</label>
              <input 
              v-model="formData.email"
                type="email" 
              class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter email address"
                required
            />
          </div>
          <div class="space-y-2">
            <label class="text-sm font-medium text-gray-700">Phone Number *</label>
            <input
              v-model="formData.phone"
                type="tel"
              class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter phone number"
                required
              />
            </div>
        </div>
        </div>

        <!-- Company Details -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Company Details</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-if="!hiddenFields.website" class="space-y-2">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-gray-700">Website</label>
            <button
              type="button"
              @click="hideField('website')"
              class="text-red-600 hover:text-red-800 transition-colors"
              title="Remove this field"
            >
              <X class="h-4 w-4" :class="{ 'opacity-50': !formData.website, 'opacity-100': formData.website }" />
            </button>
          </div>
              <input 
            v-model="formData.website"
                type="url"
            class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="https://www.company.com"
              />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Tax ID / EIN *</label>
              <input 
                v-model="formData.taxId"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter Tax ID or EIN"
                required
              />
            </div>
            <div v-if="!hiddenFields.dunsNumber" class="space-y-2">
              <div class="flex items-center justify-between">
                <label class="text-sm font-medium text-gray-700">DUNS Number</label>
                <button
                  type="button"
                  @click="hideField('dunsNumber')"
                  class="text-red-600 hover:text-red-800 transition-colors"
                  title="Remove this field"
                >
                  <X class="h-4 w-4" :class="{ 'opacity-50': !formData.dunsNumber, 'opacity-100': formData.dunsNumber }" />
                </button>
              </div>
              <input 
                v-model="formData.dunsNumber"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter DUNS number"
              />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Incorporation Date *</label>
              <input 
                v-model="formData.incorporationDate"
                type="date"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>
          </div>
        </div>

        <!-- Custom Fields for Company Section -->
        <div v-if="categoryCustomFieldPanelOpen.company" class="mt-6 pt-6 border-t border-gray-200">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-5 space-y-4">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h5 class="text-sm font-semibold text-blue-900">Add Custom Fields</h5>
                <p class="text-xs text-blue-800">Add additional fields specific to this section. Each field is saved as a key:value pair.</p>
              </div>
            </div>

            <!-- New Field Input Form -->
            <div class="bg-white border border-blue-300 rounded-lg p-4 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                <div class="md:col-span-3 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Field Label *</label>
                  <input
                    v-model="newCustomField.label"
                    type="text"
                    placeholder="e.g., Parent Company"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'company'"
                  />
                </div>
                <div class="md:col-span-2 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Data Type *</label>
                  <select
                    v-model="newCustomField.type"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @change="newCustomField.value = newCustomField.type === 'file' ? null : ''; newCustomField.category = 'company'"
                  >
                    <option v-for="type in customFieldTypes" :key="type.value" :value="type.value">
                      {{ type.label }}
                    </option>
                  </select>
                </div>
                <div class="md:col-span-6 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Value *</label>
                  <input
                    v-if="newCustomField.type === 'text'"
                    v-model="newCustomField.value"
                    type="text"
                    placeholder="Enter value"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'company'"
                  />
                  <textarea
                    v-else-if="newCustomField.type === 'textarea'"
                    v-model="newCustomField.value"
                    rows="2"
                    placeholder="Enter value"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none"
                    @focus="newCustomField.category = 'company'"
                  />
                  <input
                    v-else-if="newCustomField.type === 'number' || newCustomField.type === 'decimal'"
                    v-model.number="newCustomField.value"
                    type="number"
                    :step="newCustomField.type === 'decimal' ? 0.01 : 1"
                    placeholder="Enter number"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'company'"
                  />
                  <input
                    v-else-if="newCustomField.type === 'date'"
                    v-model="newCustomField.value"
                    type="date"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'company'"
                  />
                  <input
                    v-else-if="newCustomField.type === 'email'"
                    v-model="newCustomField.value"
                    type="email"
                    placeholder="Enter email"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'company'"
                  />
                  <input
                    v-else-if="newCustomField.type === 'url'"
                    v-model="newCustomField.value"
                    type="url"
                    placeholder="Enter URL"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'company'"
                  />
                  <div v-else-if="newCustomField.type === 'file'" class="space-y-2">
                    <input
                      type="file"
                      @change="(e) => handleNewCustomFieldFileChange(e, 'company')"
                      class="block w-full text-sm text-gray-900 border border-blue-200 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <div v-if="newCustomField.fileData" class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded p-2">
                      <span class="text-xs text-gray-700">{{ newCustomField.fileData.fileName }}</span>
                      <button
                        type="button"
                        @click="newCustomField.fileData = null; newCustomField.value = null"
                        class="text-xs text-red-600 hover:text-red-800"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                  <input
                    v-else
                    v-model="newCustomField.value"
                    type="text"
                    placeholder="Enter value"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'company'"
                  />
                </div>
                <div class="md:col-span-1">
                  <button
                    type="button"
                    @click="addCustomFieldWithValue('company')"
                    class="w-full px-4 py-2.5 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>

            <!-- Added Custom Fields List -->
            <div v-if="categoryCustomFields.company.length > 0" class="space-y-2">
              <p class="text-xs font-semibold text-blue-900">Custom fields added:</p>
              <div class="space-y-2">
                <template v-for="field in categoryCustomFields.company" :key="field.id">
                  <div
                    v-if="!isCategoryFieldHidden(field.id, 'company')"
                    class="bg-white border border-blue-200 rounded-lg p-3"
                  >
                    <div class="flex items-start justify-between gap-3">
                      <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                          <p class="text-sm font-semibold text-gray-900">{{ field.label }}</p>
                          <span class="text-xs text-gray-500">({{ getCustomFieldTypeLabel(field.type) }})</span>
                          <span class="text-xs text-blue-600 font-mono">Key: {{ field.name }}</span>
                        </div>
                        <div class="mt-2">
                          <p v-if="field.type !== 'file'" class="text-sm text-gray-700">
                            <span class="font-medium">Value:</span> 
                            <span class="ml-1">{{ formatCustomFieldValue(field, 'company') }}</span>
                          </p>
                          <div v-else-if="getCustomFieldValue(field, 'company')" class="flex items-center gap-2">
                            <span class="text-sm text-gray-700 font-medium">File:</span>
                            <span class="text-sm text-gray-600">{{ getCustomFieldValue(field, 'company')?.fileName || 'File uploaded' }}</span>
                            <button
                              type="button"
                              @click="downloadCustomFieldFile(field, 'company')"
                              class="text-xs text-blue-600 hover:text-blue-800"
                            >
                              Download
                            </button>
                          </div>
                        </div>
                      </div>
                      <div class="flex items-center gap-2">
                        <!-- X button to hide field (for non-mandatory fields) -->
                        <button
                          v-if="!field.required"
                          type="button"
                          @click="hideCategoryField(field.id, 'company')"
                          class="text-red-600 hover:text-red-800 transition-colors"
                          title="Remove this field"
                        >
                          <X class="h-4 w-4" :class="{ 'opacity-50': !getCustomFieldValue(field, 'company'), 'opacity-100': getCustomFieldValue(field, 'company') }" />
                        </button>
                        <!-- Remove button to delete field completely -->
                        <button
                          type="button"
                          @click="removeCustomField(field.id, 'company')"
                          class="text-xs text-red-600 hover:text-red-800 font-medium px-2 py-1"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- Company Size & Financials -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Company Size & Financials</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Number of Employees *</label>
              <select 
                v-model="formData.employeeCount"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Select employee count</option>
                <option value="1-10">1-10</option>
                <option value="11-50">11-50</option>
                <option value="51-200">51-200</option>
                <option value="201-500">201-500</option>
                <option value="501-1000">501-1000</option>
                <option value="1000+">1000+</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Annual Revenue *</label>
              <select 
                v-model="formData.annualRevenue"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Select annual revenue</option>
                <option value="0-1M">$0 - $1M</option>
                <option value="1M-5M">$1M - $5M</option>
                <option value="5M-10M">$5M - $10M</option>
                <option value="10M-50M">$10M - $50M</option>
                <option value="50M-100M">$50M - $100M</option>
                <option value="100M+">$100M+</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Company Address -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Company Address</h4>
          <div class="space-y-4">
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Headquarters Address *</label>
              <textarea 
                v-model="formData.headquartersAddress"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter complete address"
                rows="3"
                required
              ></textarea>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700">Country *</label>
                <input 
                  v-model="formData.headquartersCountry"
                  class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter country"
                  required
                />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700">Years in Business *</label>
                <input 
                  v-model="formData.yearsInBusiness"
                  type="number"
                  min="0"
                  class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter years in business"
                  required
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Company Description -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Company Description</h4>
          <div class="space-y-2">
            <label class="text-sm font-medium text-gray-700">Company Description *</label>
            <textarea 
              v-model="formData.companyDescription"
              class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Describe your company, its mission, and key capabilities"
              rows="4"
              required
            ></textarea>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Navigation Buttons -->
    <div class="flex justify-between mt-6">
      <button
        type="button"
        @click="goToPreviousTab"
        disabled
        class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        ← Previous
      </button>
      <button
        type="button"
        @click="goToNextTab"
        class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        Next: Financial →
      </button>
    </div>
    </div>

    <!-- Financial Information -->
    <div v-show="activeFormTab === 'financial'">
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center gap-2">
          <DollarSign class="h-5 w-5 text-gray-700" />
          <h3 class="text-lg font-semibold text-gray-900">Financial Information</h3>
          <CheckCircle2 v-if="completionStatus.financial === 100" class="h-4 w-4 text-green-600 ml-auto" />
          <AlertCircle v-else class="h-4 w-4 text-yellow-600" />
          <button
            type="button"
            @click="toggleCategoryFieldPanel('financial')"
            class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
          >
            <span class="text-base leading-none">+</span>
            Add Field
          </button>
        </div>
      </div>
      <div class="p-6 space-y-6">
        <!-- Proposed Value -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Proposed Value</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Total Proposed Value *</label>
              <div class="relative">
                <span class="absolute left-3 top-3 text-gray-500">$</span>
                <input 
                  v-model="formData.proposedValue"
                  type="number"
                  step="0.01"
                  min="0"
                  class="w-full pl-8 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0.00"
                  required
                />
              </div>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Currency *</label>
              <select 
                v-model="formData.currency"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Select currency</option>
                <option value="USD">USD - US Dollar</option>
                <option value="EUR">EUR - Euro</option>
                <option value="GBP">GBP - British Pound</option>
                <option value="CAD">CAD - Canadian Dollar</option>
                <option value="AUD">AUD - Australian Dollar</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Pricing Breakdown -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Pricing Breakdown</h4>
          <div class="space-y-4">
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Detailed Pricing Breakdown *</label>
              <textarea 
                v-model="formData.pricingBreakdown"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Provide detailed breakdown of costs, including labor, materials, overhead, profit margin, etc."
                rows="4"
                required
              ></textarea>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700">Payment Terms *</label>
                <select 
                  v-model="formData.paymentTerms"
                  class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select payment terms</option>
                  <option value="Net 30">Net 30</option>
                  <option value="Net 45">Net 45</option>
                  <option value="Net 60">Net 60</option>
                  <option value="50% Upfront, 50% on completion">50% Upfront, 50% on completion</option>
                  <option value="Milestone-based">Milestone-based</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700">Project Duration (Months) *</label>
                <input 
                  v-model="formData.projectDuration"
                  type="number"
                  min="1"
                  class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter duration in months"
                  required
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Financial Stability -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Financial Stability</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div v-if="!hiddenFields.creditRating" class="space-y-2">
              <div class="flex items-center justify-between">
                <label class="text-sm font-medium text-gray-700">Credit Rating</label>
                <button
                  type="button"
                  @click="hideField('creditRating')"
                  class="text-red-600 hover:text-red-800 transition-colors"
                  title="Remove this field"
                >
                  <X class="h-4 w-4" :class="{ 'opacity-50': !formData.creditRating, 'opacity-100': formData.creditRating }" />
                </button>
              </div>
              <select 
                v-model="formData.creditRating"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select credit rating</option>
                <option value="AAA">AAA</option>
                <option value="AA">AA</option>
                <option value="A">A</option>
                <option value="BBB">BBB</option>
                <option value="BB">BB</option>
                <option value="B">B</option>
                <option value="CCC">CCC</option>
                <option value="Not Rated">Not Rated</option>
              </select>
            </div>
            <div v-if="!hiddenFields.insuranceCoverage" class="space-y-2">
              <div class="flex items-center justify-between">
                <label class="text-sm font-medium text-gray-700">Insurance Coverage Amount</label>
                <button
                  type="button"
                  @click="hideField('insuranceCoverage')"
                  class="text-red-600 hover:text-red-800 transition-colors"
                  title="Remove this field"
                >
                  <X class="h-4 w-4" :class="{ 'opacity-50': !formData.insuranceCoverage, 'opacity-100': formData.insuranceCoverage }" />
                </button>
              </div>
              <div class="relative">
                <span class="absolute left-3 top-3 text-gray-500">$</span>
                <input 
                  v-model="formData.insuranceCoverage"
                  type="number"
                  step="1000"
                  min="0"
                  class="w-full pl-8 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Custom Fields for Financial Section -->
        <div v-if="categoryCustomFieldPanelOpen.financial" class="mt-6 pt-6 border-t border-gray-200">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-5 space-y-4">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h5 class="text-sm font-semibold text-blue-900">Add Custom Fields</h5>
                <p class="text-xs text-blue-800">Add additional financial fields. Each field is saved as a key:value pair.</p>
              </div>
            </div>
            <div class="bg-white border border-blue-300 rounded-lg p-4 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                <div class="md:col-span-3 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Field Label *</label>
                  <input v-model="newCustomField.label" type="text" placeholder="e.g., Bank Name" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'financial'" />
                </div>
                <div class="md:col-span-2 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Data Type *</label>
                  <select v-model="newCustomField.type" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @change="newCustomField.value = newCustomField.type === 'file' ? null : ''; newCustomField.category = 'financial'">
                    <option v-for="type in customFieldTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
                  </select>
                </div>
                <div class="md:col-span-6 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Value *</label>
                  <input v-if="newCustomField.type === 'text'" v-model="newCustomField.value" type="text" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'financial'" />
                  <textarea v-else-if="newCustomField.type === 'textarea'" v-model="newCustomField.value" rows="2" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none" @focus="newCustomField.category = 'financial'" />
                  <input v-else-if="newCustomField.type === 'number' || newCustomField.type === 'decimal'" v-model.number="newCustomField.value" type="number" :step="newCustomField.type === 'decimal' ? 0.01 : 1" placeholder="Enter number" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'financial'" />
                  <input v-else-if="newCustomField.type === 'date'" v-model="newCustomField.value" type="date" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'financial'" />
                  <input v-else-if="newCustomField.type === 'email'" v-model="newCustomField.value" type="email" placeholder="Enter email" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'financial'" />
                  <input v-else-if="newCustomField.type === 'url'" v-model="newCustomField.value" type="url" placeholder="Enter URL" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'financial'" />
                  <div v-else-if="newCustomField.type === 'file'" class="space-y-2">
                    <input type="file" @change="(e) => handleNewCustomFieldFileChange(e, 'financial')" class="block w-full text-sm text-gray-900 border border-blue-200 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                    <div v-if="newCustomField.fileData" class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded p-2">
                      <span class="text-xs text-gray-700">{{ newCustomField.fileData.fileName }}</span>
                      <button type="button" @click="newCustomField.fileData = null; newCustomField.value = null" class="text-xs text-red-600 hover:text-red-800">Remove</button>
                    </div>
                  </div>
                  <input v-else v-model="newCustomField.value" type="text" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'financial'" />
                </div>
                <div class="md:col-span-1">
                  <button type="button" @click="addCustomFieldWithValue('financial')" class="w-full px-4 py-2.5 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors">Add</button>
                </div>
              </div>
            </div>
            <div v-if="categoryCustomFields.financial.length > 0" class="space-y-2">
              <p class="text-xs font-semibold text-blue-900">Custom fields added:</p>
              <div class="space-y-2">
                <template v-for="field in categoryCustomFields.financial" :key="field.id">
                  <div v-if="!isCategoryFieldHidden(field.id, 'financial')" class="bg-white border border-blue-200 rounded-lg p-3">
                    <div class="flex items-start justify-between gap-3">
                      <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                          <p class="text-sm font-semibold text-gray-900">{{ field.label }}</p>
                          <span class="text-xs text-gray-500">({{ getCustomFieldTypeLabel(field.type) }})</span>
                          <span class="text-xs text-blue-600 font-mono">Key: {{ field.name }}</span>
                        </div>
                        <div class="mt-2">
                          <p v-if="field.type !== 'file'" class="text-sm text-gray-700"><span class="font-medium">Value:</span> <span class="ml-1">{{ formatCustomFieldValue(field, 'financial') }}</span></p>
                          <div v-else-if="getCustomFieldValue(field, 'financial')" class="flex items-center gap-2">
                            <span class="text-sm text-gray-700 font-medium">File:</span>
                            <span class="text-sm text-gray-600">{{ getCustomFieldValue(field, 'financial')?.fileName || 'File uploaded' }}</span>
                            <button type="button" @click="downloadCustomFieldFile(field, 'financial')" class="text-xs text-blue-600 hover:text-blue-800">Download</button>
                          </div>
                        </div>
                      </div>
                      <div class="flex items-center gap-2">
                        <!-- X button to hide field (for non-mandatory fields) -->
                        <button
                          v-if="!field.required"
                          type="button"
                          @click="hideCategoryField(field.id, 'financial')"
                          class="text-red-600 hover:text-red-800 transition-colors"
                          title="Remove this field"
                        >
                          <X class="h-4 w-4" :class="{ 'opacity-50': !getCustomFieldValue(field, 'financial'), 'opacity-100': getCustomFieldValue(field, 'financial') }" />
                        </button>
                        <!-- Remove button to delete field completely -->
                        <button type="button" @click="removeCustomField(field.id, 'financial')" class="text-xs text-red-600 hover:text-red-800 font-medium px-2 py-1">Delete</button>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
          </div>
        </div>

    <!-- Tab Navigation Buttons -->
    <div class="flex justify-between mt-6">
      <button
        type="button"
        @click="goToPreviousTab"
        class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        ← Previous: Company
      </button>
      <button
        type="button"
        @click="goToNextTab"
        class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        Next: RFP Responses →
      </button>
    </div>
    </div>

    <!-- RFP Responses -->
    <div v-show="activeFormTab === 'responses'">
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center gap-2">
          <FileText class="h-5 w-5 text-gray-700" />
          <h3 class="text-lg font-semibold text-gray-900">RFP Response Sections</h3>
          <AlertCircle v-if="completionStatus.responses < 100" class="h-4 w-4 text-yellow-600 ml-auto" />
        </div>
                </div>
      <div class="p-6 space-y-6">
        <!-- Show message if no criteria are loaded -->
        <div v-if="!evaluationCriteria || evaluationCriteria.length === 0" class="text-center p-8 bg-gray-50 rounded-lg border border-gray-200">
          <AlertCircle class="h-12 w-12 text-gray-400 mx-auto mb-3" />
          <p class="text-sm font-medium text-gray-700 mb-2">No evaluation criteria available</p>
          <p class="text-xs text-gray-500">
            The RFP evaluation criteria are being loaded. If this message persists, the RFP may not have any evaluation criteria defined.
          </p>
          <button 
            type="button"
            @click="fetchEvaluationCriteria"
            class="mt-4 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            ↻ Retry Loading Criteria
          </button>
        </div>
        
        <div v-for="criteria in (evaluationCriteria || [])" :key="criteria.id" class="space-y-3">
          <div class="flex items-center justify-between">
                <div>
              <h4 class="font-semibold flex items-center gap-2 text-gray-900">
                {{ criteria.title }}
                <span v-if="criteria.required" class="text-red-500">*</span>
              </h4>
              <p class="text-sm text-gray-600">{{ criteria.description }}</p>
            </div>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 border border-gray-300">
              {{ criteria.weight }}% weight
            </span>
                </div>
          
                <div class="space-y-3">
            <RichResponseEditor
              :model-value="getCriteriaResponse(criteria.id)"
              :placeholder="criteria.type === 'pricing'
                ? 'Provide detailed pricing breakdown including costs, phases, and payment terms'
                : `Enter your response for ${criteria.title}`"
              :disabled="submissionStatus === 'SUBMITTED'"
              :upload-attachment="(file, options) => uploadResponseAttachment(criteria.id, file, options)"
              @update:modelValue="value => setCriteriaResponse(criteria.id, value)"
 
              @blur="handleAutoSave"
            />
            <div v-if="criteria.type === 'pricing'" class="text-sm text-gray-500">
              <p>You can embed pricing tables directly in the editor or attach supplementary pricing documents.</p>
 
              </div>
      
          </div>
        </div>
        
        <!-- Dynamic Response Fields based on RFP Type -->
        <div class="mt-8 pt-8 border-t border-gray-200">
          <div class="mb-6">
            <h4 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <FileText class="h-5 w-5" />
              Additional Information
            </h4>
            <p class="text-sm text-gray-600 mt-1">Please provide the following additional details specific to this RFP type.</p>
          </div>

          <!-- Custom Field Builder - Inline Label + Type + Value -->
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-5 space-y-4">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h5 class="text-sm font-semibold text-blue-900">Add Custom Fields</h5>
                <p class="text-xs text-blue-800">Add custom fields with label, data type, and value. Each field is saved as a key:value pair.</p>
              </div>
            </div>

            <!-- New Field Input Form -->
            <div class="bg-white border border-blue-300 rounded-lg p-4 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                <!-- Field Label -->
                <div class="md:col-span-3 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Field Label *</label>
                  <input
                    v-model="newCustomField.label"
                    type="text"
                    placeholder="e.g., Certificate Number"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'responses'"
                  />
                </div>
                
                <!-- Data Type -->
                <div class="md:col-span-2 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Data Type *</label>
                  <select
                    v-model="newCustomField.type"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @change="newCustomField.value = newCustomField.type === 'file' ? null : ''; newCustomField.category = 'responses'"
                  >
                    <option v-for="type in customFieldTypes" :key="type.value" :value="type.value">
                      {{ type.label }}
                    </option>
                  </select>
                </div>
                
                <!-- Value Input - Dynamic based on type -->
                <div class="md:col-span-6 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Value *</label>
                  
                  <!-- Text Input -->
                  <input
                    v-if="newCustomField.type === 'text'"
                    v-model="newCustomField.value"
                    type="text"
                    placeholder="Enter value"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'responses'"
                  />
                  
                  <!-- Textarea -->
                  <textarea
                    v-else-if="newCustomField.type === 'textarea'"
                    v-model="newCustomField.value"
                    rows="2"
                    placeholder="Enter value"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none"
                    @focus="newCustomField.category = 'responses'"
                  />
                  
                  <!-- Number Input -->
                  <input
                    v-else-if="newCustomField.type === 'number' || newCustomField.type === 'decimal'"
                    v-model.number="newCustomField.value"
                    type="number"
                    :step="newCustomField.type === 'decimal' ? 0.01 : 1"
                    placeholder="Enter number"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'responses'"
                  />
                  
                  <!-- Date Input -->
                  <input
                    v-else-if="newCustomField.type === 'date'"
                    v-model="newCustomField.value"
                    type="date"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'responses'"
                  />
                  
                  <!-- Email Input -->
                  <input
                    v-else-if="newCustomField.type === 'email'"
                    v-model="newCustomField.value"
                    type="email"
                    placeholder="Enter email"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'responses'"
                  />
                  
                  <!-- URL Input -->
                  <input
                    v-else-if="newCustomField.type === 'url'"
                    v-model="newCustomField.value"
                    type="url"
                    placeholder="Enter URL"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'responses'"
                  />
                  
                  <!-- File Upload -->
                  <div v-else-if="newCustomField.type === 'file'" class="space-y-2">
                    <input
                      type="file"
                      @change="(event) => handleNewCustomFieldFileChange(event, 'responses')"
                      class="block w-full text-sm text-gray-900 border border-blue-200 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    <div v-if="newCustomField.fileData" class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded p-2">
                      <span class="text-xs text-gray-700">{{ newCustomField.fileData.fileName }}</span>
                      <button
                        type="button"
                        @click="newCustomField.fileData = null; newCustomField.value = null"
                        class="text-xs text-red-600 hover:text-red-800"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                  
                  <!-- Default Text -->
                  <input
                    v-else
                    v-model="newCustomField.value"
                    type="text"
                    placeholder="Enter value"
                    class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                    @focus="newCustomField.category = 'responses'"
                  />
                </div>
                
                <!-- Add Button -->
                <div class="md:col-span-1">
                  <button
                    type="button"
                    @click="addCustomFieldWithValue('responses')"
                    class="w-full px-4 py-2.5 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
                  >
                    Add
                  </button>
                </div>
              </div>
            </div>

            <!-- Added Custom Fields List -->
            <div v-if="customDynamicFields.length > 0" class="space-y-2">
              <p class="text-xs font-semibold text-blue-900">Custom fields added (key:value pairs):</p>
              <div class="space-y-2">
                <template v-for="field in customDynamicFields" :key="field.id">
                  <div
                    v-if="!isDynamicFieldHidden(field.id) && !isDynamicFieldHidden(field._uniqueKey)"
                    class="bg-white border border-blue-200 rounded-lg p-3"
                  >
                  <div class="flex items-start justify-between gap-3">
                    <div class="flex-1">
                      <div class="flex items-center gap-2 mb-1">
                        <p class="text-sm font-semibold text-gray-900">{{ field.label }}</p>
                        <span class="text-xs text-gray-500">({{ getCustomFieldTypeLabel(field.type) }})</span>
                        <span class="text-xs text-blue-600 font-mono">Key: {{ field.name }}</span>
                      </div>
                      <div class="mt-2">
                        <!-- Display value based on type -->
                        <p v-if="field.type !== 'file'" class="text-sm text-gray-700">
                          <span class="font-medium">Value:</span> 
                          <span class="ml-1">{{ formatCustomFieldValue(field) }}</span>
                        </p>
                        <div v-else-if="getCustomFieldValue(field)" class="flex items-center gap-2">
                          <span class="text-sm text-gray-700 font-medium">File:</span>
                          <span class="text-sm text-gray-600">{{ getCustomFieldValue(field)?.fileName || 'File uploaded' }}</span>
                          <button
                            type="button"
                            @click="downloadCustomFieldFile(field)"
                            class="text-xs text-blue-600 hover:text-blue-800"
                          >
                            Download
                          </button>
                        </div>
                      </div>
                    </div>
                    <div class="flex items-center gap-2">
                      <!-- Remove button to hide field (for non-mandatory fields) -->
                      <button
                        v-if="!field.required"
                        type="button"
                        @click="hideDynamicField(field.id || field._uniqueKey, null)"
                        class="text-red-600 hover:text-red-800 transition-colors"
                        title="Remove this field"
                      >
                        <X class="h-4 w-4" :class="{ 'opacity-50': !getCustomFieldValue(field), 'opacity-100': getCustomFieldValue(field) }" />
                      </button>
                      <!-- Remove button to delete custom field completely -->
                      <button
                        type="button"
                        @click="removeCustomField(field.id)"
                        class="text-xs text-red-600 hover:text-red-800 font-medium px-2 py-1"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  </div>
                </template>
              </div>
            </div>
          </div>

          <!-- RFP-defined Dynamic Fields (from backend) -->
          <div v-if="dynamicResponseFields.length === 0 && customDynamicFields.length === 0" class="mt-6 p-4 bg-white border border-dashed border-gray-300 rounded-lg">
            <p class="text-sm text-gray-700">
              No predefined fields available for this RFP type yet. Use the builder above to add your own custom fields with values.
            </p>
          </div>
          
          <div v-if="dynamicResponseFields.length > 0" class="space-y-6 mt-6">
            <p class="text-sm font-semibold text-gray-700">RFP-Defined Fields:</p>
            <template v-for="(field, index) in dynamicResponseFields" :key="resolveFieldKey(field, index)">
              <div v-if="!isDynamicFieldHidden(resolveFieldKey(field, index)) || field.required" class="space-y-2">
              <div class="flex items-center justify-between">
                <label class="text-sm font-medium text-gray-700 flex items-center gap-1">
                  {{ field.label || field.name }}
                  <span v-if="field.required" class="text-red-500">*</span>
                </label>
                <!-- Show X button only for non-mandatory fields -->
                <button
                  v-if="!field.required"
                  type="button"
                  @click="hideDynamicField(resolveFieldKey(field, index), index)"
                  class="text-red-600 hover:text-red-800 transition-colors"
                  title="Remove this field"
                >
                  <X class="h-4 w-4" :class="{ 'opacity-50': !dynamicResponseData[resolveFieldKey(field, index)], 'opacity-100': dynamicResponseData[resolveFieldKey(field, index)] }" />
                </button>
              </div>
              <p v-if="field.description" class="text-xs text-gray-500">{{ field.description }}</p>
              
              <!-- Text Input -->
              <input
                v-if="field.type === 'text' || field.type === 'string' || !field.type"
                v-model="dynamicResponseData[resolveFieldKey(field, index)]"
                :type="field.inputType || 'text'"
                :placeholder="field.placeholder || `Enter ${field.label || field.name}`"
                :required="field.required"
                :class="getDynamicFieldInputClasses(resolveFieldKey(field, index))"
                @input="() => handleDynamicFieldInput(field, index)"
                @blur="() => handleDynamicFieldBlurAndSave(field, index)"
              />
              
              <!-- Number Input -->
              <input
                v-else-if="field.type === 'number' || field.type === 'integer' || field.type === 'decimal'"
                v-model.number="dynamicResponseData[resolveFieldKey(field, index)]"
                type="number"
                :min="field.min"
                :max="field.max"
                :step="field.step || (field.type === 'decimal' ? 0.01 : 1)"
                :placeholder="field.placeholder || `Enter ${field.label || field.name}`"
                :required="field.required"
                :class="getDynamicFieldInputClasses(resolveFieldKey(field, index))"
                @input="() => handleDynamicFieldInput(field, index)"
                @blur="() => handleDynamicFieldBlurAndSave(field, index)"
              />
              
              <!-- Textarea -->
              <textarea
                v-else-if="field.type === 'textarea' || field.type === 'text'"
                v-model="dynamicResponseData[resolveFieldKey(field, index)]"
                :rows="field.rows || 4"
                :placeholder="field.placeholder || `Enter ${field.label || field.name}`"
                :required="field.required"
                :class="`${getDynamicFieldInputClasses(resolveFieldKey(field, index))} resize-none min-h-24`"
                @input="() => handleDynamicFieldInput(field, index)"
                @blur="() => handleDynamicFieldBlurAndSave(field, index)"
              />
              
              <!-- Date Input -->
              <input
                v-else-if="field.type === 'date'"
                v-model="dynamicResponseData[resolveFieldKey(field, index)]"
                type="date"
                :min="field.min"
                :max="field.max"
                :required="field.required"
                :class="getDynamicFieldInputClasses(resolveFieldKey(field, index))"
                @input="() => handleDynamicFieldInput(field, index)"
                @blur="() => handleDynamicFieldBlurAndSave(field, index)"
              />
              
              <!-- Email Input -->
              <input
                v-else-if="field.type === 'email'"
                v-model="dynamicResponseData[resolveFieldKey(field, index)]"
                type="email"
                :placeholder="field.placeholder || `Enter ${field.label || field.name}`"
                :required="field.required"
                :class="getDynamicFieldInputClasses(resolveFieldKey(field, index))"
                @input="() => handleDynamicFieldInput(field, index)"
                @blur="() => handleDynamicFieldBlurAndSave(field, index)"
              />
              
              <!-- URL Input -->
              <input
                v-else-if="field.type === 'url'"
                v-model="dynamicResponseData[resolveFieldKey(field, index)]"
                type="url"
                :placeholder="field.placeholder || `Enter ${field.label || field.name}`"
                :required="field.required"
                :class="getDynamicFieldInputClasses(resolveFieldKey(field, index))"
                @input="() => handleDynamicFieldInput(field, index)"
                @blur="() => handleDynamicFieldBlurAndSave(field, index)"
              />
              
              <!-- File Upload -->
              <div v-else-if="field.type === 'file' || field.type === 'file_upload'" class="space-y-3">
                <input
                  type="file"
                  :required="field.required"
                  class="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  @change="event => handleDynamicFileChange(field, index, event)"
                />
                <div
                  v-if="dynamicResponseData[resolveFieldKey(field, index)]?.fileName"
                  class="flex flex-wrap items-center justify-between gap-2 rounded-md border border-gray-200 bg-gray-50 p-3"
                >
                  <div>
                    <p class="text-sm font-medium text-gray-900">
                      {{ dynamicResponseData[resolveFieldKey(field, index)].fileName }}
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ formatFileSize(dynamicResponseData[resolveFieldKey(field, index)].fileSize || 0) }}
                    </p>
                  </div>
                  <div class="flex gap-2">
                    <button
                      type="button"
                      class="inline-flex items-center px-3 py-1.5 rounded-md border border-blue-300 text-xs font-medium text-blue-700 bg-white hover:bg-blue-50"
                      @click="() => downloadDynamicFileValue(field, index)"
                    >
                      Download
                    </button>
                    <button
                      type="button"
                      class="inline-flex items-center px-3 py-1.5 rounded-md border border-red-200 text-xs font-medium text-red-700 bg-white hover:bg-red-50"
                      @click="() => clearDynamicFileValue(field, index)"
                    >
                      Remove
                    </button>
                  </div>
                </div>
                <div
                  v-else-if="typeof dynamicResponseData[resolveFieldKey(field, index)] === 'string'"
                  class="flex flex-wrap items-center justify-between gap-2 rounded-md border border-gray-200 bg-gray-50 p-3"
                >
                  <p class="text-sm text-gray-700">A file reference has been saved for this field.</p>
                  <div class="flex gap-2">
                    <button
                      type="button"
                      class="inline-flex items-center px-3 py-1.5 rounded-md border border-blue-300 text-xs font-medium text-blue-700 bg-white hover:bg-blue-50"
                      @click="() => downloadDynamicFileValue(field, index)"
                    >
                      Download
                    </button>
                    <button
                      type="button"
                      class="inline-flex items-center px-3 py-1.5 rounded-md border border-red-200 text-xs font-medium text-red-700 bg-white hover:bg-red-50"
                      @click="() => clearDynamicFileValue(field, index)"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </div>
              
              <!-- Default to text input if type is unknown -->
              <input
                v-else
                v-model="dynamicResponseData[resolveFieldKey(field, index)]"
                type="text"
                :placeholder="field.placeholder || `Enter ${field.label || field.name}`"
                :required="field.required"
                :class="getDynamicFieldInputClasses(resolveFieldKey(field, index))"
                @input="() => handleDynamicFieldInput(field, index)"
                @blur="() => handleDynamicFieldBlurAndSave(field, index)"
              />

              <p
                v-if="dynamicFieldErrors[resolveFieldKey(field, index)]"
                class="text-xs text-red-600"
              >
                {{ dynamicFieldErrors[resolveFieldKey(field, index)] }}
              </p>
              </div>
            </template>
          </div>
          
          <!-- Note about custom fields -->
          <div v-if="customDynamicFields.length > 0 && dynamicResponseFields.length > 0" class="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p class="text-xs text-blue-800">
              <strong>Note:</strong> Your custom fields ({{ customDynamicFields.length }}) are shown above with their values. They are saved as key:value pairs in the response.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Navigation Buttons -->
    <div class="flex justify-between mt-6">
      <button
        type="button"
        @click="goToPreviousTab"
        class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        ← Previous: Financial
      </button>
      <button
        type="button"
        @click="goToNextTab"
        class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        Next: Compliance →
      </button>
    </div>
    </div>

    <!-- Compliance & Certifications -->
    <div v-show="activeFormTab === 'compliance'">
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center gap-2">
          <Shield class="h-5 w-5 text-gray-700" />
          <h3 class="text-lg font-semibold text-gray-900">Compliance & Certifications</h3>
          <CheckCircle2 v-if="completionStatus.compliance === 100" class="h-4 w-4 text-green-600 ml-auto" />
          <AlertCircle v-else class="h-4 w-4 text-yellow-600" />
          <button
            type="button"
            @click="toggleCategoryFieldPanel('compliance')"
            class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
          >
            <span class="text-base leading-none">+</span>
            Add Field
          </button>
        </div>
      </div>
      <div class="p-6 space-y-6">
        <!-- Company Certifications -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Company Certifications</h4>
          <div class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div v-if="!hiddenFields.isoCertifications" class="space-y-2">
                <div class="flex items-center justify-between">
                  <label class="text-sm font-medium text-gray-700">ISO Certifications</label>
                  <button
                    type="button"
                    @click="hideField('isoCertifications')"
                    class="text-red-600 hover:text-red-800 transition-colors"
                    title="Remove this field"
                  >
                    <X class="h-4 w-4" :class="{ 'opacity-50': !formData.iso9001 && !formData.iso27001 && !formData.iso14001, 'opacity-100': formData.iso9001 || formData.iso27001 || formData.iso14001 }" />
                  </button>
                </div>
                <div class="space-y-2">
                  <label class="flex items-center">
                    <input type="checkbox" v-model="formData.iso9001" class="mr-2" />
                    <span class="text-sm">ISO 9001 (Quality Management)</span>
                  </label>
                  <label class="flex items-center">
                    <input type="checkbox" v-model="formData.iso27001" class="mr-2" />
                    <span class="text-sm">ISO 27001 (Information Security)</span>
                  </label>
                  <label class="flex items-center">
                    <input type="checkbox" v-model="formData.iso14001" class="mr-2" />
                    <span class="text-sm">ISO 14001 (Environmental Management)</span>
                  </label>
                </div>
              </div>
              <div v-if="!hiddenFields.industryCertifications" class="space-y-2">
                <div class="flex items-center justify-between">
                  <label class="text-sm font-medium text-gray-700">Industry Certifications</label>
                  <button
                    type="button"
                    @click="hideField('industryCertifications')"
                    class="text-red-600 hover:text-red-800 transition-colors"
                    title="Remove this field"
                  >
                    <X class="h-4 w-4" :class="{ 'opacity-50': !formData.soc2 && !formData.pciDss && !formData.hippa, 'opacity-100': formData.soc2 || formData.pciDss || formData.hippa }" />
                  </button>
                </div>
                <div class="space-y-2">
                  <label class="flex items-center">
                    <input type="checkbox" v-model="formData.soc2" class="mr-2" />
                    <span class="text-sm">SOC 2 Type II</span>
                  </label>
                  <label class="flex items-center">
                    <input type="checkbox" v-model="formData.pciDss" class="mr-2" />
                    <span class="text-sm">PCI DSS</span>
                  </label>
                  <label class="flex items-center">
                    <input type="checkbox" v-model="formData.hippa" class="mr-2" />
                    <span class="text-sm">HIPAA Compliance</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Security & Compliance -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Security & Compliance</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Data Security Measures *</label>
              <textarea 
                v-model="formData.dataSecurityMeasures"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe your data security measures, encryption, access controls, etc."
                rows="3"
                required
              ></textarea>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Compliance Standards *</label>
              <textarea 
                v-model="formData.complianceStandards"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="List all compliance standards you adhere to"
                rows="3"
                required
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Insurance & Liability -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Insurance & Liability</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Professional Liability Insurance *</label>
              <div class="relative">
                <span class="absolute left-3 top-3 text-gray-500">$</span>
                <input 
                  v-model="formData.professionalLiability"
                  type="number"
                  step="1000"
                  min="0"
                  class="w-full pl-8 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0"
                  required
                />
              </div>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">General Liability Insurance *</label>
              <div class="relative">
                <span class="absolute left-3 top-3 text-gray-500">$</span>
                <input 
                  v-model="formData.generalLiability"
                  type="number"
                  step="1000"
                  min="0"
                  class="w-full pl-8 pr-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="0"
                  required
                />
              </div>
            </div>
          </div>
        </div>

        <!-- References -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Client References</h4>
          <div class="space-y-4">
            <div v-for="(reference, index) in (formData.references || [])" :key="index" class="p-4 border border-gray-200 rounded-lg space-y-4">
              <div class="flex items-center justify-between">
                <h5 class="font-medium text-gray-900">Reference {{ index + 1 }}</h5>
                <button 
                  type="button" 
                  @click="removeReference(index)"
                  class="text-red-600 hover:text-red-800"
                >
                  <X class="h-4 w-4" />
                </button>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2">
                  <label class="text-sm font-medium text-gray-700">Company Name *</label>
                  <input 
                    v-model="reference.companyName"
                    class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter company name"
                    required
                  />
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-gray-700">Contact Person *</label>
                  <input 
                    v-model="reference.contactPerson"
                    class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter contact person"
                    required
                  />
                </div>
                <div class="space-y-2">
                  <label class="text-sm font-medium text-gray-700">Email *</label>
                  <input 
                    v-model="reference.email"
                    type="email"
                    class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter email"
                    required
                  />
                </div>
                <div v-if="!isReferenceFieldHidden(index, 'phone')" class="space-y-2">
                  <div class="flex items-center justify-between">
                    <label class="text-sm font-medium text-gray-700">Phone</label>
                    <button
                      type="button"
                      @click="hideReferenceField(index, 'phone')"
                      class="text-red-600 hover:text-red-800 transition-colors"
                      title="Remove this field"
                    >
                      <X class="h-4 w-4" :class="{ 'opacity-50': !reference.phone, 'opacity-100': reference.phone }" />
                    </button>
                  </div>
                  <input 
                    v-model="reference.phone"
                    type="tel"
                    class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter phone"
                  />
                </div>
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700">Project Description *</label>
                <textarea 
                  v-model="reference.projectDescription"
                  class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Describe the project you completed for this client"
                  rows="2"
                  required
                ></textarea>
              </div>
            </div>
            <button 
              type="button" 
              @click="addReference"
              class="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <UserPlus class="h-4 w-4 mr-2" />
              Add Reference
            </button>
          </div>
        </div>

        <!-- Custom Fields for Compliance Section -->
        <div v-if="categoryCustomFieldPanelOpen.compliance" class="mt-6 pt-6 border-t border-gray-200">
          <div class="bg-blue-50 border border-blue-200 rounded-lg p-5 space-y-4">
            <div class="flex items-center justify-between flex-wrap gap-2">
              <div>
                <h5 class="text-sm font-semibold text-blue-900">Add Custom Fields</h5>
                <p class="text-xs text-blue-800">Add additional compliance fields. Each field is saved as a key:value pair.</p>
              </div>
            </div>
            <div class="bg-white border border-blue-300 rounded-lg p-4 space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
                <div class="md:col-span-3 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Field Label *</label>
                  <input v-model="newCustomField.label" type="text" placeholder="e.g., Audit Report" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'compliance'" />
                </div>
                <div class="md:col-span-2 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Data Type *</label>
                  <select v-model="newCustomField.type" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @change="newCustomField.value = newCustomField.type === 'file' ? null : ''; newCustomField.category = 'compliance'">
                    <option v-for="type in customFieldTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
                  </select>
                </div>
                <div class="md:col-span-6 space-y-1">
                  <label class="text-xs font-medium text-blue-900">Value *</label>
                  <input v-if="newCustomField.type === 'text'" v-model="newCustomField.value" type="text" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'compliance'" />
                  <textarea v-else-if="newCustomField.type === 'textarea'" v-model="newCustomField.value" rows="2" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none" @focus="newCustomField.category = 'compliance'" />
                  <input v-else-if="newCustomField.type === 'number' || newCustomField.type === 'decimal'" v-model.number="newCustomField.value" type="number" :step="newCustomField.type === 'decimal' ? 0.01 : 1" placeholder="Enter number" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'compliance'" />
                  <input v-else-if="newCustomField.type === 'date'" v-model="newCustomField.value" type="date" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'compliance'" />
                  <input v-else-if="newCustomField.type === 'email'" v-model="newCustomField.value" type="email" placeholder="Enter email" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'compliance'" />
                  <input v-else-if="newCustomField.type === 'url'" v-model="newCustomField.value" type="url" placeholder="Enter URL" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'compliance'" />
                  <div v-else-if="newCustomField.type === 'file'" class="space-y-2">
                    <input type="file" @change="(e) => handleNewCustomFieldFileChange(e, 'compliance')" class="block w-full text-sm text-gray-900 border border-blue-200 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                    <div v-if="newCustomField.fileData" class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded p-2">
                      <span class="text-xs text-gray-700">{{ newCustomField.fileData.fileName }}</span>
                      <button type="button" @click="newCustomField.fileData = null; newCustomField.value = null" class="text-xs text-red-600 hover:text-red-800">Remove</button>
                    </div>
                  </div>
                  <input v-else v-model="newCustomField.value" type="text" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'compliance'" />
                </div>
                <div class="md:col-span-1">
                  <button type="button" @click="addCustomFieldWithValue('compliance')" class="w-full px-4 py-2.5 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors">Add</button>
                </div>
              </div>
            </div>
            <div v-if="categoryCustomFields.compliance.length > 0" class="space-y-2">
              <p class="text-xs font-semibold text-blue-900">Custom fields added:</p>
              <div class="space-y-2">
                <template v-for="field in categoryCustomFields.compliance" :key="field.id">
                  <div v-if="!isCategoryFieldHidden(field.id, 'compliance')" class="bg-white border border-blue-200 rounded-lg p-3">
                    <div class="flex items-start justify-between gap-3">
                      <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                          <p class="text-sm font-semibold text-gray-900">{{ field.label }}</p>
                          <span class="text-xs text-gray-500">({{ getCustomFieldTypeLabel(field.type) }})</span>
                          <span class="text-xs text-blue-600 font-mono">Key: {{ field.name }}</span>
                        </div>
                        <div class="mt-2">
                          <p v-if="field.type !== 'file'" class="text-sm text-gray-700"><span class="font-medium">Value:</span> <span class="ml-1">{{ formatCustomFieldValue(field, 'compliance') }}</span></p>
                          <div v-else-if="getCustomFieldValue(field, 'compliance')" class="flex items-center gap-2">
                            <span class="text-sm text-gray-700 font-medium">File:</span>
                            <span class="text-sm text-gray-600">{{ getCustomFieldValue(field, 'compliance')?.fileName || 'File uploaded' }}</span>
                            <button type="button" @click="downloadCustomFieldFile(field, 'compliance')" class="text-xs text-blue-600 hover:text-blue-800">Download</button>
                          </div>
                        </div>
                      </div>
                      <div class="flex items-center gap-2">
                        <!-- X button to hide field (for non-mandatory fields) -->
                        <button
                          v-if="!field.required"
                          type="button"
                          @click="hideCategoryField(field.id, 'compliance')"
                          class="text-red-600 hover:text-red-800 transition-colors"
                          title="Remove this field"
                        >
                          <X class="h-4 w-4" :class="{ 'opacity-50': !getCustomFieldValue(field, 'compliance'), 'opacity-100': getCustomFieldValue(field, 'compliance') }" />
                        </button>
                        <!-- Remove button to delete field completely -->
                        <button type="button" @click="removeCustomField(field.id, 'compliance')" class="text-xs text-red-600 hover:text-red-800 font-medium px-2 py-1">Delete</button>
                      </div>
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab Navigation Buttons -->
    <div class="flex justify-between mt-6">
      <button
        type="button"
        @click="goToPreviousTab"
        class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        ← Previous: RFP Responses
      </button>
      <button
        type="button"
        @click="goToNextTab"
        class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        Next: Documents →
      </button>
    </div>
    </div>

    <!-- Document Upload -->
    <div v-show="activeFormTab === 'documents'">
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Upload class="h-5 w-5 text-gray-700" />
            <h3 class="text-lg font-semibold text-gray-900">Supporting Documents</h3>
            <CheckCircle2 v-if="completionStatus.documents === 100" class="h-4 w-4 text-green-600" />
            <AlertCircle v-else class="h-4 w-4 text-yellow-600" />
          </div>
          <div class="flex items-center gap-2">
            <button
              type="button"
              @click="toggleCategoryFieldPanel('documents')"
              class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
            >
              <span class="text-base leading-none">+</span>
              Add Field
            </button>
            <button
              v-if="regularDocuments.length >= 2"
              type="button"
              @click="mergeSelectedDocuments"
              :disabled="isMergingDocuments || isUploadingDocuments || selectedDocuments.size < 2"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Loader2 v-if="isMergingDocuments" class="h-4 w-4 mr-2 animate-spin" />
              <FileText v-else class="h-4 w-4 mr-2" />
              <span v-if="isMergingDocuments">Merging...</span>
              <span v-else>Merge Selected ({{ selectedDocuments.size }})</span>
            </button>
          </div>
        </div>
      </div>
      <div class="p-6 space-y-6">
        <!-- Document Upload Form -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Upload Supporting Documents</h4>
          <p class="text-sm text-gray-600">
            Upload your proposal documents, technical specifications, pricing sheets, and other supporting materials.
          </p>
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Document Name *</label>
              <input
                v-model="newDocument.name"
                type="text"
                placeholder="e.g., Technical Specifications"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Document Type *</label>
              <select
                v-model="newDocument.documentType"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option v-for="option in documentTypeOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Select File *</label>
              <input
                type="file"
                @change="handleFileSelect"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png,.zip"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          
          <div class="flex gap-2">
            <button
              type="button"
              @click="addDocument"
              :disabled="!newDocument.name || !newDocument.file"
              class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Upload class="h-4 w-4 mr-2" />
              Add Document
            </button>
            <button
              type="button"
              @click="clearDocumentForm"
              class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <X class="h-4 w-4 mr-2" />
              Clear
            </button>
          </div>
        </div>

        <!-- Regular Documents List -->
        <div v-if="regularDocuments.length > 0" class="space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <h4 class="text-sm font-semibold text-gray-800">Documents ({{ regularDocuments.length }})</h4>
              <div class="flex items-center gap-2 text-xs text-gray-600">
                <div class="flex items-center gap-1">
                  <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>{{ regularDocuments.filter(d => d.uploaded).length }} Saved</span>
                </div>
                <div class="flex items-center gap-1">
                  <div class="w-2 h-2 bg-gray-400 rounded-full"></div>
                  <span>{{ regularDocuments.filter(d => !d.uploaded).length }} Pending</span>
                </div>
              </div>
            </div>
            <div v-if="regularDocuments.length >= 2" class="flex items-center gap-2">
              <button
                type="button"
                @click="selectAllDocuments"
                class="text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                Select All
              </button>
              <button
                type="button"
                @click="deselectAllDocuments"
                class="text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                Deselect All
              </button>
              <span class="text-xs text-gray-600">
                {{ selectedDocuments.size }} selected
              </span>
            </div>
          </div>
          <div class="space-y-2">
            <div 
              v-for="(doc, docIndex) in regularDocuments" 
              :key="`doc-${docIndex}-${doc.s3Id || doc.name}`"
              :draggable="regularDocuments.length > 1 && !isMergingDocuments"
              @dragstart="handleDragStart(getRegularDocumentIndex(docIndex), $event)"
              @dragover.prevent="handleDragOver(getRegularDocumentIndex(docIndex), $event)"
              @drop="handleDrop(getRegularDocumentIndex(docIndex), $event)"
              @dragend="handleDragEnd"
              class="flex items-center justify-between p-3 border border-gray-200 rounded-lg cursor-move transition-all"
              :class="[
                doc.uploaded ? 'bg-green-50 border-green-200' : '',
                draggedIndex === getRegularDocumentIndex(docIndex) ? 'opacity-50 border-blue-400 bg-blue-50' : '',
                dragOverIndex === getRegularDocumentIndex(docIndex) ? 'border-blue-500 bg-blue-100' : '',
                selectedDocuments.has(getRegularDocumentIndex(docIndex)) ? 'border-blue-500 bg-blue-50' : ''
              ]"
            >
              <div class="flex items-center gap-3 flex-1">
                <!-- Checkbox for selection -->
                <input
                  v-if="regularDocuments.length >= 2"
                  type="checkbox"
                  :checked="selectedDocuments.has(getRegularDocumentIndex(docIndex))"
                  @change="toggleDocumentSelection(getRegularDocumentIndex(docIndex))"
                  :disabled="isMergingDocuments"
                  class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer disabled:cursor-not-allowed"
                />
                
                <!-- Drag Handle -->
                <div 
                  v-if="regularDocuments.length > 1"
                  class="mr-2 cursor-grab active:cursor-grabbing"
                  :class="{ 'cursor-not-allowed': isMergingDocuments }"
                  title="Drag to reorder"
                >
                  <svg class="h-5 w-5 text-gray-400 hover:text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                    <circle cx="9" cy="5" r="1.5"></circle>
                    <circle cx="9" cy="12" r="1.5"></circle>
                    <circle cx="9" cy="19" r="1.5"></circle>
                    <circle cx="15" cy="5" r="1.5"></circle>
                    <circle cx="15" cy="12" r="1.5"></circle>
                    <circle cx="15" cy="19" r="1.5"></circle>
                  </svg>
                </div>
                
                <CheckCircle2 v-if="doc.uploaded" class="h-4 w-4 text-green-500" />
                <FileText v-else class="h-4 w-4 text-gray-500" />
                <div class="flex-1">
                  <p class="text-sm font-medium text-gray-900">
                    {{ doc.name }} 
                    <span v-if="regularDocuments.length > 1" class="text-xs text-gray-400">(#{{ docIndex + 1 }})</span>
                  </p>
                  <p class="text-xs text-gray-600">
                    {{ doc.fileName }} ({{ formatFileSize(doc.fileSize) }})
                    <span v-if="doc.documentType" class="ml-2 px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded">
                      {{ documentTypeOptions.find(opt => opt.value === doc.documentType)?.label || doc.documentType }}
                    </span>
                  </p>
                  <p v-if="doc.uploaded" class="text-xs text-green-600">✅ Uploaded (ID: {{ doc.s3Id }})</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button
                  v-if="doc.uploaded"
                  type="button"
                  @click="downloadVendorDocument(doc)"
                  class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  <Download class="h-4 w-4 mr-2" />
                  Download
                </button>
                <button
                  type="button"
                  @click="removeDocument(getRegularDocumentIndex(docIndex))"
                  :disabled="doc.uploaded && isMergingDocuments"
                  class="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 disabled:opacity-50"
                >
                  <X class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Merged Documents Section -->
        <div v-if="mergedDocuments.length > 0" class="space-y-3 mt-6 pt-6 border-t border-gray-200">
          <div class="flex items-center gap-4">
            <h4 class="text-sm font-semibold text-blue-700">Merged Documents ({{ mergedDocuments.length }})</h4>
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span class="text-xs text-gray-600">All merged documents are saved</span>
            </div>
          </div>
          <div class="space-y-2">
            <div 
              v-for="(doc, docIndex) in mergedDocuments" 
              :key="`merged-${docIndex}-${doc.s3Id || doc.name}`"
              class="flex items-center justify-between p-3 border border-blue-200 rounded-lg bg-blue-50 transition-colors"
            >
              <div class="flex items-center gap-3 flex-1">
                <FileText class="h-4 w-4 text-blue-600" />
                <div class="flex-1">
                  <p class="text-sm font-medium text-blue-900">
                    {{ doc.name }}
                    <span class="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">Merged</span>
                    <span class="text-xs text-gray-400">(#{{ docIndex + 1 }})</span>
                  </p>
                  <p class="text-xs text-gray-600">
                    {{ doc.fileName }} ({{ formatFileSize(doc.fileSize) }})
                    <span v-if="doc.documentType" class="ml-2 px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded">
                      {{ documentTypeOptions.find(opt => opt.value === doc.documentType)?.label || doc.documentType }}
                    </span>
                  </p>
                  <p class="text-xs text-green-600">✅ Uploaded (ID: {{ doc.s3Id }})</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  @click="downloadVendorDocument(doc)"
                  title="Download merged document"
                  class="inline-flex items-center px-3 py-2 border border-blue-300 shadow-sm text-sm font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50"
                >
                  <Download class="h-4 w-4 mr-2" />
                  Download
                </button>
                <button
                  type="button"
                  @click="removeDocument(getMergedDocumentIndex(docIndex))"
                  :disabled="isMergingDocuments"
                  class="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 disabled:opacity-50"
                  title="Delete merged document"
                >
                  <X class="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Custom Fields for Documents Section -->
        <div v-if="categoryCustomFieldPanelOpen.documents" class="border border-blue-200 rounded-lg p-5 space-y-4">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <div>
              <h5 class="text-sm font-semibold text-blue-900">Custom Document Fields</h5>
              <p class="text-xs text-blue-800">Track extra info about uploaded documents.</p>
            </div>
          </div>
          <div class="bg-white border border-blue-300 rounded-lg p-4 space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
              <div class="md:col-span-3 space-y-1">
                <label class="text-xs font-medium text-blue-900">Field Label *</label>
                <input v-model="newCustomField.label" type="text" placeholder="e.g., Expiry Date" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'documents'" />
              </div>
              <div class="md:col-span-2 space-y-1">
                <label class="text-xs font-medium text-blue-900">Data Type *</label>
                <select v-model="newCustomField.type" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @change="newCustomField.value = newCustomField.type === 'file' ? null : ''; newCustomField.category = 'documents'">
                  <option v-for="type in customFieldTypes" :key="type.value" :value="type.value">{{ type.label }}</option>
                </select>
              </div>
              <div class="md:col-span-6 space-y-1">
                <label class="text-xs font-medium text-blue-900">Value *</label>
                <input v-if="newCustomField.type === 'text'" v-model="newCustomField.value" type="text" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'documents'" />
                <textarea v-else-if="newCustomField.type === 'textarea'" v-model="newCustomField.value" rows="2" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm resize-none" @focus="newCustomField.category = 'documents'" />
                <input v-else-if="newCustomField.type === 'number' || newCustomField.type === 'decimal'" v-model.number="newCustomField.value" type="number" :step="newCustomField.type === 'decimal' ? 0.01 : 1" placeholder="Enter number" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'documents'" />
                <input v-else-if="newCustomField.type === 'date'" v-model="newCustomField.value" type="date" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'documents'" />
                <input v-else-if="newCustomField.type === 'email'" v-model="newCustomField.value" type="email" placeholder="Enter email" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'documents'" />
                <input v-else-if="newCustomField.type === 'url'" v-model="newCustomField.value" type="url" placeholder="Enter URL" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'documents'" />
                <div v-else-if="newCustomField.type === 'file'" class="space-y-2">
                  <input type="file" @change="(e) => handleNewCustomFieldFileChange(e, 'documents')" class="block w-full text-sm text-gray-900 border border-blue-200 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500" />
                  <div v-if="newCustomField.fileData" class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded p-2">
                    <span class="text-xs text-gray-700">{{ newCustomField.fileData.fileName }}</span>
                    <button type="button" @click="newCustomField.fileData = null; newCustomField.value = null" class="text-xs text-red-600 hover:text-red-800">Remove</button>
                  </div>
                </div>
                <input v-else v-model="newCustomField.value" type="text" placeholder="Enter value" class="w-full p-2.5 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm" @focus="newCustomField.category = 'documents'" />
              </div>
              <div class="md:col-span-1">
                <button type="button" @click="addCustomFieldWithValue('documents')" class="w-full px-4 py-2.5 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors">Add</button>
              </div>
            </div>
          </div>
          <div v-if="categoryCustomFields.documents.length > 0" class="space-y-2">
            <p class="text-xs font-semibold text-blue-900">Custom document fields:</p>
            <div class="space-y-2">
              <template v-for="field in categoryCustomFields.documents" :key="field.id">
                <div v-if="!isCategoryFieldHidden(field.id, 'documents')" class="bg-white border border-blue-200 rounded-lg p-3">
                  <div class="flex items-start justify-between gap-3">
                    <div class="flex-1">
                      <div class="flex items-center gap-2 mb-1">
                        <p class="text-sm font-semibold text-gray-900">{{ field.label }}</p>
                        <span class="text-xs text-gray-500">({{ getCustomFieldTypeLabel(field.type) }})</span>
                        <span class="text-xs text-blue-600 font-mono">Key: {{ field.name }}</span>
                      </div>
                      <div class="mt-2">
                        <p v-if="field.type !== 'file'" class="text-sm text-gray-700"><span class="font-medium">Value:</span> <span class="ml-1">{{ formatCustomFieldValue(field, 'documents') }}</span></p>
                        <div v-else-if="getCustomFieldValue(field, 'documents')" class="flex items-center gap-2">
                          <span class="text-sm text-gray-700 font-medium">File:</span>
                          <span class="text-sm text-gray-600">{{ getCustomFieldValue(field, 'documents')?.fileName || 'File uploaded' }}</span>
                          <button type="button" @click="downloadCustomFieldFile(field, 'documents')" class="text-xs text-blue-600 hover:text-blue-800">Download</button>
                        </div>
                      </div>
                    </div>
                    <div class="flex items-center gap-2">
                      <!-- X button to hide field (for non-mandatory fields) -->
                      <button
                        v-if="!field.required"
                        type="button"
                        @click="hideCategoryField(field.id, 'documents')"
                        class="text-red-600 hover:text-red-800 transition-colors"
                        title="Remove this field"
                      >
                        <X class="h-4 w-4" :class="{ 'opacity-50': !getCustomFieldValue(field, 'documents'), 'opacity-100': getCustomFieldValue(field, 'documents') }" />
                      </button>
                      <!-- Remove button to delete field completely -->
                      <button type="button" @click="removeCustomField(field.id, 'documents')" class="text-xs text-red-600 hover:text-red-800 font-medium px-2 py-1">Delete</button>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- File Upload Guidelines -->
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h5 class="font-medium text-blue-900 mb-2">Upload Guidelines</h5>
          <ul class="text-sm text-blue-800 space-y-1">
            <li>• Supported formats: PDF, Word (.doc, .docx), Excel (.xls, .xlsx), Images (.jpg, .jpeg, .png), Text files (.txt)</li>
            <li>• Maximum file size: 50MB per file</li>
            <li>• Files are securely stored in S3 cloud storage</li>
            <li>• You can rearrange documents and merge them together</li>
            <li>• <strong>Merging supports all combinations:</strong> PDF + Word, PDF + Excel, PDF + Images, Word + Excel, Excel + Images, etc.</li>
            <li>• All files are automatically converted to PDF format during merging</li>
            <li>• Excel files: All sheets are converted to tables in the merged PDF</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Tab Navigation Buttons -->
    <div class="flex justify-between mt-6">
      <button
        type="button"
        @click="goToPreviousTab"
        class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        ← Previous: Compliance
      </button>
      <button
        type="button"
        @click="goToNextTab"
        class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        Next: Team →
      </button>
    </div>
    </div>

    <!-- Team Structure & Key Personnel -->
    <div v-show="activeFormTab === 'team'">
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center gap-2">
          <Users class="h-5 w-5 text-gray-700" />
          <h3 class="text-lg font-semibold text-gray-900">Team Structure & Key Personnel</h3>
          <CheckCircle2 v-if="completionStatus.personnel === 100" class="h-4 w-4 text-green-600 ml-auto" />
          <AlertCircle v-else class="h-4 w-4 text-yellow-600" />
          <button
            type="button"
            @click="toggleCategoryFieldPanel('team')"
            class="inline-flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-md border border-blue-200 text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
          >
            <span class="text-base leading-none">+</span>
            Add Field
          </button>
        </div>
      </div>
      <div class="p-6 space-y-6">
        <!-- Project Team Overview -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Project Team Overview</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Total Team Size *</label>
              <input 
                v-model="formData.totalTeamSize"
                type="number"
                min="1"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter total team size"
                required
              />
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Team Structure *</label>
              <select 
                v-model="formData.teamStructure"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Select team structure</option>
                <option value="Dedicated Team">Dedicated Team</option>
                <option value="Shared Resources">Shared Resources</option>
                <option value="Hybrid Model">Hybrid Model</option>
                <option value="Outsourced">Outsourced</option>
              </select>
                </div>
            </div>
              </div>

        <!-- Key Personnel -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h4 class="text-md font-semibold text-gray-800">Key Personnel</h4>
            <button 
              type="button" 
              @click="addTeamMember"
              class="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <UserPlus class="h-4 w-4 mr-2" />
              Add Team Member
            </button>
                </div>
          
          <div v-for="(person, index) in (keyPersonnel || [])" :key="index" class="p-4 border border-gray-200 rounded-lg space-y-4">
            <div class="flex items-center justify-between">
              <h5 class="font-medium text-gray-900">Team Member {{ index + 1 }}</h5>
              <button 
                type="button" 
                @click="removeTeamMember(index)"
                class="text-red-600 hover:text-red-800"
              >
                <X class="h-4 w-4" />
              </button>
              </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700">Full Name *</label>
                <input 
                  v-model="person.name"
                  class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter full name"
                  required
                />
            </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700">Role/Position *</label>
                <input 
                  v-model="person.role"
                  class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Project Manager, Technical Lead"
                  required
                />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700">Email *</label>
                <input 
                  v-model="person.email"
                  type="email"
                  class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter email address"
                  required
                />
              </div>
              <div v-if="!isPersonnelFieldHidden(index, 'phone')" class="space-y-2">
                <div class="flex items-center justify-between">
                  <label class="text-sm font-medium text-gray-700">Phone</label>
                  <button
                    type="button"
                    @click="hidePersonnelField(index, 'phone')"
                    class="text-red-600 hover:text-red-800 transition-colors"
                    title="Remove this field"
                  >
                    <X class="h-4 w-4" :class="{ 'opacity-50': !person.phone, 'opacity-100': person.phone }" />
                  </button>
                </div>
                <input 
                  v-model="person.phone"
                  type="tel"
                  class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter phone number"
                />
              </div>
              <div class="space-y-2">
                <label class="text-sm font-medium text-gray-700">Years of Experience *</label>
                <input 
                  v-model="person.experience"
                  type="number"
                  min="0"
                  class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter years of experience"
                  required
                />
              </div>
              <div v-if="!isPersonnelFieldHidden(index, 'education')" class="space-y-2">
                <div class="flex items-center justify-between">
                  <label class="text-sm font-medium text-gray-700">Education Level</label>
                  <button
                    type="button"
                    @click="hidePersonnelField(index, 'education')"
                    class="text-red-600 hover:text-red-800 transition-colors"
                    title="Remove this field"
                  >
                    <X class="h-4 w-4" :class="{ 'opacity-50': !person.education, 'opacity-100': person.education }" />
                  </button>
                </div>
                <select 
                  v-model="person.education"
                  class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select education level</option>
                  <option value="High School">High School</option>
                  <option value="Associate Degree">Associate Degree</option>
                  <option value="Bachelor's Degree">Bachelor's Degree</option>
                  <option value="Master's Degree">Master's Degree</option>
                  <option value="PhD">PhD</option>
                  <option value="Professional Certification">Professional Certification</option>
                </select>
              </div>
            </div>
            
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Relevant Experience *</label>
              <textarea 
                v-model="person.relevantExperience"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe relevant experience for this project"
                rows="3"
                required
              ></textarea>
            </div>
            
            <div v-if="!isPersonnelFieldHidden(index, 'certifications')" class="space-y-2">
              <div class="flex items-center justify-between">
                <label class="text-sm font-medium text-gray-700">Certifications & Qualifications</label>
                <button
                  type="button"
                  @click="hidePersonnelField(index, 'certifications')"
                  class="text-red-600 hover:text-red-800 transition-colors"
                  title="Remove this field"
                >
                  <X class="h-4 w-4" :class="{ 'opacity-50': !person.certifications || person.certifications.length === 0, 'opacity-100': person.certifications && person.certifications.length > 0 }" />
                </button>
              </div>
              <div class="space-y-2">
                <div v-for="(cert, certIndex) in (person.certifications || [])" :key="certIndex" class="flex items-center gap-2">
                  <input 
                    v-model="person.certifications[certIndex]"
                    class="flex-1 p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter certification"
                  />
                  <button 
                    type="button" 
                    @click="removeCertification(index, certIndex)"
                    class="text-red-600 hover:text-red-800"
                  >
                    <X class="h-4 w-4" />
        </button>
                </div>
                <button 
                  type="button" 
                  @click="addCertification(index)"
                  class="text-blue-600 hover:text-blue-800 text-sm"
                >
                  + Add Certification
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Project Management -->
        <div class="space-y-4">
          <h4 class="text-md font-semibold text-gray-800">Project Management</h4>
          <div class="space-y-4">
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Project Management Methodology *</label>
              <select 
                v-model="formData.projectMethodology"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Select methodology</option>
                <option value="Agile">Agile</option>
                <option value="Waterfall">Waterfall</option>
                <option value="Scrum">Scrum</option>
                <option value="Kanban">Kanban</option>
                <option value="Hybrid">Hybrid</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="text-sm font-medium text-gray-700">Communication Plan *</label>
              <textarea 
                v-model="formData.communicationPlan"
                class="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe your communication plan, reporting structure, and meeting schedules"
                rows="3"
                required
              ></textarea>
            </div>
          </div>
        </div>
      </div>
            </div>

    <!-- Tab Navigation Buttons -->
    <div class="flex justify-between mt-6">
      <button
        type="button"
        @click="goToPreviousTab"
        class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        ← Previous: Documents
      </button>
      <button
        v-if="!isPreviewReadonly"
        type="button"
        @click="handleAutoSave"
        class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        <Save class="h-4 w-4 mr-2" />
        Save Progress
      </button>
    </div>
    </div>
    </div><!-- End tab-content -->

    <!-- Submission Actions (Always Visible) -->
    <div v-if="!isPreviewReadonly" class="bg-white border border-gray-200 rounded-lg shadow-sm">
      <div class="p-6">
        <!-- Success Banner -->
        <div v-if="submissionStatus === 'SUBMITTED'" class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div class="flex items-center">
            <CheckCircle2 class="h-6 w-6 text-green-600 mr-3" />
            <div>
              <h3 class="text-lg font-semibold text-green-800">Proposal Successfully Submitted!</h3>
              <p class="text-green-700 text-sm">
                Your proposal was submitted on {{ formatDate(submittedAt) }} and is now under review.
              </p>
            </div>
          </div>
        </div>
        
        <div class="flex flex-col sm:flex-row justify-between items-center gap-4">
          <div class="text-sm text-gray-600">
            <p v-if="lastSavedAt">Last saved: {{ formatLastSaved(lastSavedAt) }}</p>
            <p v-else>Auto-save is enabled</p>
            <p v-if="submissionStatus === 'SUBMITTED'" class="text-green-600 font-medium">
              ✓ Proposal submitted on {{ formatDate(submittedAt) }}
            </p>
          </div>
          <div class="flex gap-2">
            <button type="button" @click="handleAutoSave" class="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
              <Save class="h-4 w-4 mr-2" />
                Save Draft
              </button>
            <button 
              type="button"
              @click="handleSubmit"
              :disabled="overallProgress < 50 || isSubmitting || submissionStatus === 'SUBMITTED' || submissionInProgress"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Loader2 v-if="isSubmitting" class="h-4 w-4 mr-2 animate-spin" />
              <CheckCircle2 v-else-if="submissionStatus === 'SUBMITTED'" class="h-4 w-4 mr-2" />
              <Send v-else class="h-4 w-4 mr-2" />
              {{ 
                isSubmitting ? 'Submitting...' : 
                submissionStatus === 'SUBMITTED' ? 'Already Submitted' : 
                'Submit Proposal' 
              }}
            </button>
            <div v-if="overallProgress < 50" class="text-sm text-gray-500 mt-2">
              Complete at least 50% of all sections to enable submission (currently {{ overallProgress }}%)
            </div>
            </div>
        </div>
      </div>
    </div>
        </div> <!-- End Form Content -->
      </div> <!-- End max-w-7xl -->

        <!-- Sliding Right Panel: Documents Viewer -->
        <div 
          v-if="rightPanelOpen"
          class="fixed inset-0 z-50 overflow-hidden"
          @click.self="toggleRightPanel"
        >
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-black bg-opacity-50 transition-opacity"></div>
          
          <!-- Sliding Panel -->
          <div class="absolute right-0 top-0 bottom-0 w-full max-w-2xl bg-white shadow-2xl overflow-y-auto transform transition-transform">
            <!-- Panel Header -->
            <div class="sticky top-0 z-10 bg-white border-b border-gray-200 px-6 py-4">
              <div class="flex items-center justify-between">
                <h2 class="text-xl font-bold text-gray-900">RFP Information</h2>
                <button
                  type="button"
                  @click="toggleRightPanel"
                  class="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X class="h-6 w-6" />
                </button>
              </div>
            </div>

            <!-- Panel Content -->
            <div class="space-y-4 p-6">
          <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
            <div class="p-6 border-b border-gray-200">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-900">Side Panel</h3>
                <div class="inline-flex rounded-md border border-gray-300 overflow-hidden bg-white">
                  <button
                    type="button"
                    @click="rightPanelTab = 'details'"
                    :class="['px-3 py-1.5 text-xs font-medium focus:outline-none', rightPanelTab === 'details' ? 'bg-blue-600 text-white' : 'text-gray-700']"
                  >
                    RFP Details
                  </button>
                  <button
                    type="button"
                    @click="rightPanelTab = 'documents'"
                    :class="['px-3 py-1.5 text-xs font-medium focus:outline-none border-l border-gray-300', rightPanelTab === 'documents' ? 'bg-blue-600 text-white' : 'text-gray-700']"
                  >
                    Documents
                  </button>
                </div>
              </div>
              <div v-if="rightPanelTab === 'documents' && selectedDocType" class="mt-2 text-xs text-gray-600">{{ selectedDocTypeLabel }}</div>
            </div>
            <div class="p-6 space-y-4">
              <!-- DETAILS TAB CONTENT -->
              <div v-if="rightPanelTab === 'details'" class="space-y-4">
                <div class="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div class="font-medium text-gray-900 mb-2">{{ rfpInfo.rfpTitle }}</div>
                  <div class="text-sm text-gray-700">RFP Number: <span class="font-medium">{{ rfpInfo.rfpNumber }}</span></div>
                  <div class="text-sm text-gray-700">Deadline: <span class="font-medium">{{ rfpInfo.deadline }}</span></div>
                  <div class="text-sm text-gray-700" v-if="rfpInfo.description">Description: <span class="font-medium break-words">{{ rfpInfo.description }}</span></div>
                  <div class="text-sm text-gray-700" v-if="rfpInfo.rfpType">Type: <span class="font-medium">{{ rfpInfo.rfpType }}</span></div>
                  <div class="text-sm text-gray-700" v-if="rfpInfo.category">Category: <span class="font-medium">{{ rfpInfo.category }}</span></div>
                  <div class="text-sm text-gray-700" v-if="rfpInfo.criticality">Criticality: <span class="font-medium capitalize">{{ rfpInfo.criticality }}</span></div>
                  <div class="text-sm text-gray-700">Budget: <span class="font-medium">{{ rfpInfo.budget }}</span></div>
                </div>
                <div class="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div class="font-medium text-gray-900 mb-2">Completion Snapshot</div>
                  <div class="grid grid-cols-2 gap-3 text-sm">
                    <div>Company: <span class="font-medium">{{ completionStatus.company }}%</span></div>
                    <div>Financial: <span class="font-medium">{{ completionStatus.financial }}%</span></div>
                    <div>Responses: <span class="font-medium">{{ completionStatus.responses }}%</span></div>
                    <div>Documents: <span class="font-medium">{{ completionStatus.documents }}%</span></div>
                    <div>Personnel: <span class="font-medium">{{ completionStatus.personnel }}%</span></div>
                    <div>Compliance: <span class="font-medium">{{ completionStatus.compliance }}%</span></div>
                  </div>
                </div>
                <div class="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div class="font-medium text-gray-900 mb-2">Invitation</div>
                  <div class="text-sm text-gray-700" v-if="invitationData.vendorName">Vendor: <span class="font-medium">{{ invitationData.vendorName }}</span></div>
                  <div class="text-sm text-gray-700" v-if="invitationData.contactEmail">Email: <span class="font-medium">{{ invitationData.contactEmail }}</span></div>
                </div>
              </div>

              <!-- DOCUMENTS TAB CONTENT -->
              <div v-else class="space-y-4">
                <!-- RFP Documents Section (Primary) -->
                <div class="space-y-3">
                  <div class="flex items-center justify-between">
                    <h4 class="text-sm font-semibold text-gray-900">📄 RFP Documents</h4>
                    <span v-if="rfpDocTabs.length > 0" class="text-xs text-gray-600 bg-blue-100 px-2 py-1 rounded-full">
                      {{ rfpDocTabs.length }} document{{ rfpDocTabs.length !== 1 ? 's' : '' }}
                    </span>
                  </div>
                  
                  <!-- Loading State -->
                  <div v-if="!rfpDocuments" class="text-sm text-gray-500 italic p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <Loader2 class="h-4 w-4 animate-spin inline mr-2" />
                    Loading RFP documents...
                  </div>
                  
                  <!-- No Documents State -->
                  <div v-else-if="rfpDocuments && rfpDocTabs.length === 0" class="text-sm text-gray-500 p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <div class="flex items-start gap-3">
                      <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                        </svg>
                      </div>
                      <div class="flex-1">
                        <p class="font-medium text-gray-700 mb-1">No RFP documents available</p>
                        <p class="text-xs text-gray-600">The RFP creator hasn't attached any documents to this proposal yet.</p>
                        <button 
                          type="button" 
                          @click="resolveRfpDocumentTabs"
                          class="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium"
                        >
                          🔄 Refresh documents
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Documents Available -->
                  <div v-else-if="rfpDocTabs.length > 0" class="space-y-3">
                    <div class="relative">
                      <select 
                        v-model="selectedRfpDocumentId"
                        @change="onRfpDocumentSelect"
                        class="w-full p-3 border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm"
                      >
                        <option value="">📂 Select a document to view...</option>
                        <option v-for="doc in rfpDocTabs" :key="doc.id" :value="doc.id">
                          📄 {{ doc.label }} ({{ doc.content_type || 'Document' }})
                        </option>
                        <option value="all" v-if="rfpDocTabs.length > 1">📋 View All Documents ({{ rfpDocTabs.length }})</option>
                      </select>
                      <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                        <svg class="h-5 w-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                      </div>
                    </div>
                  
                    <!-- Selected Document Actions -->
                    <div v-if="selectedRfpDocument" class="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <div class="flex items-center gap-3">
                        <FileText class="h-5 w-5 text-blue-600" />
                        <div>
                          <p class="font-medium text-gray-900">{{ selectedRfpDocument.label }}</p>
                          <p class="text-sm text-gray-600">{{ selectedRfpDocument.content_type || 'Document' }}</p>
                        </div>
                      </div>
                      <div class="flex items-center gap-2">
                        <button 
                          type="button" 
                          @click="selectedDocument = selectedRfpDocument; selectedDocType = String(selectedRfpDocument.id)"
                          class="px-3 py-2 text-xs rounded-md border-0 bg-blue-600 text-white hover:bg-blue-700 font-medium shadow-sm"
                        >
                          👁️ View
                        </button>
                        <button 
                          type="button" 
                          @click="downloadRfpDocument(selectedRfpDocument)"
                          class="inline-flex items-center px-3 py-2 border border-blue-300 shadow-sm text-xs font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50"
                        >
                          <Download class="h-3 w-3 mr-1" />
                          Download
                        </button>
                      </div>
                    </div>

                    <!-- All Documents List (when "View All" is selected) -->
                    <div v-else-if="selectedRfpDocumentId === 'all'" class="space-y-2 max-h-96 overflow-y-auto">
                      <div class="text-sm font-medium text-gray-700 mb-2 sticky top-0 bg-white pb-2">All RFP Documents ({{ rfpDocTabs.length }})</div>
                      <div v-for="doc in rfpDocTabs" :key="doc.id" class="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200 hover:border-blue-300 transition-colors">
                        <div class="flex items-center gap-2">
                          <FileText class="h-4 w-4 text-blue-600" />
                          <div>
                            <span class="text-sm font-medium text-gray-900">{{ doc.label }}</span>
                            <span class="text-xs text-gray-500 block">({{ doc.content_type || 'Document' }})</span>
                          </div>
                        </div>
                        <div class="flex items-center gap-1">
                          <button 
                            type="button" 
                            @click="selectedDocument = doc; selectedDocType = String(doc.id); selectedRfpDocumentId = doc.id"
                            class="px-2 py-1 text-xs rounded border-0 bg-blue-600 text-white hover:bg-blue-700 font-medium"
                          >
                            View
                          </button>
                          <button 
                            type="button" 
                            @click="downloadRfpDocument(doc)"
                            class="inline-flex items-center px-2 py-1 border border-blue-300 shadow-sm text-xs font-medium rounded text-blue-700 bg-white hover:bg-blue-50"
                          >
                            <Download class="h-3 w-3 mr-1" />
                            DL
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Divider -->
                <div v-if="rfpDocTabs.length > 0 && uploadedDocuments && uploadedDocuments.length > 0" class="border-t border-gray-300 my-4"></div>

                <!-- Vendor Uploaded Documents (Secondary) -->
                <div v-if="uploadedDocuments && uploadedDocuments.length > 0" class="space-y-3">
                  <div class="flex items-center justify-between">
                    <h4 class="text-sm font-medium text-gray-700">📎 Your Uploaded Documents</h4>
                    <span class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                      {{ uploadedDocuments.length }} file{{ uploadedDocuments.length !== 1 ? 's' : '' }}
                    </span>
                  </div>
                  <div v-for="(doc, index) in uploadedDocuments" :key="`vendor-doc-${index}-${doc.s3Id || doc.name}`" class="flex items-center justify-between p-2 bg-gray-50 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors">
                    <div class="flex items-center gap-2">
                      <CheckCircle2 v-if="doc.uploaded" class="h-4 w-4 text-green-600" />
                      <FileText v-else class="h-4 w-4 text-gray-500" />
                      <div>
                        <p class="text-sm font-medium text-gray-900">{{ doc.name || doc.fileName }}</p>
                        <p class="text-xs text-gray-500">{{ formatFileSize(doc.fileSize || doc.size || 0) }}</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-1">
                      <button 
                        v-if="doc.uploaded"
                        type="button" 
                        @click="downloadVendorDocument(doc)"
                        class="inline-flex items-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50"
                      >
                        <Download class="h-3 w-3 mr-1" />
                        Download
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Inline Document Viewer -->
                <div v-if="selectedDocument && selectedDocument.url" class="space-y-2">
                  <div class="flex items-center justify-between p-2 bg-blue-50 border border-blue-200 rounded-lg">
                    <div class="flex items-center gap-2">
                      <FileText class="h-4 w-4 text-blue-600" />
                      <span class="text-sm font-medium text-gray-900">Preview</span>
                    </div>
                    <button 
                      type="button" 
                      @click="selectedDocument = null; selectedDocType = ''; selectedRfpDocumentId = ''"
                      class="text-gray-400 hover:text-gray-600"
                    >
                      <X class="h-4 w-4" />
                    </button>
                  </div>
                  <div class="border border-blue-200 rounded-lg overflow-hidden bg-white" style="height: 500px;">
                    <template v-if="isImage(selectedDocument.content_type)">
                      <img :src="selectedDocument.url" alt="Selected document" class="w-full h-full object-contain bg-gray-50" />
                    </template>
                    <template v-else-if="isPdf(selectedDocument.content_type)">
                      <iframe 
                        :src="selectedDocument.url" 
                        class="w-full h-full" 
                        frameborder="0"
                        allow="fullscreen"
                        type="application/pdf"
                      />
                    </template>
                    <template v-else>
                      <div class="h-full flex items-center justify-center text-center p-6">
                        <div>
                          <FileText class="h-12 w-12 text-gray-400 mx-auto mb-3" />
                          <p class="text-sm text-gray-700 mb-3">Preview not available for this file type.</p>
                          <a :href="selectedDocument.url" target="_blank" class="inline-flex items-center px-4 py-2 border border-blue-300 shadow-sm text-sm font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50">
                            <Download class="h-4 w-4 mr-2" />
                            Open in new tab
                          </a>
                        </div>
                      </div>
                    </template>
                  </div>
                </div>
                <div v-else-if="rfpDocTabs.length > 0" class="text-center p-6 bg-gray-50 rounded-lg border border-gray-200">
                  <FileText class="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p class="text-sm text-gray-600">Select a document from the dropdown above to preview.</p>
                </div>
              </div>
            </div>
          </div>
          </div> <!-- End Sliding Panel -->
        </div> <!-- End Right Panel Container -->
    
    <!-- Success Modal -->
    <div v-if="showSuccessModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div class="p-6">
          <!-- Success Icon -->
          <div class="flex items-center justify-center w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full">
            <CheckCircle2 class="w-8 h-8 text-green-600" />
          </div>
          
          <!-- Success Message -->
          <div class="text-center">
            <h3 class="text-lg font-semibold text-gray-900 mb-2">
              🎉 Proposal Submitted Successfully!
            </h3>
            <p class="text-gray-600 mb-4">
              Your proposal has been received and is now under review.
            </p>
          </div>
          
          <!-- Submission Details -->
          <div class="bg-gray-50 rounded-lg p-4 mb-6">
            <h4 class="font-medium text-gray-900 mb-3">Submission Details</h4>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-600">RFP Number:</span>
                <span class="font-medium">{{ submissionDetails.rfpNumber }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Response ID:</span>
                <span class="font-medium">{{ submissionDetails.responseId }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Submitted By:</span>
                <span class="font-medium">{{ submissionDetails.vendorName }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Email:</span>
                <span class="font-medium">{{ submissionDetails.contactEmail }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">Submitted At:</span>
                <span class="font-medium">{{ formatDate(submissionDetails.submittedAt) }}</span>
              </div>
            </div>
          </div>
          
          <!-- Next Steps -->
          <div class="bg-blue-50 rounded-lg p-4 mb-6">
            <h4 class="font-medium text-blue-900 mb-2">What's Next?</h4>
            <ul class="text-sm text-blue-800 space-y-1">
              <li>• Your proposal is now under review</li>
              <li>• You will receive updates via email</li>
              <li>• Check your email for confirmation</li>
              <li>• Contact us if you have questions</li>
            </ul>
          </div>
          
          <!-- Action Buttons -->
          <div class="flex gap-3">
            <button 
              @click="closeSuccessModal"
              class="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Close
            </button>
            <button 
              @click="downloadSubmissionConfirmation"
              class="flex-1 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Download Confirmation
            </button>
          </div>
        </div>
      </div>
    </div>
    </div> <!-- End v-else -->
    </div> <!-- End w-full space-y-6 -->
  </div> <!-- End vendor-portal-standalone -->

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useStore } from 'vuex'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'

// Get current user from localStorage with Vuex fallback
const getCurrentUserId = () => {
  try {
    // First, try to get user from Vuex store (most reliable source)
    try {
      const store = useStore()
      const vuexUser = store.getters['auth/currentUser']
      if (vuexUser && vuexUser.id) {
        return vuexUser.id.toString()
      }
    } catch (vuexError) {
      // Ignore Vuex errors
    }
    
    // Fallback to localStorage if Vuex store is not available
    const currentUserFromStorage = localStorage.getItem('current_user')
    if (currentUserFromStorage) {
      const user = JSON.parse(currentUserFromStorage)
      const userId = user.id || user.user_id || user.userId || user.userid
      if (userId) {
        return userId.toString()
      }
    }
    
    return null
  } catch (error) {
    console.error('Error getting current user:', error)
    return null
  }
}
import { 
  Upload, 
  FileText, 
  Clock, 
  CheckCircle2, 
  User, 
  Building2,
  Save,
  Send,
  Download,
  AlertCircle,
  Loader2,
  DollarSign,
  Users,
  UserPlus,
  X,
  Shield,
  Award,
  Calendar
} from 'lucide-vue-next'
import { useToast } from '@/composables/useToast.js'
import { useRfpApi } from '@/composables/useRfpApi.js'
import RichResponseEditor from '@/components/rfp/RichResponseEditor.vue'
import Icons from '@/components_rfp/ui/Icons.vue'
import axios from 'axios'

// Toast notification
const { success: showSuccessToast, error: showErrorToast, warning: showWarningToast } = useToast()

const props = defineProps({
  previewPayload: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['exit-preview'])

// Authentication
const { getAuthHeaders } = useRfpApi()

const hasAuthToken = () => {
  if (typeof window === 'undefined') {
    return false
  }
  try {
    return Boolean(
      localStorage.getItem('session_token') ||
      localStorage.getItem('auth_token') ||
      localStorage.getItem('access_token')
    )
  } catch (error) {
    console.warn('Vendor Portal: unable to read auth tokens', error)
    return false
  }
}

const parseJsonResponse = async (response, fallbackMessage = 'Unexpected server response') => {
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    try {
      return await response.json()
    } catch (error) {
      throw new Error(fallbackMessage)
    }
  }
  const text = await response.text()
  throw new Error(text || fallbackMessage)
}

const VENDOR_PREVIEW_STORAGE_KEY = 'vendor_portal_preview_payload'

// Loading states
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const isLoading = ref(false)
const isSubmitting = ref(false)
const previewMode = ref(false)
const previewPayload = ref(null)
const appliedStandaloneClasses = ref(false)

// Right panel local toggle
const rightPanelTab = ref('details')
const rightPanelOpen = ref(false)

// Toggle right panel
const toggleRightPanel = () => {
  rightPanelOpen.value = !rightPanelOpen.value
}

// Form tabs state
const activeFormTab = ref('company')
const formTabs = [
  { id: 'company', label: 'Company Info', icon: '🏢' },
  { id: 'financial', label: 'Financial', icon: '💰' },
  { id: 'responses', label: 'RFP Responses', icon: '📝' },
  { id: 'compliance', label: 'Compliance', icon: '🛡️' },
  { id: 'documents', label: 'Documents', icon: '📄' },
  { id: 'team', label: 'Team', icon: '👥' }
]

// Navigate to next/previous tab
const goToNextTab = () => {
  const currentIndex = formTabs.findIndex(tab => tab.id === activeFormTab.value)
  if (currentIndex < formTabs.length - 1) {
    activeFormTab.value = formTabs[currentIndex + 1].id
    // Scroll to top of form
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const goToPreviousTab = () => {
  const currentIndex = formTabs.findIndex(tab => tab.id === activeFormTab.value)
  if (currentIndex > 0) {
    activeFormTab.value = formTabs[currentIndex - 1].id
    // Scroll to top of form
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const goToTab = (tabId) => {
  activeFormTab.value = tabId
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Check if tab is completed
const isTabCompleted = (tabId) => {
  const statusMap = {
    'company': completionStatus.value.company,
    'financial': completionStatus.value.financial,
    'responses': completionStatus.value.responses,
    'compliance': completionStatus.value.compliance,
    'documents': completionStatus.value.documents,
    'team': completionStatus.value.personnel
  }
  return statusMap[tabId] === 100
}

// Test mode detection
const isTestMode = computed(() => {
  const currentRoute = window.location.pathname
  return !previewMode.value && currentRoute === '/test-vendor-portal'
})

// RFP information
const rfpInfo = ref({
  rfpTitle: "Cloud Infrastructure Services RFP",
  rfpNumber: "RFP-2025-001",
  deadline: "August 1, 2025",
  budget: "$400,000 - $600,000",
  description: "",
  rfpType: "",
  category: "",
  criticality: ""
})

// Dynamic response fields based on RFP type
const dynamicResponseFields = ref([])
const dynamicResponseData = ref({})
const customDynamicFields = ref([])
const dynamicFieldErrors = ref({})

// Category-specific custom fields
const categoryCustomFields = ref({
  company: [],
  financial: [],
  compliance: [],
  documents: [],
  team: [],
  responses: []
})

// Category-specific custom field data
const categoryCustomFieldData = ref({
  company: {},
  financial: {},
  compliance: {},
  documents: {},
  team: {},
  responses: {}
})

const categoryCustomFieldPanelOpen = ref({
  company: false,
  financial: false,
  compliance: false,
  documents: false,
  team: false,
  responses: true
})

// New custom field template (will be reset per category)
const newCustomField = ref({
  label: '',
  name: '',
  type: 'text',
  value: '',
  fileData: null,
  description: '',
  required: false,
  category: 'company' // Track which category this field belongs to
})

const customFieldTypes = [
  { value: 'text', label: 'Text' },
  { value: 'textarea', label: 'Textarea' },
  { value: 'number', label: 'Number' },
  { value: 'decimal', label: 'Decimal' },
  { value: 'date', label: 'Date' },
  { value: 'email', label: 'Email' },
  { value: 'url', label: 'URL' },
  { value: 'file', label: 'File Upload' }
]

const getCustomFieldTypeLabel = (type) => {
  const normalized = (type || 'text').toLowerCase()
  const match = customFieldTypes.find(option => option.value === normalized)
  if (match) return match.label
  if (normalized === 'file_upload') return 'File Upload'
  return normalized.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase())
}

const allDynamicResponseFields = computed(() => [
  ...dynamicResponseFields.value,
  ...customDynamicFields.value
])

const normalizeFieldName = (label = '') => {
  return label
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

const ensureUniqueFieldName = (baseName, category = 'company') => {
  const categoryFields = categoryCustomFields.value[category] || []
  const existingNames = categoryFields.map(field => field.name || field.id)
  let candidate = baseName || `custom_field_${categoryFields.length + 1}`
  let counter = 1
  while (existingNames.includes(candidate)) {
    candidate = `${baseName}_${counter}`
    counter += 1
  }
  return candidate
}

const toggleCategoryFieldPanel = (category) => {
  categoryCustomFieldPanelOpen.value[category] = !categoryCustomFieldPanelOpen.value[category]
}

const resetNewCustomField = (category = 'company') => {
  newCustomField.value = {
    label: '',
    name: '',
    type: 'text',
    value: '',
    fileData: null,
    description: '',
    required: false,
    category: category
  }
}

const handleNewCustomFieldFileChange = async (event, category = 'company') => {
  try {
    const file = event.target.files?.[0]
    if (!file) {
      newCustomField.value.fileData = null
      newCustomField.value.value = null
      return
    }

    const dataUrl = await readFileAsDataUrl(file)
    newCustomField.value.fileData = {
      fileName: file.name,
      fileSize: file.size,
      contentType: file.type || 'application/octet-stream',
      dataUrl,
      uploadedAt: new Date().toISOString()
    }
    newCustomField.value.value = newCustomField.value.fileData
    newCustomField.value.category = category
  } catch (error) {
    console.error('Error reading file:', error)
    showErrorToast('Unable to read file. Please try again.')
  }
}

const addCustomFieldWithValue = (category = 'company') => {
  const label = (newCustomField.value.label || '').trim()
  if (!label) {
    showErrorToast('Please enter a label for the custom field.')
    return
  }

  const fieldType = newCustomField.value.type || 'text'
  const normalizedType = fieldType === 'file_upload' ? 'file' : fieldType
  const fieldCategory = category || newCustomField.value.category || 'company'
  
  // Validate value based on type
  let fieldValue = newCustomField.value.value
  if (normalizedType === 'file') {
    fieldValue = newCustomField.value.fileData
    if (!fieldValue) {
      showErrorToast('Please upload a file for this field.')
      return
    }
  } else {
    if (!fieldValue || (typeof fieldValue === 'string' && fieldValue.trim() === '')) {
      showErrorToast('Please enter a value for this field.')
      return
    }
  }

  let baseName = (newCustomField.value.name || '').trim()
  if (!baseName) {
    baseName = normalizeFieldName(label)
  }
  if (!baseName) {
    baseName = `custom_field_${Date.now()}`
  }
  const uniqueName = ensureUniqueFieldName(baseName, fieldCategory)

  const newField = {
    id: `custom_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    name: uniqueName,
    label,
    type: normalizedType,
    description: (newCustomField.value.description || '').trim(),
    required: !!newCustomField.value.required,
    custom: true,
    category: fieldCategory,
    _originalName: uniqueName,
    _uniqueKey: `${fieldCategory}_${uniqueName}`
  }

  // Store the value in category-specific data
  if (!categoryCustomFieldData.value[fieldCategory]) {
    categoryCustomFieldData.value[fieldCategory] = {}
  }
  categoryCustomFieldData.value[fieldCategory][uniqueName] = fieldValue

  // Add to category-specific fields
  if (!categoryCustomFields.value[fieldCategory]) {
    categoryCustomFields.value[fieldCategory] = []
  }
  categoryCustomFields.value[fieldCategory].push(newField)

  // Also add to legacy customDynamicFields for responses category (backward compatibility)
  if (fieldCategory === 'responses') {
    customDynamicFields.value.push(newField)
    dynamicResponseData.value[newField._uniqueKey] = fieldValue
  }

  resetNewCustomField(fieldCategory)
  updateCompletionStatus()
  debounceAutoSave()
  showSuccessToast(`Custom field "${label}" added to ${fieldCategory} section`)
}

// Keep old function for backward compatibility
const addCustomField = () => addCustomFieldWithValue('responses')

const removeCustomField = (fieldId, category = null) => {
  // If category is provided, remove from category-specific fields
  if (category && categoryCustomFields.value[category]) {
    const index = categoryCustomFields.value[category].findIndex(field => field.id === fieldId)
    if (index !== -1) {
      const field = categoryCustomFields.value[category][index]
      const originalName = field._originalName || field.name
      
      if (categoryCustomFieldData.value[category] && originalName) {
        delete categoryCustomFieldData.value[category][originalName]
      }
      
      categoryCustomFields.value[category].splice(index, 1)
      updateCompletionStatus()
      debounceAutoSave()
      return
    }
  }
  
  // Fallback to legacy customDynamicFields (for responses category)
  const index = customDynamicFields.value.findIndex(field => field.id === fieldId)
  if (index === -1) return

  const field = customDynamicFields.value[index]
  const fieldCategory = field.category || 'responses'
  const storageKey = field._uniqueKey || field.name
  const originalName = field._originalName || field.name

  // Remove from category-specific data
  if (categoryCustomFieldData.value[fieldCategory] && originalName) {
    delete categoryCustomFieldData.value[fieldCategory][originalName]
  }
  
  // Remove from legacy dynamicResponseData
  if (storageKey && dynamicResponseData.value[storageKey] !== undefined) {
    delete dynamicResponseData.value[storageKey]
  }
  if (originalName && dynamicResponseData.value[originalName] !== undefined) {
    delete dynamicResponseData.value[originalName]
  }
  if (storageKey) {
    clearDynamicFieldError(storageKey)
  }

  // Remove from category-specific fields
  if (categoryCustomFields.value[fieldCategory]) {
    const catIndex = categoryCustomFields.value[fieldCategory].findIndex(f => f.id === fieldId)
    if (catIndex !== -1) {
      categoryCustomFields.value[fieldCategory].splice(catIndex, 1)
    }
  }

  customDynamicFields.value.splice(index, 1)
  updateCompletionStatus()
  debounceAutoSave()
}

// Get unique field key for dynamic response fields
// This ensures each field has its own independent value in dynamicResponseData
const getFieldKey = (field, index) => {
  const aggregatedFields = allDynamicResponseFields.value
  const baseKey = field.name || field.id || field.label || `field_${index}`

  const duplicateIndex = aggregatedFields.findIndex((f, idx) =>
    idx !== index && (f.name === baseKey || f.id === baseKey)
  )

  const uniqueKey = duplicateIndex !== -1 || !field.name ? `${baseKey}_${index}` : baseKey

  if (!field._uniqueKey) {
    field._uniqueKey = uniqueKey
    field._originalName = field.name || field.id || baseKey // Store original for saving
    console.log(`[getFieldKey] Field ${index} - originalName: "${field._originalName}", uniqueKey: "${uniqueKey}"`)
  }

  return field._uniqueKey
}

const resolveFieldKey = (field, index) => field._uniqueKey || getFieldKey(field, index)

const getDynamicFieldInputClasses = (uniqueKey) => {
  const baseClasses = 'w-full p-3 border rounded-lg focus:outline-none focus:ring-2'
  if (dynamicFieldErrors.value[uniqueKey]) {
    return `${baseClasses} border-red-500 focus:ring-red-500 focus:border-red-500`
  }
  return `${baseClasses} border-gray-300 focus:ring-blue-500 focus:border-blue-500`
}

const setDynamicFieldError = (uniqueKey, message = '') => {
  if (!uniqueKey) return
  if (message) {
    dynamicFieldErrors.value = {
      ...dynamicFieldErrors.value,
      [uniqueKey]: message
    }
  } else if (dynamicFieldErrors.value[uniqueKey]) {
    const { [uniqueKey]: removed, ...rest } = dynamicFieldErrors.value
    dynamicFieldErrors.value = rest
  }
}

const clearDynamicFieldError = (uniqueKey) => {
  setDynamicFieldError(uniqueKey, '')
}

const validateDynamicField = (field, uniqueKey) => {
  const type = (field.type || 'text').toLowerCase()
  const value = dynamicResponseData.value[uniqueKey]
  const isEmpty = value === null || value === undefined || (typeof value === 'string' && value.trim() === '')
  let error = ''

  if (field.required) {
    if (type === 'file' || type === 'file_upload') {
      const hasFile = (value && typeof value === 'object' && (value.dataUrl || value.url || value.s3Id)) ||
        (typeof value === 'string' && value.trim().length > 0)
      if (!hasFile) {
        error = 'Please upload a file.'
      }
    } else if (isEmpty) {
      error = 'This field is required.'
    }
  }

  if (!error && !isEmpty) {
    switch (type) {
      case 'number':
      case 'integer':
      case 'decimal':
        if (Number.isNaN(Number(value))) {
          error = 'Enter a valid number.'
        }
        break
      case 'email':
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          error = 'Enter a valid email address.'
        }
        break
      case 'url':
        try {
          new URL(value)
        } catch {
          error = 'Enter a valid URL.'
        }
        break
      default:
        break
    }
  }

  setDynamicFieldError(uniqueKey, error)
  return !error
}

const validateAllDynamicFields = (showToast = true) => {
  let allValid = true
  allDynamicResponseFields.value.forEach((field, index) => {
    const uniqueKey = resolveFieldKey(field, index)
    const isValid = validateDynamicField(field, uniqueKey)
    if (!isValid) {
      allValid = false
    }
  })

  if (!allValid && showToast) {
    showErrorToast('Please correct the highlighted Additional Information fields.')
  }

  return allValid
}

const handleDynamicFieldBlur = (field, index) => {
  const uniqueKey = resolveFieldKey(field, index)
  validateDynamicField(field, uniqueKey)
}

const handleDynamicFieldInput = (field, index) => {
  clearDynamicFieldError(resolveFieldKey(field, index))
}

const handleDynamicFieldBlurAndSave = (field, index) => {
  handleDynamicFieldBlur(field, index)
  handleAutoSave()
}

const readFileAsDataUrl = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader()
  reader.onload = () => resolve(reader.result)
  reader.onerror = reject
  reader.readAsDataURL(file)
})

const handleDynamicFileChange = async (field, index, event) => {
  try {
    const file = event.target.files?.[0]
    const uniqueKey = resolveFieldKey(field, index)

    if (!file) {
      dynamicResponseData.value[uniqueKey] = null
      clearDynamicFieldError(uniqueKey)
      handleAutoSave()
      return
    }

    const dataUrl = await readFileAsDataUrl(file)
    dynamicResponseData.value[uniqueKey] = {
      fileName: file.name,
      fileSize: file.size,
      contentType: file.type || 'application/octet-stream',
      dataUrl,
      uploadedAt: new Date().toISOString()
    }
    validateDynamicField(field, uniqueKey)
    handleAutoSave()
    console.log(`[handleDynamicFileChange] File uploaded for field "${field.label || field.name}": ${file.name}`)
  } catch (error) {
    console.error('Error reading file:', error)
    showErrorToast('Unable to read file. Please try again.')
  }
}

const clearDynamicFileValue = (field, index) => {
  const uniqueKey = resolveFieldKey(field, index)
  dynamicResponseData.value[uniqueKey] = null
  clearDynamicFieldError(uniqueKey)
  handleAutoSave()
}

const downloadDynamicFileValue = (field, index) => {
  const uniqueKey = resolveFieldKey(field, index)
  const fileData = dynamicResponseData.value[uniqueKey]
  if (!fileData) {
    showErrorToast('No file available to download.')
    return
  }

  if (typeof fileData === 'string') {
    if (/^https?:\/\//i.test(fileData)) {
      window.open(fileData, '_blank')
    } else {
      showErrorToast('Unable to download this file reference.')
    }
    return
  }

  if (fileData.dataUrl) {
    const link = document.createElement('a')
    link.href = fileData.dataUrl
    link.download = fileData.fileName || `${uniqueKey}.file`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } else if (fileData.url) {
    window.open(fileData.url, '_blank')
  }
}

const serializeCustomFieldDefinitions = () => customDynamicFields.value.map(field => ({
  id: field.id,
  name: field.name,
  label: field.label,
  type: field.type,
  description: field.description,
  required: field.required,
  custom: true
}))

const upsertCustomFieldDefinition = (definition) => {
  if (!definition) return null
  const name = definition.name || definition.id
  if (!name) return null

  const existing = customDynamicFields.value.find(field => field.name === name)
  if (existing) {
    return existing
  }

  const hydratedField = {
    id: definition.id || `custom_${name}_${Date.now()}`,
    name,
    label: definition.label || name,
    type: definition.type || 'text',
    description: definition.description || '',
    required: !!definition.required,
    custom: true,
    _originalName: name,
    _uniqueKey: name
  }

  customDynamicFields.value.push(hydratedField)
  return hydratedField
}

const hydrateCustomFieldDefinitions = (definitions = []) => {
  if (!Array.isArray(definitions)) return
  definitions.forEach(definition => {
    upsertCustomFieldDefinition(definition)
  })
}

const buildDynamicFieldValueMap = () => {
  const mappedValues = {}
  allDynamicResponseFields.value.forEach((field, idx) => {
    const uniqueKey = field._uniqueKey || getFieldKey(field, idx)
    // Use the field's name (normalized from label) as the JSON key
    // This ensures valid JSON keys while preserving the user's intent
    const fieldName = field._originalName || field.name || field.id || uniqueKey
    const value = dynamicResponseData.value[uniqueKey]

    // Only include fields with actual values
    if (value !== undefined && value !== null) {
      // Handle empty strings - include them if they're not required
      if (value === '' && field.required) {
        // Skip required empty fields
        return
      }
      
      // For file uploads, ensure proper serialization
      if (field.type === 'file' || field.type === 'file_upload') {
        if (typeof value === 'object' && value !== null) {
          // File object with dataUrl, fileName, etc.
          mappedValues[fieldName] = {
            fileName: value.fileName || '',
            fileSize: value.fileSize || 0,
            contentType: value.contentType || 'application/octet-stream',
            dataUrl: value.dataUrl || '',
            uploadedAt: value.uploadedAt || new Date().toISOString()
          }
        } else if (typeof value === 'string' && value.trim() !== '') {
          // String URL or data URL
          mappedValues[fieldName] = value
        }
      } else {
        // For all other field types, save the value directly
        mappedValues[fieldName] = value
      }
      
      console.log(`[buildDynamicFieldValueMap] Field "${field.label || fieldName}" (key: "${fieldName}") ->`, 
        field.type === 'file' || field.type === 'file_upload' ? `[File: ${value?.fileName || 'N/A'}]` : value)
    }
  })
  
  console.log(`[buildDynamicFieldValueMap] Total fields mapped: ${Object.keys(mappedValues).length}`)
  return mappedValues
}

// RFP documents (IDs from backend) and resolved tabs
const rfpDocuments = ref([]) // raw JSON from backend (IDs or objects with id)
const rfpDocTabs = ref([]) // [{ id, label, url, content_type }]

// Dropdown state for RFP documents
const selectedRfpDocumentId = ref("")
const selectedRfpDocument = computed(() => {
  if (!selectedRfpDocumentId.value) return null
  return rfpDocTabs.value.find(doc => doc.id == selectedRfpDocumentId.value)
})

// Form data - comprehensive vendor information
const formData = ref({
  // Basic Company Information
  companyName: "",
  legalName: "",
  businessType: "",
  industrySector: "",
  
  // Contact Information
  contactName: "",
  contactTitle: "",
  email: "",
  phone: "",
  
  // Company Details
  website: "",
  taxId: "",
  dunsNumber: "",
  incorporationDate: "",
  
  // Company Size & Financials
  employeeCount: "",
  annualRevenue: "",
  headquartersAddress: "",
  headquartersCountry: "",
  yearsInBusiness: "",
  companyDescription: "",
  
  // Financial Information
  proposedValue: "",
  currency: "USD",
  pricingBreakdown: "",
  paymentTerms: "",
  projectDuration: "",
  creditRating: "",
  insuranceCoverage: "",
  
  // Team Information
  totalTeamSize: "",
  teamStructure: "",
  projectMethodology: "",
  communicationPlan: "",
  
  // Compliance & Certifications
  iso9001: false,
  iso27001: false,
  iso14001: false,
  soc2: false,
  pciDss: false,
  hippa: false,
  dataSecurityMeasures: "",
  complianceStandards: "",
  professionalLiability: "",
  generalLiability: "",
  references: [
    {
      companyName: "",
      contactPerson: "",
      email: "",
      phone: "",
      projectDescription: ""
    }
  ]
})

// Track hidden (non-mandatory) fields
const hiddenFields = ref({
  website: false,
  dunsNumber: false,
  creditRating: false,
  insuranceCoverage: false,
  isoCertifications: false,
  industryCertifications: false
})

// Track hidden fields for key personnel (index-based)
const hiddenPersonnelFields = ref({}) // { personIndex: { phone: false, education: false, certifications: false } }

// Track hidden fields for references (index-based)
const hiddenReferenceFields = ref({}) // { referenceIndex: { phone: false } }

// Track hidden dynamic response fields (by field key)
const hiddenDynamicFields = ref({}) // { fieldKey: true }

// Track hidden category custom fields (by category and field ID)
const hiddenCategoryFields = ref({
  company: {},
  financial: {},
  compliance: {},
  team: {},
  documents: {},
  responses: {}
}) // { category: { fieldId: true } }

const hiddenCustomFields = ref(new Set())

const isPreviewReadonly = computed(() => previewMode.value)

// Function to hide a dynamic field (both RFP-defined and custom)
const hideDynamicField = (fieldKey, fieldIndex = null) => {
  hiddenDynamicFields.value[fieldKey] = true
  
  // Clear the field value when hiding
  if (dynamicResponseData.value[fieldKey] !== undefined) {
    delete dynamicResponseData.value[fieldKey]
  }
  
  // Also clear from customDynamicFields if it's a custom field
  if (fieldIndex !== null) {
    const customFieldIndex = customDynamicFields.value.findIndex(f => f.id === fieldKey || f._uniqueKey === fieldKey)
    if (customFieldIndex !== -1) {
      // Don't remove from array, just mark as hidden
      // The field will be hidden via v-if in template
    }
  }
  
  console.log(`Dynamic field ${fieldKey} hidden from form`)
  showSuccessToast('Field Removed', `The field has been removed from the form.`)
}

// Helper to check if a dynamic field is hidden
const isDynamicFieldHidden = (fieldKey) => {
  return hiddenDynamicFields.value[fieldKey] || false
}

// Function to hide a category custom field
const hideCategoryField = (fieldId, category) => {
  if (!hiddenCategoryFields.value[category]) {
    hiddenCategoryFields.value[category] = {}
  }
  hiddenCategoryFields.value[category][fieldId] = true
  
  // Clear the field value when hiding
  const field = categoryCustomFields.value[category]?.find(f => f.id === fieldId)
  if (field) {
    const fieldName = field._originalName || field.name
    if (categoryCustomFieldData.value[category] && fieldName) {
      delete categoryCustomFieldData.value[category][fieldName]
    }
  }
  
  console.log(`Category field ${fieldId} hidden from ${category} section`)
  showSuccessToast('Field Removed', `The field has been removed from the form.`)
}

// Helper to check if a category custom field is hidden
const isCategoryFieldHidden = (fieldId, category) => {
  return hiddenCategoryFields.value[category]?.[fieldId] || false
}

// Function to hide a non-mandatory field
const hideField = (fieldName) => {
  if (fieldName in hiddenFields.value) {
    hiddenFields.value[fieldName] = true
    // Clear the field value when hiding
    if (fieldName in formData.value) {
      if (fieldName === 'website' || fieldName === 'dunsNumber' || fieldName === 'creditRating' || fieldName === 'insuranceCoverage') {
        formData.value[fieldName] = ''
      } else if (fieldName === 'isoCertifications') {
        formData.value.iso9001 = false
        formData.value.iso27001 = false
        formData.value.iso14001 = false
      } else if (fieldName === 'industryCertifications') {
        formData.value.soc2 = false
        formData.value.pciDss = false
        formData.value.hippa = false
      }
    }
    console.log(`Field ${fieldName} hidden from form`)
    showSuccessToast('Field Removed', `The ${fieldName} field has been removed from the form.`)
  }
}

// Function to hide a field for a specific person
const hidePersonnelField = (personIndex, fieldName) => {
  if (!hiddenPersonnelFields.value[personIndex]) {
    hiddenPersonnelFields.value[personIndex] = {}
  }
  hiddenPersonnelFields.value[personIndex][fieldName] = true
  
  // Clear the field value
  if (keyPersonnel.value && keyPersonnel.value[personIndex]) {
    if (fieldName === 'phone') {
      keyPersonnel.value[personIndex].phone = ''
    } else if (fieldName === 'education') {
      keyPersonnel.value[personIndex].education = ''
    } else if (fieldName === 'certifications') {
      keyPersonnel.value[personIndex].certifications = []
    }
  }
  
  console.log(`Personnel field ${fieldName} hidden for person ${personIndex}`)
  showSuccessToast('Field Removed', `The ${fieldName} field has been removed.`)
}

// Function to hide a field for a specific reference
const hideReferenceField = (referenceIndex, fieldName) => {
  if (!hiddenReferenceFields.value[referenceIndex]) {
    hiddenReferenceFields.value[referenceIndex] = {}
  }
  hiddenReferenceFields.value[referenceIndex][fieldName] = true
  
  // Clear the field value
  if (formData.value.references && formData.value.references[referenceIndex]) {
    if (fieldName === 'phone') {
      formData.value.references[referenceIndex].phone = ''
    }
  }
  
  console.log(`Reference field ${fieldName} hidden for reference ${referenceIndex}`)
  showSuccessToast('Field Removed', `The ${fieldName} field has been removed.`)
}

// Helper function to check if a personnel field is hidden
const isPersonnelFieldHidden = (personIndex, fieldName) => {
  return hiddenPersonnelFields.value[personIndex]?.[fieldName] || false
}

// Helper function to check if a reference field is hidden
const isReferenceFieldHidden = (referenceIndex, fieldName) => {
  return hiddenReferenceFields.value[referenceIndex]?.[fieldName] || false
}

// Invitation data
const invitationData = ref({
  rfpId: null,
  vendorId: null,
  invitationId: null,
  org: "",
  vendorName: "",
  contactEmail: "",
  contactPhone: "",
  isOpenRfp: false
})

// UTM parameters for tracking
const utmParameters = ref({})

// Dynamic URL building
const buildDynamicUrl = () => {
  const baseUrl = window.location.origin + window.location.pathname
  const params = new URLSearchParams()
  
  // Add base parameters
  params.append('submissionSource', 'open')
  if (invitationData.value.rfpId) {
    params.append('rfpId', invitationData.value.rfpId)
  }
  
  // Add UTM parameters
  Object.entries(utmParameters.value).forEach(([key, value]) => {
    if (value) {
      params.append(key, value)
    }
  })
  
  // Add vendor data as it's filled
  if (formData.value.contactName) {
    params.append('vendorName', formData.value.contactName)
  }
  if (formData.value.email) {
    params.append('contactEmail', formData.value.email)
  }
  if (formData.value.phone) {
    params.append('contactPhone', formData.value.phone)
  }
  if (formData.value.companyName) {
    params.append('org', formData.value.companyName)
  }
  
  return `${baseUrl}?${params.toString()}`
}

// Update URL as form is filled
const updateUrl = () => {
  if (previewMode.value) {
    return
  }
  if (invitationData.value.isOpenRfp) {
    const newUrl = buildDynamicUrl()
    if (newUrl !== window.location.href) {
      window.history.replaceState({}, '', newUrl)
    }
  }
}

// RFP responses - dynamic based on evaluation criteria
const responses = ref({})
const createEmptyResponseEntry = () => ({
  htmlContent: '',
  attachments: []
})
 
const cloneDeep = (value, fallback) => {
  try {
    return JSON.parse(JSON.stringify(value ?? fallback))
  } catch (error) {
    return fallback
  }
}
 
const sanitizeResponseAttachment = (attachment = {}, criteriaId = null) => {
  if (!attachment) {
    return null
  }
 
  const id =
    attachment.id ??
    attachment.s3_file_id ??
    (attachment.url ? `${attachment.url}-${Math.random().toString(36).slice(2)}` : Math.random().toString(36).slice(2))
 
  return {
    id: String(id),
    url: attachment.url || attachment.document_url || attachment.attachmentUrl || '',
    key: attachment.key || attachment.s3_key || null,
    fileName: attachment.fileName || attachment.storedName || attachment.originalFilename || attachment.name || 'attachment',
    originalFilename: attachment.originalFilename || attachment.fileName || attachment.storedName || attachment.name || 'attachment',
    fileSize: attachment.fileSize || attachment.size || null,
    contentType: attachment.contentType || attachment.mimeType || '',
    uploadedAt: attachment.uploadedAt || attachment.upload_date || new Date().toISOString(),
    isImage: attachment.isImage ?? Boolean((attachment.contentType || attachment.mimeType || '').startsWith('image/')),
    criteriaId: criteriaId !== null ? String(criteriaId) : (attachment.criteriaId ? String(attachment.criteriaId) : null),
    responseId: attachment.responseId || null
  }
}
 
const normalizeResponseEntry = (value, criteriaId = null) => {
  if (!value) {
    return createEmptyResponseEntry()
  }
 
  if (typeof value === 'string') {
    return {
      htmlContent: value,
      attachments: []
    }
  }
 
  const normalized = {
    ...value,
    htmlContent: value.htmlContent || value.text || ''
  }
 
  const attachments = Array.isArray(value.attachments)
    ? value.attachments
        .map(item => sanitizeResponseAttachment(item, criteriaId))
        .filter(item => item && item.url)
    : []
 
  normalized.attachments = attachments
 
  return normalized
}
 
const responseHasContent = (value) => {
  const normalized = normalizeResponseEntry(value)
  const html = normalized.htmlContent || ''
  const stripped = html.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, '').trim()
  const hasTable = html.includes('<table')
  const hasAttachments = normalized.attachments && normalized.attachments.length > 0
  return Boolean(stripped) || hasTable || hasAttachments
}
 
const getCriteriaResponse = (criteriaId) => {
  const key = String(criteriaId)
  return normalizeResponseEntry(responses.value?.[key], key)
}
 
const setCriteriaResponse = (criteriaId, value) => {
  const key = String(criteriaId)
  const normalized = normalizeResponseEntry(value, key)
  console.log('VendorPortal: setCriteriaResponse', {
    criteriaId: key,
    value,
    normalized,
    hasHtmlContent: !!normalized.htmlContent,
    htmlContentLength: normalized.htmlContent?.length || 0,
    attachmentsCount: normalized.attachments?.length || 0,
    attachments: normalized.attachments
  })
  responses.value = {
    ...responses.value,
    [key]: normalized
  }
  console.log('VendorPortal: Updated responses for criteria', key, {
    totalResponses: Object.keys(responses.value).length,
    thisResponse: responses.value[key]
  })
}
 
// Draft data for auto-save
const draftData = ref({
  companyInfo: {},
  responses: {},
  documents: [],
  keyPersonnel: [],
  lastSaved: null
})

// Completion status - calculated dynamically
const completionStatus = ref({
  company: 0,
  financial: 0,
  responses: 0,
  documents: 0,
  personnel: 0,
  compliance: 0
})

// Evaluation criteria - loaded from backend
const evaluationCriteria = ref([])

// Document management - changed to array structure like Phase1Creation
const documentUploads = ref({})
const documentUrls = ref({})
const uploadedDocuments = ref([]) // Changed to array for dynamic document management
const uploadingDocuments = ref({}) // Track which documents are currently uploading
const isMergingDocuments = ref(false)
const isUploadingDocuments = ref(false)
const perDocUploading = ref({})
const selectedDocuments = ref(new Set()) // Track selected document indices for merging

// Separate regular documents from merged documents
const regularDocuments = computed(() => {
  return uploadedDocuments.value.filter(doc => !doc.isMerged)
})

const mergedDocuments = computed(() => {
  return uploadedDocuments.value.filter(doc => doc.isMerged)
})

// New document form
const newDocument = ref({
  name: '',
  file: null,
  fileName: '',
  fileSize: 0,
  documentType: 'rfps' // Default document type: rfps, contract, sl, bcp_drp
})

// Document type options
const documentTypeOptions = [
  { value: 'rfps', label: 'RFP' },
  { value: 'contract', label: 'Contract' },
  { value: 'sl', label: 'SLA' },i
  { value: 'bcp_drp', label: 'BCP/DRP' }
]

// Flag to prevent recursive calls
let isEnsuringReactiveData = false

// Ensure all reactive data is properly initialized
const ensureReactiveData = () => {
  // Prevent recursive calls
  if (isEnsuringReactiveData) {
    return
  }
  
  try {
    isEnsuringReactiveData = true
    
    // Ensure evaluationCriteria is always an array
    if (!Array.isArray(evaluationCriteria.value)) {
      evaluationCriteria.value = []
    }
    
    // Ensure responses is always an object (but don't normalize to avoid recursive updates)
    if (typeof responses.value !== 'object' || responses.value === null) {
      responses.value = {}
    }
    // Note: Normalization removed to prevent recursive updates
    // Normalization should only happen when loading data from backend
 
    
    // Ensure uploadedDocuments is always an array
    if (!Array.isArray(uploadedDocuments.value)) {
      uploadedDocuments.value = []
    }
    
    // Ensure uploadingDocuments is always an object
    if (typeof uploadingDocuments.value !== 'object' || uploadingDocuments.value === null) {
      uploadingDocuments.value = {}
    }
    
    // Ensure keyPersonnel is always an array
    if (!Array.isArray(keyPersonnel.value)) {
      keyPersonnel.value = []
    }
    
    // Ensure formData.references is always an array
    if (!Array.isArray(formData.value.references)) {
      formData.value.references = []
    }
    
    // Ensure formData is always an object
    if (typeof formData.value !== 'object' || formData.value === null) {
      formData.value = {}
    }
    
    // Ensure completionStatus is always an object
    if (typeof completionStatus.value !== 'object' || completionStatus.value === null) {
      completionStatus.value = {
        company: 0,
        financial: 0,
        responses: 0,
        documents: 0,
        personnel: 0,
        compliance: 0
      }
    }

    if (!(hiddenCustomFields.value instanceof Set)) {
      hiddenCustomFields.value = new Set()
    }
    
    // Ensure invitationData is always an object
    if (typeof invitationData.value !== 'object' || invitationData.value === null) {
      invitationData.value = {
        rfpId: null,
        vendorId: null,
        invitationId: null,
        org: "",
        vendorName: "",
        contactEmail: "",
        contactPhone: "",
        isOpenRfp: false
      }
    }
    
    console.log('✅ Reactive data ensured to be properly initialized')
  } catch (error) {
    console.error('❌ Error ensuring reactive data:', error)
  } finally {
    isEnsuringReactiveData = false
  }
}

// Document upload state
const uploadStates = ref({})

// Track file input refs
const fileInputRefs = ref({})

// Reset file input after successful upload
const resetFileInput = (documentType) => {
  const fileInput = fileInputRefs.value[documentType]
  if (fileInput) {
    fileInput.value = ''
  }
}

// Document viewer state
const selectedDocType = ref("")
const selectedDocument = ref(null)
const docTypeLabels = {
  technical_proposal: 'Technical Proposal',
  pricing_sheet: 'Pricing Sheet',
  company_profile: 'Company Profile',
  certifications: 'Certifications'
}

const selectedDocTypeLabel = computed(() => {
  return docTypeLabels[selectedDocType.value] || ''
})

const isPdf = (mime) => typeof mime === 'string' && mime.includes('pdf')
const isImage = (mime) => typeof mime === 'string' && (
  mime.includes('png') || mime.includes('jpg') || mime.includes('jpeg') || mime.includes('gif')
)

const viewDocument = (type) => {
  try {
    const doc = uploadedDocuments.value?.[type]
    if (!doc) return
    selectedDocType.value = type
    selectedDocument.value = doc
  } catch (e) {
    console.error('Error setting selected document', e)
  }
}

// Download RFP document
const downloadRfpDocument = async (doc) => {
  try {
    if (!doc.url) {
      showErrorToast('Document URL not available')
      return
    }
    
    console.log('📥 Downloading RFP document:', doc.label)
    
    // Open the document URL in a new tab for download
    window.open(doc.url, '_blank')
    showSuccessToast(`Downloading ${doc.label}`)
  } catch (error) {
    console.error('Error downloading RFP document:', error)
    showErrorToast('Failed to download document')
  }
}

// Handle RFP document dropdown selection
const onRfpDocumentSelect = () => {
  if (selectedRfpDocumentId.value === "all") {
    console.log('📋 View All Documents selected')
    // Clear the selected document to show all documents
    selectedDocument.value = null
    selectedDocType.value = ""
    showSuccessToast(`Showing all ${rfpDocTabs.value.length} documents`)
  } else if (selectedRfpDocument.value) {
    console.log('📋 Selected RFP document:', selectedRfpDocument.value)
    // Auto-load the document into the viewer
    selectedDocument.value = selectedRfpDocument.value
    selectedDocType.value = String(selectedRfpDocument.value.id)
  }
}

// Resolve RFP documents (IDs) to file metadata from backend
const resolveRfpDocumentTabs = async () => {
  try {
    console.log('🔍 Resolving RFP document tabs from:', rfpDocuments.value)
    
    // Normalize to array of IDs from any JSON shape
    let ids = []
    if (Array.isArray(rfpDocuments.value)) {
      ids = rfpDocuments.value.map(item => typeof item === 'object' ? (item.id || item.file_id || item) : item)
    } else if (rfpDocuments.value && typeof rfpDocuments.value === 'object') {
      ids = Object.values(rfpDocuments.value).map(item => typeof item === 'object' ? (item.id || item.file_id) : item)
    }

    ids = ids.filter(Boolean)
    console.log('🔍 Extracted IDs:', ids)
    
    if (ids.length === 0) {
      console.log('⚠️ No valid document IDs found')
      rfpDocTabs.value = []
      return
    }

    // Fetch each file metadata via existing endpoint
    const fetches = ids.map(async (id) => {
      try {
        console.log(`📥 Fetching metadata for file ID: ${id}`)
        
        // Try the S3Files endpoint first (for RFP documents)
        const res = await fetch(`${API_BASE_URL}/s3-files/${id}/`, {
          headers: getAuthHeaders()
        })
        const data = await res.json()
        console.log(`📥 Response for ID ${id}:`, data)
        
        if (data.success && data.s3_file) {
          return {
            id,
            label: data.s3_file.file_name || `File ${id}`,
            url: data.s3_file.url,
            content_type: data.s3_file.file_type
          }
        } else {
          // Fallback: try the file_operations endpoint
          console.log(`⚠️ S3Files endpoint failed for ID ${id}, trying file_operations endpoint`)
          const fallbackRes = await fetch(`${API_BASE_URL}/s3/files/${id}/`, {
            headers: getAuthHeaders()
          })
          const fallbackData = await fallbackRes.json()
          
          if (fallbackData.success && fallbackData.file_operation) {
            return {
              id,
              label: fallbackData.file_operation.file_name || `File ${id}`,
              url: fallbackData.file_operation.s3_url,
              content_type: fallbackData.file_operation.content_type || fallbackData.file_operation.file_type
            }
          } else {
            // Final fallback: create a basic document entry with the ID
            console.log(`⚠️ No metadata found for ID ${id}, creating fallback entry`)
            return {
              id,
              label: `Document ${id}`,
              url: `#document-${id}`, // Placeholder URL
              content_type: 'unknown'
            }
          }
        }
      } catch (e) {
        console.error('Failed to load file metadata', id, e)
        // Return a fallback entry even if the request fails
        return {
          id,
          label: `Document ${id}`,
          url: `#document-${id}`,
          content_type: 'unknown'
        }
      }
    })

    const results = (await Promise.all(fetches)).filter(Boolean)
    console.log('✅ Resolved document tabs:', results)
    rfpDocTabs.value = results
  } catch (e) {
    console.error('Error resolving RFP document tabs', e)
  }
}

const applyPreviewPayload = async (payload) => {
  if (!payload) return
  previewMode.value = true
  previewPayload.value = payload

  if (payload.rfpInfo) {
    rfpInfo.value = {
      ...rfpInfo.value,
      ...payload.rfpInfo
    }
  }

  if (payload.timeline?.deadline) {
    rfpInfo.value.deadline = payload.timeline.deadline
  }

  if (Array.isArray(payload.evaluationCriteria)) {
    evaluationCriteria.value = payload.evaluationCriteria.map((criterion, index) => ({
      id: criterion.id || `preview-criteria-${index}`,
      title: criterion.title || criterion.name || `Criterion ${index + 1}`,
      description: criterion.description || '',
      weight: Number(criterion.weight) || 0,
      required: Boolean(criterion.required),
      type: criterion.type || 'text'
    }))
    evaluationCriteria.value.forEach(criterion => {
      setCriteriaResponse(criterion.id, createEmptyResponseEntry())
    })
  } else {
    evaluationCriteria.value = []
  }

  if (Array.isArray(payload.dynamicResponseFields)) {
    dynamicResponseFields.value = payload.dynamicResponseFields
  }

  if (payload.categoryCustomFields) {
    const categories = ['company', 'financial', 'compliance', 'documents', 'team', 'responses']
    const nextFields = { ...categoryCustomFields.value }
    categories.forEach(category => {
      nextFields[category] = payload.categoryCustomFields[category] || []
    })
    categoryCustomFields.value = nextFields
  }

  if (payload.categoryCustomFieldData) {
    const categories = ['company', 'financial', 'compliance', 'documents', 'team', 'responses']
    const nextData = { ...categoryCustomFieldData.value }
    categories.forEach(category => {
      nextData[category] = payload.categoryCustomFieldData[category] || {}
    })
    categoryCustomFieldData.value = nextData
  }

  if (payload.hiddenFields) {
    hiddenFields.value = {
      ...hiddenFields.value,
      ...payload.hiddenFields
    }
  }

  if (Array.isArray(payload.hiddenCustomFields)) {
    hiddenCustomFields.value = new Set(payload.hiddenCustomFields)
  }

  if (Array.isArray(payload.documents)) {
    rfpDocuments.value = payload.documents
    await resolveRfpDocumentTabs()
  } else {
    rfpDocuments.value = []
    rfpDocTabs.value = []
  }
}

const loadPreviewData = async () => {
  isLoading.value = true
  try {
    const payloadRaw = localStorage.getItem(VENDOR_PREVIEW_STORAGE_KEY)
    if (!payloadRaw) {
      showError('Preview Unavailable', 'Preview data not found. Please reopen the preview from the RFP builder.')
      showErrorToast('Preview data missing. Close this tab and try again.')
      return
    }

    const payload = JSON.parse(payloadRaw)
    await applyPreviewPayload(payload)
    showInfo('Preview Mode', 'You are viewing the vendor portal preview. Actions are read-only in this mode.')
  } catch (error) {
    console.error('Error loading preview data:', error)
    showError('Preview Error', 'Unable to load preview data. Please reopen the preview from the RFP builder.')
    showErrorToast('Unable to load preview data.')
  } finally {
    isLoading.value = false
  }
}

// Document upload methods
const handleDocumentUpload = async (documentType, file) => {
  try {
    // Ensure uploadStates is initialized for this document type
    if (!uploadStates.value[documentType]) {
      uploadStates.value[documentType] = {
        isUploading: false,
        progress: 0,
        error: null
      }
    }
    
    // Set uploading state
    uploadingDocuments.value[documentType] = true
    uploadStates.value[documentType].isUploading = true
    uploadStates.value[documentType].error = null

    // Prepare form data
    const uploadFormData = new FormData()
    uploadFormData.append('file', file)
    uploadFormData.append('documentType', documentType) // Backend expects documentType
    uploadFormData.append('rfpId', invitationData.value.rfpId) // Backend expects rfpId
    
    // Debug: Log FormData contents
    console.log('📋 FormData contents:')
    for (let [key, value] of uploadFormData.entries()) {
      if (value instanceof File) {
        console.log(`  ${key}: File(${value.name}, ${value.size} bytes, ${value.type})`)
      } else {
        console.log(`  ${key}: ${value}`)
      }
    }
    
    // Use vendorId if available
    // For open RFP, we might not have either, which is fine
    // The backend will create these records if needed
    if (invitationData.value.vendorId) {
      uploadFormData.append('vendorId', invitationData.value.vendorId)
    }
    
    // Add submission source for open RFP
    if (invitationData.value.isOpenRfp) {
      uploadFormData.append('submissionSource', 'open')
    }
    
    console.log('📤 Uploading document:', {
      documentType,
      filename: file.name,
      size: file.size,
      rfpId: invitationData.value.rfpId,
      vendorId: invitationData.value.vendorId,
      invitationId: invitationData.value.invitationId
    })
    
    // For FormData uploads, we need to exclude Content-Type from headers
    // as the browser needs to set it automatically with the proper boundary
    const authHeaders = getAuthHeaders()
    const { 'Content-Type': _, ...headersWithoutContentType } = authHeaders
    
    const response = await fetch(`${API_BASE_URL}/rfp-responses/upload-document/`, {
      method: 'POST',
      headers: headersWithoutContentType,
      body: uploadFormData
    })
    
    // Check if response is ok before parsing JSON
    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ Upload failed with status:', response.status, errorText)
      throw new Error(`Upload failed with status ${response.status}: ${errorText}`)
    }
    
    const data = await response.json()
    console.log('📥 Upload response:', data)
    
    if (data.success) {
      // Find the document in the array and update it
      const docIndex = uploadedDocuments.value.findIndex(doc => doc.fileName === file.name && !doc.uploaded)
      if (docIndex !== -1) {
        uploadedDocuments.value[docIndex].uploaded = true
        uploadedDocuments.value[docIndex].s3Id = data.document_id || data.s3_file_id
        uploadedDocuments.value[docIndex].url = data.document_url || data.s3_url
      } else {
        // If not found, add as new document
        uploadedDocuments.value.push({
          name: data.document_name || file.name,
          fileName: data.filename || file.name,
          fileSize: data.file_size || file.size,
          fileType: file.type,
          url: data.document_url || data.s3_url,
          uploaded: true,
          s3Id: data.document_id || data.s3_file_id,
          file: null,
          isMerged: false
        })
      }
      
      showSuccessToast(`Document "${file.name}" uploaded successfully to S3`)
      updateCompletionStatus()
      
      // Reset file input through state
      uploadStates.value[documentType].progress = 100
    } else {
      uploadStates.value[documentType].error = data.error || 'Failed to upload document'
      console.error('Upload failed:', data.error)
      showErrorToast(data.error || 'Failed to upload document')
    }
  } catch (error) {
    uploadStates.value[documentType].error = 'Network error. Please try again.'
    console.error('Error uploading document:', error)
    showErrorToast('Network error. Please try again.')
  } finally {
    // Reset states
    uploadingDocuments.value[documentType] = false
    uploadStates.value[documentType].isUploading = false
  }
}

const uploadResponseAttachment = async (criteriaId, file, options = {}) => {
  console.log('VendorPortal: uploadResponseAttachment called', {
    criteriaId,
    fileName: file.name,
    fileSize: file.size,
    fileType: file.type,
    options,
    rfpId: invitationData.value.rfpId,
    vendorId: invitationData.value.vendorId,
    invitationId: invitationData.value.invitationId
  })
 
  if (!criteriaId || !file) {
    console.error('VendorPortal: Missing criteria or file for attachment upload', { criteriaId, file })
    throw new Error('Missing criteria or file for attachment upload')
  }
 
  if (!invitationData.value.rfpId) {
    console.error('VendorPortal: Missing RFP ID for attachment upload', invitationData.value)
    showErrorToast('Unable to determine RFP identifier. Please refresh the page and try again.')
    throw new Error('Unable to determine RFP ID for attachment upload')
  }
 
  try {
    const attachmentFormData = new FormData()
    attachmentFormData.append('file', file)
    attachmentFormData.append('criteriaId', String(criteriaId))
 
    if (invitationData.value.rfpId) {
      attachmentFormData.append('rfpId', invitationData.value.rfpId)
    }
    if (invitationData.value.vendorId) {
      attachmentFormData.append('vendorId', invitationData.value.vendorId)
    }
    if (invitationData.value.invitationId) {
      attachmentFormData.append('invitationId', invitationData.value.invitationId)
    }
 
    const storedResponseId = localStorage.getItem('rfp_response_id')
    if (storedResponseId) {
      attachmentFormData.append('responseId', storedResponseId)
    }
 
    if (formData.value.contactName) {
      attachmentFormData.append('uploadedBy', formData.value.contactName)
    }
 
    const authHeaders = getAuthHeaders()
    const { 'Content-Type': _ignored, ...headersWithoutContentType } = authHeaders
 
    const response = await fetch(`${API_BASE_URL}/rfp-responses/upload-response-asset/`, {
      method: 'POST',
      headers: headersWithoutContentType,
      body: attachmentFormData
    })
 
    const data = await response.json()
 
    if (!response.ok || !data.success) {
      throw new Error(data?.error || 'Failed to upload attachment')
    }
 
    if (data.attachment?.responseId) {
      localStorage.setItem('rfp_response_id', data.attachment.responseId)
    }
 
    if (data.attachment) {
      data.attachment.criteriaId = String(criteriaId)
    }
 
    if (data.attachment?.id) {
      console.log('✅ VendorPortal: Uploaded rich response attachment successfully:', data.attachment)
    } else {
      console.warn('⚠️ VendorPortal: Upload response missing attachment data:', data)
    }
 
    console.log('VendorPortal: Returning attachment to RichResponseEditor', data.attachment)
    return data.attachment
  } catch (error) {
    console.error('❌ VendorPortal: Error uploading response attachment:', error)
    showErrorToast(error.message || 'Failed to upload attachment')
    throw error
  }
}
 

// New handleFileSelect for dynamic document upload
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    newDocument.value.file = file
    newDocument.value.fileName = file.name
    newDocument.value.fileSize = file.size
  }
}

// Add document to list
const addDocument = () => {
  if (!newDocument.value.name || !newDocument.value.file) {
    showErrorToast('Please provide both document name and select a file.')
    return
  }

  // Check file size (max 50MB)
  if (newDocument.value.fileSize > 50 * 1024 * 1024) {
    showErrorToast('File size must be less than 50MB.')
    return
  }

  // Add to uploaded documents list
  uploadedDocuments.value.push({
    name: newDocument.value.name,
    file: newDocument.value.file,
    fileName: newDocument.value.fileName,
    fileSize: newDocument.value.fileSize,
    documentType: newDocument.value.documentType || 'rfps',
    uploaded: false,
    s3Id: null,
    url: null,
    isMerged: false
  })

  // Clear form
  clearDocumentForm()
  
  showSuccessToast('Document added to upload queue.')
}

// Clear document form
const clearDocumentForm = () => {
  newDocument.value = {
    name: '',
    file: null,
    fileName: '',
    fileSize: 0,
    documentType: 'rfps'
  }
  // Clear file input
  const fileInput = document.querySelector('input[type="file"]')
  if (fileInput) {
    fileInput.value = ''
  }
}

// Drag and drop handlers for reordering documents
const draggedIndex = ref(null)
const dragOverIndex = ref(null)

const handleDragStart = (index, event) => {
  if (isMergingDocuments.value) {
    event.preventDefault()
    return
  }
  draggedIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/html', index)
  // Add visual feedback
  event.target.style.opacity = '0.5'
}

const handleDragOver = (index, event) => {
  if (draggedIndex.value === null || draggedIndex.value === index) return
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  dragOverIndex.value = index
}

const handleDrop = (index, event) => {
  event.preventDefault()
  
  if (draggedIndex.value === null || draggedIndex.value === index) {
    draggedIndex.value = null
    dragOverIndex.value = null
    return
  }
  
  // Reorder documents
  const draggedDoc = uploadedDocuments.value[draggedIndex.value]
  const oldIndex = draggedIndex.value
  const newIndex = draggedIndex.value < index ? index - 1 : index
  
  // Remove dragged item from its current position
  uploadedDocuments.value.splice(oldIndex, 1)
  
  // Insert at new position
  uploadedDocuments.value.splice(newIndex, 0, draggedDoc)
  
  // Adjust selectedDocuments indices
  const adjustedSelection = new Set()
  selectedDocuments.value.forEach(selectedIndex => {
    if (oldIndex < newIndex) {
      // Dragging down
      if (selectedIndex === oldIndex) {
        adjustedSelection.add(newIndex)
      } else if (selectedIndex > oldIndex && selectedIndex <= newIndex) {
        adjustedSelection.add(selectedIndex - 1)
      } else if (selectedIndex < oldIndex || selectedIndex > newIndex) {
        adjustedSelection.add(selectedIndex)
      }
    } else {
      // Dragging up
      if (selectedIndex === oldIndex) {
        adjustedSelection.add(newIndex)
      } else if (selectedIndex >= newIndex && selectedIndex < oldIndex) {
        adjustedSelection.add(selectedIndex + 1)
      } else if (selectedIndex < newIndex || selectedIndex > oldIndex) {
        adjustedSelection.add(selectedIndex)
      }
    }
  })
  selectedDocuments.value = adjustedSelection
  
  // Reset drag state
  draggedIndex.value = null
  dragOverIndex.value = null
  
  showSuccessToast('Document order updated.')
}

const handleDragEnd = (event) => {
  // Reset visual feedback
  event.target.style.opacity = '1'
  draggedIndex.value = null
  dragOverIndex.value = null
}

// Helper functions to get actual indices in uploadedDocuments array
const getRegularDocumentIndex = (filteredIndex) => {
  let count = 0
  for (let i = 0; i < uploadedDocuments.value.length; i++) {
    if (!uploadedDocuments.value[i].isMerged) {
      if (count === filteredIndex) {
        return i
      }
      count++
    }
  }
  return -1
}

const getMergedDocumentIndex = (filteredIndex) => {
  let count = 0
  for (let i = 0; i < uploadedDocuments.value.length; i++) {
    if (uploadedDocuments.value[i].isMerged) {
      if (count === filteredIndex) {
        return i
      }
      count++
    }
  }
  return -1
}

// Document selection functions (only for regular documents)
const toggleDocumentSelection = (index) => {
  // Only allow selection of regular (non-merged) documents
  const doc = uploadedDocuments.value[index]
  if (doc && doc.isMerged) {
    return
  }
  
  if (selectedDocuments.value.has(index)) {
    selectedDocuments.value.delete(index)
  } else {
    selectedDocuments.value.add(index)
  }
  // Create a new Set to trigger reactivity
  selectedDocuments.value = new Set(selectedDocuments.value)
}

const selectAllDocuments = () => {
  // Only select regular (non-merged) documents
  const allIndices = uploadedDocuments.value
    .map((doc, index) => doc.isMerged ? -1 : index)
    .filter(index => index !== -1)
  selectedDocuments.value = new Set(allIndices)
}

const deselectAllDocuments = () => {
  selectedDocuments.value = new Set()
}

// Merge selected documents (only regular documents can be merged)
const mergeSelectedDocuments = async () => {
  if (selectedDocuments.value.size < 2) {
    showErrorToast('Please select at least 2 documents to merge.')
    return
  }

  const selectedIndices = Array.from(selectedDocuments.value).sort((a, b) => a - b)
  const selectedDocs = selectedIndices
    .map(index => uploadedDocuments.value[index])
    .filter(doc => doc && !doc.isMerged) // Exclude merged documents from selection

  // Ensure we still have at least 2 documents after filtering
  if (selectedDocs.length < 2) {
    showErrorToast('Please select at least 2 regular documents to merge. Merged documents cannot be merged again.')
    return
  }

  // Check if all selected documents are uploaded
  const allUploaded = selectedDocs.every(doc => doc.uploaded && doc.s3Id)
  const allPending = selectedDocs.every(doc => !doc.uploaded && doc.file)

  if (allUploaded) {
    // Merge by document IDs
    const documentIds = selectedDocs
      .map(doc => Number(doc.s3Id))
      .filter(id => id !== null && id !== undefined && !isNaN(id) && id > 0)
    
    if (documentIds.length >= 2) {
      await mergeDocuments(documentIds)
      // Clear selection after merge
      selectedDocuments.value = new Set()
    } else {
      showErrorToast('Invalid document IDs. Please ensure all selected documents are saved.')
    }
  } else if (allPending) {
    // Merge from files
    await mergeDocumentsFromFiles(selectedDocs)
    // Clear selection after merge
    selectedDocuments.value = new Set()
  } else {
    showErrorToast('Please ensure all selected documents are either all saved or all pending. Mixed states are not supported for merging.')
  }
}

// Remove document
const removeDocument = async (index) => {
  const doc = uploadedDocuments.value[index]
  
  // Remove from selection if selected
  if (selectedDocuments.value.has(index)) {
    selectedDocuments.value.delete(index)
    // Adjust other selected indices
    const adjustedSelection = new Set()
    selectedDocuments.value.forEach(selectedIndex => {
      if (selectedIndex < index) {
        adjustedSelection.add(selectedIndex)
      } else if (selectedIndex > index) {
        adjustedSelection.add(selectedIndex - 1)
      }
    })
    selectedDocuments.value = adjustedSelection
  } else {
    // Adjust other selected indices
    const adjustedSelection = new Set()
    selectedDocuments.value.forEach(selectedIndex => {
      if (selectedIndex < index) {
        adjustedSelection.add(selectedIndex)
      } else if (selectedIndex > index) {
        adjustedSelection.add(selectedIndex - 1)
      }
    })
    selectedDocuments.value = adjustedSelection
  }
  
  if (doc.uploaded) {
    // For already uploaded documents, confirm deletion
    PopupService.confirm(
      `Are you sure you want to delete "${doc.name}"? This will remove it from your response.`,
      'Confirm Deletion',
      async () => {
        try {
          // Delete from backend if it has an s3Id
          if (doc.s3Id && invitationData.value.rfpId) {
            try {
              const response = await fetch(`${API_BASE_URL}/rfp-responses/${invitationData.value.rfpId}/documents/delete/`, {
                method: 'DELETE',
                headers: {
                  'Content-Type': 'application/json',
                  ...getAuthHeaders()
                },
                body: JSON.stringify({
                  documentId: doc.s3Id,
                  vendorId: invitationData.value.vendorId,
                  invitationId: invitationData.value.invitationId
                })
              })
              const data = await response.json()
              if (data.success) {
                console.log(`✅ Removed document ${doc.s3Id} from backend`)
              }
            } catch (error) {
              console.error('Error deleting document from backend:', error)
            }
          }
          
          // Remove from UI
          uploadedDocuments.value.splice(index, 1)
          showSuccessToast('Document has been removed.')
          updateCompletionStatus()
        } catch (error) {
          console.error('Error deleting document:', error)
          showErrorToast('Failed to delete document. Please try again.')
        }
      }
    )
  } else {
    // For pending documents, just remove from queue
    uploadedDocuments.value.splice(index, 1)
    showSuccessToast('Document removed from upload queue.')
  }
}

// Save a single document immediately to S3
const saveSingleDocument = async (index) => {
  if (!invitationData.value.rfpId) {
    showErrorToast('Missing RFP ID. Please refresh the page.')
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
    uploadFormData.append('rfpId', invitationData.value.rfpId)
    // Use document type from doc, or fallback to custom_${index} for backward compatibility
    uploadFormData.append('documentType', doc.documentType ? `${doc.documentType}_${index}` : `custom_${index}`)
    
    if (invitationData.value.vendorId) {
      uploadFormData.append('vendorId', invitationData.value.vendorId)
    }
    if (invitationData.value.invitationId) {
      uploadFormData.append('invitationId', invitationData.value.invitationId)
    }
    if (invitationData.value.isOpenRfp) {
      uploadFormData.append('submissionSource', 'open')
    }

    const authHeaders = getAuthHeaders()
    const { 'Content-Type': _, ...headersWithoutContentType } = authHeaders

    const response = await fetch(`${API_BASE_URL}/rfp-responses/upload-document/`, {
      method: 'POST',
      headers: headersWithoutContentType,
      body: uploadFormData
    })

    const data = await response.json()
    console.log(`📊 Upload response for ${doc.name}:`, data)

    if (data.success) {
      // Mark document as uploaded
      uploadedDocuments.value[index].uploaded = true
      uploadedDocuments.value[index].s3Id = data.document_id || data.s3_file_id
      uploadedDocuments.value[index].url = data.document_url || data.s3_url
      
      console.log(`✅ Document uploaded successfully: ${doc.name} (ID: ${uploadedDocuments.value[index].s3Id})`)
      showSuccessToast(`Document "${doc.name}" uploaded successfully`)
      updateCompletionStatus()
    } else {
      showErrorToast(data.error || 'Failed to upload document')
    }
  } catch (error) {
    console.error(`❌ Error uploading document ${doc.name}:`, error)
    showErrorToast('Failed to upload document. Please try again.')
  } finally {
    perDocUploading.value[index] = false
  }
}

// Download vendor document
const downloadVendorDocument = async (doc) => {
  try {
    if (doc.url) {
      window.open(doc.url, '_blank')
      showSuccessToast('Download started')
    } else if (doc.s3Id) {
      // Fetch document details to get URL
      const response = await fetch(`${API_BASE_URL}/s3-files/${doc.s3Id}/`, {
        headers: getAuthHeaders()
      })
      const data = await response.json()
      const fileData = data.s3_file || data
      if (fileData.url) {
        window.open(fileData.url, '_blank')
        showSuccessToast('Download started')
      } else {
        showErrorToast('Document URL not available')
      }
    } else {
      showErrorToast('Document URL not available')
    }
  } catch (error) {
    console.error('Error downloading document:', error)
    showErrorToast('Failed to download document')
  }
}

// Download document from S3 (old function - kept for compatibility)
const downloadDocument = async (documentType) => {
  try {
    if (!invitationData.value.rfpId) {
      showErrorToast('Missing RFP ID for download')
      return
    }

    console.log('📥 Downloading document:', documentType)
    
    // Build query parameters
    const params = new URLSearchParams()
    params.append('documentType', documentType)
    if (invitationData.value.vendorId) {
      params.append('vendorId', invitationData.value.vendorId)
    }
    if (invitationData.value.invitationId) {
      params.append('invitationId', invitationData.value.invitationId)
    }
    
    const response = await fetch(`${API_BASE_URL}/rfp-responses/${invitationData.value.rfpId}/documents/download/?${params}`, {
      headers: getAuthHeaders()
    })
    const data = await response.json()
    
    console.log('📥 Download response:', data)
    
    if (data.success) {
      // Handle different response formats
      const downloadUrl = data.download_url || data.url || data.s3_url
      if (downloadUrl) {
        // Open download URL in new tab
        window.open(downloadUrl, '_blank')
        showSuccessToast('Document download started')
      } else {
        showErrorToast('Download URL not found in response')
      }
    } else {
      showErrorToast(data.error || 'Failed to download document')
    }
  } catch (error) {
    console.error('Error downloading document:', error)
    showErrorToast('Network error. Please try again.')
  }
}

// Delete document from S3
const deleteDocument = async (documentType) => {
  PopupService.confirm(
    'Are you sure you want to delete this document?',
    'Confirm Deletion',
    async () => {
      await performDelete(documentType)
    }
  )
}

const performDelete = async (documentType) => {
  
  try {
    if (!invitationData.value.rfpId) {
      showErrorToast('Missing RFP ID for deletion')
      return
    }

    console.log('🗑️ Deleting document:', documentType)
    
    // Prepare request body
    const requestBody = {
      documentType: documentType
    }
    
    if (invitationData.value.vendorId) {
      requestBody.vendorId = invitationData.value.vendorId
    }
    if (invitationData.value.invitationId) {
      requestBody.invitationId = invitationData.value.invitationId
    }
    
    const response = await fetch(`${API_BASE_URL}/rfp-responses/${invitationData.value.rfpId}/documents/delete/`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(requestBody)
    })
    
    const data = await response.json()
    console.log('🗑️ Delete response:', data)
    
    if (data.success) {
      // Remove from local state (array structure)
      const docIndex = uploadedDocuments.value.findIndex(doc => doc.s3Id === documentType || doc.name === documentType)
      if (docIndex !== -1) {
        uploadedDocuments.value.splice(docIndex, 1)
      }
      showSuccessToast('Document deleted successfully')
      updateCompletionStatus()
    } else {
      showErrorToast(data.error || 'Failed to delete document')
    }
  } catch (error) {
    console.error('Error deleting document:', error)
    showErrorToast('Network error. Please try again.')
  }
}

// Merge documents function
const mergeDocuments = async (documentIds = null) => {
  if (!documentIds) {
    const savedDocs = uploadedDocuments.value.filter(doc => doc.uploaded && doc.s3Id)
    if (savedDocs.length < 2) {
      const pendingDocs = uploadedDocuments.value.filter(doc => !doc.uploaded && doc.file)
      if (pendingDocs.length >= 2) {
        return await mergeDocumentsFromFiles(pendingDocs)
      } else {
        showErrorToast('At least 2 documents are required for merging.')
        return null
      }
    }
    documentIds = savedDocs.map(doc => doc.s3Id).filter(id => id !== null && id !== undefined)
  }

  const rfpId = invitationData.value.rfpId

  if (!documentIds || !Array.isArray(documentIds) || documentIds.length < 2) {
    console.error('❌ Invalid document IDs for merging:', documentIds)
    showErrorToast('At least 2 documents are required for merging.')
    return null
  }

  const numericIds = documentIds.map(id => Number(id)).filter(id => !isNaN(id) && id > 0)
  if (numericIds.length < 2) {
    console.error('❌ Invalid numeric document IDs:', numericIds)
    showErrorToast('Invalid document IDs. Please ensure all documents are saved.')
    return null
  }

  try {
    isMergingDocuments.value = true
    console.log(`🔄 Merging ${numericIds.length} documents in order for vendor response:`, numericIds)
    
    // Log document details being merged
    const docsToMerge = uploadedDocuments.value.filter(doc => doc.uploaded && doc.s3Id && numericIds.includes(Number(doc.s3Id)))
    const fileTypeInfo = docsToMerge.map(doc => {
      const ext = doc.fileName?.split('.').pop()?.toLowerCase() || doc.fileType || 'unknown'
      return `${doc.name} (${ext})`
    })
    console.log(`📋 Documents to merge:`, fileTypeInfo)

    const currentUserId = getCurrentUserId() || '1'
    const mergeResponse = await axios.post(`${API_BASE_URL}/merge-documents/`, {
      document_ids: numericIds,
      document_order: numericIds,
      rfp_id: rfpId || null,
      user_id: currentUserId
    }, {
      headers: getAuthHeaders(),
      timeout: 120000
    })

    console.log('📊 Merge response:', mergeResponse.data)

    if (mergeResponse.data && mergeResponse.data.success) {
      console.log('✅ Documents merged successfully:', mergeResponse.data)
      
      try {
        const docResponse = await axios.get(`${API_BASE_URL}/s3-files/${mergeResponse.data.merged_document_id}/`, {
          headers: getAuthHeaders()
        })
        
        const fileData = docResponse.data.s3_file || docResponse.data
        console.log('✅ Fetched merged document details:', fileData)
        
        const mergedDoc = {
          name: fileData.document_name || fileData.file_name || 'Merged Document',
          fileName: fileData.file_name || 'merged_document.pdf',
          fileSize: fileData.file_size || 0,
          fileType: fileData.file_type || 'pdf',
          url: fileData.url || mergeResponse.data.merged_document_url,
          uploaded: true,
          s3Id: mergeResponse.data.merged_document_id,
          file: null,
          isMerged: true,
          documentType: 'rfps' // Merged documents default to rfps type
        }
        
        uploadedDocuments.value.push(mergedDoc)
        console.log('✅ Merged document added to document list:', mergedDoc)
        
      } catch (fetchError) {
        console.error('❌ Error fetching merged document details:', fetchError)
        const mergedDoc = {
          name: mergeResponse.data.merged_document_name || 'Merged Document',
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
      }
      
      const fileCount = mergeResponse.data.document_count || numericIds.length
      showSuccessToast(`Successfully merged ${fileCount} document(s) (supports PDF, Word, Images, and all combinations).`)
      updateCompletionStatus()
      return mergeResponse.data.merged_document_id
    } else {
      const errorMsg = mergeResponse.data?.error || 'Failed to merge documents.'
      console.error('❌ Merge failed:', errorMsg)
      showErrorToast(errorMsg)
      return null
    }
  } catch (mergeError) {
    console.error('❌ Error merging documents:', mergeError)
    if (mergeError.response) {
      const errorData = mergeError.response.data || {}
      const errorMsg = errorData.error || errorData.message || 'Failed to merge documents.'
      const processedCount = errorData.processed_count
      const requestedCount = errorData.requested_count
      
      // Provide more detailed error message
      let detailedError = errorMsg
      if (processedCount !== undefined && requestedCount !== undefined) {
        detailedError = `${errorMsg} (Processed: ${processedCount}/${requestedCount})`
      }
      
      console.error('❌ Merge error details:', {
        error: errorMsg,
        processedCount,
        requestedCount,
        status: mergeError.response.status
      })
      
      showErrorToast(detailedError)
    } else {
      showErrorToast('Network error. Please check your connection and try again.')
    }
    return null
  } finally {
    isMergingDocuments.value = false
  }
}

// Merge documents directly from files
const mergeDocumentsFromFiles = async (docs) => {
  if (!docs || docs.length < 2) {
    showErrorToast('At least 2 documents are required for merging.')
    return null
  }

  const rfpId = invitationData.value.rfpId

  try {
    isMergingDocuments.value = true
    console.log(`🔄 Merging ${docs.length} files directly (before upload)`)
    
    // Log file types being merged
    const fileTypes = docs.map(doc => {
      if (doc.file) {
        const ext = doc.file.name.split('.').pop()?.toLowerCase() || 'unknown'
        return `${doc.name} (${ext})`
      }
      return doc.name
    })
    console.log(`📋 Files to merge:`, fileTypes)

    const formData = new FormData()
    docs.forEach(doc => {
      if (doc.file) {
        formData.append('files', doc.file)
      }
    })
    
    if (rfpId) {
      formData.append('rfp_id', rfpId)
    }
    const currentUserId = getCurrentUserId() || '1'
    formData.append('user_id', currentUserId)

    const mergeResponse = await axios.post(`${API_BASE_URL}/merge-documents/`, formData, {
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000
    })

    console.log('📊 Merge response:', mergeResponse.data)

    if (mergeResponse.data && mergeResponse.data.success) {
      console.log('✅ Documents merged successfully from files:', mergeResponse.data)
      
      try {
        const docResponse = await axios.get(`${API_BASE_URL}/s3-files/${mergeResponse.data.merged_document_id}/`, {
          headers: getAuthHeaders()
        })
        
        const fileData = docResponse.data.s3_file || docResponse.data
        console.log('✅ Fetched merged document details:', fileData)
        
        const mergedDoc = {
          name: fileData.document_name || fileData.file_name || 'Merged Document',
          fileName: fileData.file_name || 'merged_document.pdf',
          fileSize: fileData.file_size || 0,
          fileType: fileData.file_type || 'pdf',
          url: fileData.url || mergeResponse.data.merged_document_url,
          uploaded: true,
          s3Id: mergeResponse.data.merged_document_id,
          file: null,
          isMerged: true,
          documentType: 'rfps' // Merged documents default to rfps type
        }
        
        uploadedDocuments.value.push(mergedDoc)
        console.log('✅ Merged document added to document list:', mergedDoc)
        
      } catch (fetchError) {
        console.error('❌ Error fetching merged document details:', fetchError)
        const mergedDoc = {
          name: mergeResponse.data.merged_document_name || 'Merged Document',
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
      }
      
      const fileCount = mergeResponse.data.document_count || docs.length
      showSuccessToast(`Successfully merged ${fileCount} document(s) (supports PDF, Word, Images, and all combinations).`)
      updateCompletionStatus()
      return mergeResponse.data.merged_document_id
    } else {
      const errorMsg = mergeResponse.data?.error || 'Failed to merge documents.'
      console.error('❌ Merge failed:', errorMsg)
      showErrorToast(errorMsg)
      return null
    }
  } catch (mergeError) {
    console.error('❌ Error merging documents from files:', mergeError)
    if (mergeError.response) {
      const errorData = mergeError.response.data || {}
      const errorMsg = errorData.error || errorData.message || 'Failed to merge documents.'
      const processedCount = errorData.processed_count
      const requestedCount = errorData.requested_count
      
      // Provide more detailed error message
      let detailedError = errorMsg
      if (processedCount !== undefined && requestedCount !== undefined) {
        detailedError = `${errorMsg} (Processed: ${processedCount}/${requestedCount})`
      }
      
      console.error('❌ Merge error details:', {
        error: errorMsg,
        processedCount,
        requestedCount,
        status: mergeError.response.status
      })
      
      showErrorToast(detailedError)
    } else {
      showErrorToast(`Failed to merge documents: ${mergeError.message}`)
    }
    return null
  } finally {
    isMergingDocuments.value = false
  }
}

// Save all pending documents and merge
const saveAllDocuments = async () => {
  console.log('🚀 saveAllDocuments called')
  const rfpId = invitationData.value.rfpId
  const hasRfpId = rfpId && rfpId !== 'null' && rfpId !== ''
  
  // Check if we have at least 2 documents
  if (uploadedDocuments.value.length < 2) {
    showErrorToast('At least 2 documents are required for merging.')
    return
  }
  
  if (!hasRfpId) {
    console.log('ℹ️ No RFP ID found - will merge documents without RFP association')
    const allDocs = uploadedDocuments.value
    const docsWithFiles = allDocs.filter(doc => doc.file)
    if (docsWithFiles.length >= 2) {
      console.log('🔄 Merging documents directly from files (no RFP ID needed)')
      await mergeDocumentsFromFiles(docsWithFiles)
      return
    } else {
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
      showErrorToast('Please add at least 2 documents with files to merge.')
      return
    }
  }

  try {
    isUploadingDocuments.value = true
    console.log('📋 Current uploadedDocuments:', uploadedDocuments.value.map((d, idx) => ({
      index: idx,
      name: d.name,
      uploaded: d.uploaded,
      s3Id: d.s3Id,
      hasFile: !!d.file
    })))
    
    // Step 1: Upload any pending documents
    const pendingDocs = uploadedDocuments.value.filter(doc => !doc.uploaded && doc.file)
    console.log(`📤 Found ${pendingDocs.length} pending documents to upload`)
    
    for (let i = 0; i < pendingDocs.length; i++) {
      const doc = pendingDocs[i]
      const docIndex = uploadedDocuments.value.findIndex(d => d === doc)
      if (docIndex !== -1) {
        await saveSingleDocument(docIndex)
        // Small delay to ensure upload completes
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }
    
    // Step 2: Always merge all documents in current order (if we have 2+ saved documents)
    // Wait a bit to ensure all uploads are complete
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // Refresh the document list to get latest s3Ids
    const allSavedDocs = uploadedDocuments.value.filter(doc => doc.uploaded && doc.s3Id && !doc.isMerged)
    console.log(`📊 Found ${allSavedDocs.length} saved documents (excluding merged) to merge`)
    
    if (allSavedDocs.length >= 2) {
      console.log('🔄 Merging all saved documents in current order')
      const orderedDocumentIds = uploadedDocuments.value
        .filter(doc => doc.uploaded && doc.s3Id && !doc.isMerged) // Exclude already merged documents
        .map(doc => Number(doc.s3Id))
        .filter(id => id !== null && id !== undefined && !isNaN(id) && id > 0)
      
      console.log('📋 Document IDs to merge (in order):', orderedDocumentIds)
      console.log('📋 Full document list for debugging:', uploadedDocuments.value.map(d => ({
        name: d.name,
        uploaded: d.uploaded,
        s3Id: d.s3Id,
        isMerged: d.isMerged
      })))
      
      if (orderedDocumentIds.length >= 2) {
        // Validate documents exist before merging
        console.log('🔍 Validating documents exist before merging...')
        const validationPromises = orderedDocumentIds.map(async (docId) => {
          try {
            const docResponse = await axios.get(`${API_BASE_URL}/s3-files/${docId}/`, {
              headers: getAuthHeaders()
            })
            return { id: docId, exists: docResponse.data.success || !!docResponse.data.s3_file }
          } catch (error) {
            console.warn(`⚠️ Document ${docId} validation failed:`, error.response?.status || error.message)
            return { id: docId, exists: false }
          }
        })
        
        const validationResults = await Promise.all(validationPromises)
        const validDocumentIds = validationResults
          .filter(result => result.exists)
          .map(result => result.id)
        
        console.log(`✅ Validation complete: ${validDocumentIds.length}/${orderedDocumentIds.length} documents are valid`)
        
        if (validDocumentIds.length < 2) {
          const invalidIds = orderedDocumentIds.filter(id => !validDocumentIds.includes(id))
          console.error('❌ Not enough valid documents:', {
            valid: validDocumentIds.length,
            invalid: invalidIds,
            total: orderedDocumentIds.length
          })
          showErrorToast(`Cannot merge: Only ${validDocumentIds.length} valid document(s) found. ${invalidIds.length > 0 ? `Invalid document IDs: ${invalidIds.join(', ')}` : 'Please ensure all documents are properly saved.'}`)
          return
        }
        
        // Use only valid document IDs for merging
        if (validDocumentIds.length !== orderedDocumentIds.length) {
          console.warn(`⚠️ Some documents are invalid. Merging only valid documents: ${validDocumentIds.join(', ')}`)
          showWarningToast(`Some documents could not be found. Merging ${validDocumentIds.length} valid document(s).`)
        }
        
        const mergeResult = await mergeDocuments(validDocumentIds)
        if (mergeResult) {
          console.log('✅ Merge completed successfully')
        } else {
          console.error('❌ Merge failed or returned null')
        }
      } else {
        console.warn('⚠️ Not enough valid document IDs for merging:', orderedDocumentIds)
        showErrorToast('Not enough valid documents to merge. Please ensure all documents are saved.')
      }
    } else {
      console.log(`ℹ️ Only ${allSavedDocs.length} saved documents found. Need at least 2 for merging.`)
      if (allSavedDocs.length === 0 && pendingDocs.length === 0) {
        // Check if there are already merged documents
        const mergedDocs = uploadedDocuments.value.filter(doc => doc.isMerged)
        if (mergedDocs.length > 0) {
          showSuccessToast('Documents are already merged.')
        } else {
          showSuccessToast('All documents are saved. Please add at least 2 documents to merge.')
        }
      } else {
        showErrorToast('Please save at least 2 documents before merging.')
      }
    }
  } catch (error) {
    console.error('❌ Error in saveAllDocuments:', error)
    showErrorToast('Error saving documents. Please try again.')
  } finally {
    isUploadingDocuments.value = false
  }
}

// Load existing documents - updated for array structure
const loadExistingDocuments = async () => {
  try {
    if (!invitationData.value.rfpId) {
      console.log('⚠️ Missing RFP ID for document loading')
      return
    }

    console.log('📂 Loading existing documents for RFP:', invitationData.value.rfpId)
    
    // Build query parameters
    const params = new URLSearchParams()
    if (invitationData.value.vendorId) {
      params.append('vendorId', invitationData.value.vendorId)
    }
    if (invitationData.value.invitationId) {
      params.append('invitationId', invitationData.value.invitationId)
    }
    
    const response = await fetch(`${API_BASE_URL}/rfp-responses/${invitationData.value.rfpId}/documents/?${params}`, {
      headers: getAuthHeaders()
    })
    const data = await response.json()
    
    console.log('📥 Documents response:', data)
    
    if (data.success && data.documents) {
      // Transform backend document structure to both legacy array + map formats
      const transformedDocuments = []
      const documentUrlMap = {}

      Object.keys(data.documents).forEach(docType => {
        const doc = data.documents[docType]

        // Only include documents that have a valid URL reference
        if (!doc || (!doc.url && !(typeof doc === 'string' && doc))) {
          console.warn(`⚠️ Skipping document ${docType} - missing URL:`, doc)
          return
        }

        let normalizedDoc

        if (typeof doc === 'string') {
          // If doc is just a URL string
          normalizedDoc = {
            filename: docType.replace(/_/g, ' '),
            size: 0,
            upload_date: new Date().toISOString(),
            url: doc,
            key: null,
            content_type: 'application/octet-stream',
            document_id: null,
            metadata: {}
          }
        } else if (typeof doc === 'object') {
          // If doc is an object with metadata
          normalizedDoc = {
            filename: doc.filename || doc.name || docType.replace(/_/g, ' '),
            size: doc.size || doc.file_size || 0,
            upload_date: doc.upload_date || doc.uploadDate || new Date().toISOString(),
            url: doc.url || null,
            key: doc.key || doc.s3_key || null,
            content_type: doc.content_type || doc.contentType || 'application/octet-stream',
            document_id: doc.document_id || doc.s3_file_id || doc.id || null,
            metadata: doc.metadata || {}
          }
        } else {
          console.warn(`⚠️ Skipping document ${docType} - unsupported format:`, doc)
          return
        }

        documentUrlMap[docType] = normalizedDoc

        const docId = normalizedDoc.document_id
        const fileName = normalizedDoc.filename
        const docName = normalizedDoc.filename || docType.replace(/_/g, ' ')

        // Skip documents without valid identifiers
        if (!docId && !fileName) {
          console.log('⚠️ Skipping invalid document entry:', doc)
          return
        }

        // Extract document type from document_type field or infer from docType
        let documentType = normalizedDoc.document_type || 'rfps'
        // If docType starts with a document type prefix, extract it
        if (docType && typeof docType === 'string') {
          const typeMatch = docType.match(/^(rfps|contract|sl|bcp_drp)_/)
          if (typeMatch) {
            documentType = typeMatch[1]
          } else if (docType.startsWith('custom_')) {
            // For custom documents, try to infer from metadata or default to rfps
            documentType = normalizedDoc.metadata?.document_type || 'rfps'
          } else if (!isNaN(Number(docType))) {
            // If docType is a number (document ID), try to get type from metadata
            documentType = normalizedDoc.metadata?.document_type || normalizedDoc.document_type || 'rfps'
          }
        }
        
        transformedDocuments.push({
          name: docName || `Document ${docId || 'Unknown'}`,
          fileName: fileName || docName || `document_${docId || 'unknown'}.pdf`,
          fileSize: normalizedDoc.size,
          fileType: normalizedDoc.content_type || 'pdf',
          url: normalizedDoc.url,
          key: normalizedDoc.key,
          uploaded: true,
          s3Id: docId,
          file: null,
          isMerged: Boolean(normalizedDoc.metadata?.is_merged),
          documentType: documentType
        })
      })
      
      // Only update if we have valid documents
      if (transformedDocuments.length > 0) {
        uploadedDocuments.value = transformedDocuments
        documentUrls.value = documentUrlMap
        console.log('📋 Loaded documents:', transformedDocuments)
        console.log('📋 Document URLs count:', Object.keys(documentUrlMap).length)
        updateCompletionStatus()
      } else {
        console.log('ℹ️ No valid documents found in response')
        uploadedDocuments.value = [] // Ensure array is empty if no valid documents
        documentUrls.value = {}
      }
    } else {
      console.log('ℹ️ No existing documents found or error:', data.error)
      uploadedDocuments.value = [] // Ensure array is empty
      documentUrls.value = {}
    }
  } catch (error) {
    console.error('Error loading documents:', error)
    // Don't show error toast for empty responses - it's normal if no documents exist
    if (error.message && !error.message.includes('404')) {
      console.log('ℹ️ Error loading documents (non-critical):', error.message)
    }
    // Ensure array is empty on error
    uploadedDocuments.value = []
  }
}

// Format file size
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatCustomFieldValue = (field) => {
  const value = getCustomFieldValue(field)
  if (value === null || value === undefined) return 'Not set'
  if (typeof value === 'object') {
    if (value.fileName) return `File: ${value.fileName}`
    return JSON.stringify(value)
  }
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return String(value)
}

const getCustomFieldValue = (field, category = null) => {
  const fieldCategory = category || field.category || 'responses'
  const originalName = field._originalName || field.name
  
  // Try category-specific data first
  if (categoryCustomFieldData.value[fieldCategory] && categoryCustomFieldData.value[fieldCategory][originalName] !== undefined) {
    return categoryCustomFieldData.value[fieldCategory][originalName]
  }
  
  // Fallback to legacy dynamicResponseData
  const uniqueKey = field._uniqueKey || field.name
  return dynamicResponseData.value[uniqueKey]
}

const downloadCustomFieldFile = (field, category = null) => {
  const fieldCategory = category || field.category || 'responses'
  const fileData = getCustomFieldValue(field, fieldCategory)
  
  if (!fileData) {
    showErrorToast('No file available to download.')
    return
  }

  if (typeof fileData === 'string') {
    if (/^https?:\/\//i.test(fileData)) {
      window.open(fileData, '_blank')
    } else {
      showErrorToast('Unable to download this file reference.')
    }
    return
  }

  if (fileData.dataUrl) {
    const link = document.createElement('a')
    link.href = fileData.dataUrl
    link.download = fileData.fileName || `${field.name || 'file'}.file`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } else if (fileData.url) {
    window.open(fileData.url, '_blank')
  }
}

// Documents - dynamic based on RFP requirements
const documents = ref([])

// Key personnel - dynamic
const keyPersonnel = ref([
  {
    name: "",
    role: "",
    email: "",
    phone: "",
    experience: "",
    education: "",
    relevantExperience: "",
    certifications: [""]
  }
])

// Team member management methods
const addTeamMember = () => {
  // Ensure keyPersonnel is properly initialized
  if (!Array.isArray(keyPersonnel.value)) {
    keyPersonnel.value = []
  }
  
  keyPersonnel.value.push({
    name: "",
    role: "",
    email: "",
    phone: "",
    experience: "",
    education: "",
    relevantExperience: "",
    certifications: [""]
  })
}

const removeTeamMember = (index) => {
  if (!Array.isArray(keyPersonnel.value)) {
    keyPersonnel.value = []
    return
  }
  
  if (keyPersonnel.value.length > 1) {
    keyPersonnel.value.splice(index, 1)
  }
}

const addCertification = (personIndex) => {
  if (!Array.isArray(keyPersonnel.value) || !keyPersonnel.value[personIndex]) {
    return
  }
  
  if (!Array.isArray(keyPersonnel.value[personIndex].certifications)) {
    keyPersonnel.value[personIndex].certifications = []
  }
  
  keyPersonnel.value[personIndex].certifications.push("")
}

const removeCertification = (personIndex, certIndex) => {
  if (!Array.isArray(keyPersonnel.value) || !keyPersonnel.value[personIndex]) {
    return
  }
  
  if (!Array.isArray(keyPersonnel.value[personIndex].certifications)) {
    keyPersonnel.value[personIndex].certifications = []
    return
  }
  
  if (keyPersonnel.value[personIndex].certifications.length > 1) {
    keyPersonnel.value[personIndex].certifications.splice(certIndex, 1)
  }
}

// Reference management methods
const addReference = () => {
  // Ensure references array is properly initialized
  if (!Array.isArray(formData.value.references)) {
    formData.value.references = []
  }
  
  formData.value.references.push({
    companyName: "",
    contactPerson: "",
    email: "",
    phone: "",
    projectDescription: ""
  })
}

const removeReference = (index) => {
  if (!Array.isArray(formData.value.references)) {
    formData.value.references = []
    return
  }
  
  if (formData.value.references.length > 1) {
    formData.value.references.splice(index, 1)
  }
}

// Submission status
const submissionStatus = ref('DRAFT')
const lastSavedAt = ref(null)
const submittedAt = ref(null)

// Computed properties
const overallProgress = computed(() => {
  // Ensure completionStatus is properly initialized
  if (!completionStatus.value || typeof completionStatus.value !== 'object') {
    return 0
  }
  
  const progress = Math.round(
    (completionStatus.value.company + completionStatus.value.financial + completionStatus.value.responses + completionStatus.value.documents + completionStatus.value.personnel + completionStatus.value.compliance) / 6
  )
  console.log(`🎯 Overall progress: ${progress}% (Company: ${completionStatus.value.company}%, Financial: ${completionStatus.value.financial}%, Responses: ${completionStatus.value.responses}%, Documents: ${completionStatus.value.documents}%, Personnel: ${completionStatus.value.personnel}%, Compliance: ${completionStatus.value.compliance}%)`)
  return progress
})

// API base URL
const API_BASE_URL = 'http://localhost:8000/api/v1'

// Watch for form data changes and update completion status
watch(formData, () => {
  updateCompletionStatus()
}, { deep: true })

// Watch for responses changes
watch(responses, () => {
  updateCompletionStatus()
}, { deep: true })

// Watch for key personnel changes
watch(keyPersonnel, () => {
  updateCompletionStatus()
}, { deep: true })

// Watch for uploaded documents changes
watch(uploadedDocuments, () => {
  updateCompletionStatus()
}, { deep: true })

watch(() => props.previewPayload, async (newPayload) => {
  if (!newPayload) return
  isLoading.value = true
  try {
    await applyPreviewPayload(newPayload)
    updateCompletionStatus()
  } finally {
    isLoading.value = false
  }
}, { immediate: false })

// Watch for right panel tab changes to resolve documents when needed
watch(rightPanelTab, async (newTab) => {
  if (newTab === 'documents') {
    console.log('🔄 Right panel switched to documents tab')
    // If we have rfpDocuments but haven't resolved them yet, resolve now
    if (rfpDocuments.value && rfpDocTabs.value.length === 0) {
      console.log('🔄 Resolving RFP document tabs...')
      await resolveRfpDocumentTabs()
    }
    // Log current state for debugging
    console.log('📋 Current RFP documents state:', {
      hasRfpDocuments: !!rfpDocuments.value,
      rfpDocumentsValue: rfpDocuments.value,
      rfpDocTabsCount: rfpDocTabs.value.length,
      rfpDocTabs: rfpDocTabs.value
    })
  }
})

// Methods
const extractUTMParameters = () => {
  const params = new URLSearchParams(window.location.search)
  const utmParams = {}
  
  // Extract UTM parameters
  const utmKeys = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']
  utmKeys.forEach(key => {
    const value = params.get(key)
    if (value) {
      utmParams[key] = value
    }
  })
  
  // Extract additional tracking parameters
  const additionalKeys = ['gclid', 'fbclid', 'msclkid', 'ttclid']
  additionalKeys.forEach(key => {
    const value = params.get(key)
    if (value) {
      utmParams[key] = value
    }
  })
  
  return utmParams
}

const parseQueryParameters = () => {
  if (props.previewPayload) {
    previewMode.value = true
    invitationData.value = {
      rfpId: null,
      vendorId: null,
      invitationId: 'preview',
      org: '',
      vendorName: '',
      contactEmail: '',
      contactPhone: '',
      isOpenRfp: false
    }
    utmParameters.value = {}
    return
  }

  const params = new URLSearchParams(window.location.search)
  const pathParts = window.location.pathname.split('/').filter(part => part)

  const isPreviewQuery = params.get('preview') === 'true' || params.get('mode') === 'preview'
  const isPreviewPath = pathParts.includes('preview') || pathParts.includes('vendor-preview')
  if (isPreviewQuery || isPreviewPath) {
    previewMode.value = true
    invitationData.value = {
      rfpId: null,
      vendorId: null,
      invitationId: 'preview',
      org: '',
      vendorName: '',
      contactEmail: '',
      contactPhone: '',
      isOpenRfp: false
    }
    console.log('🕶️ Vendor Portal initialized in preview mode')
    return
  }
  
  // New parameter format
  let rfpId = params.get('rfpId') || ""
  let vendorId = params.get('vendorId') || ""
  let invitationId = params.get('invitationId') || params.get('invitation_id') || ""  // Support both formats
  let org = params.get('org') || ""
  let vendorName = params.get('vendorName') || ""
  let contactEmail = params.get('contactEmail') || ""
  let contactPhone = params.get('contactPhone') || ""
  
  // Check if it's an open RFP
  const isOpenRfp = pathParts.includes('open') || params.get('isOpenRfp') === 'true' || params.get('submissionSource') === 'open'
  
  // Extract UTM parameters
  const utmParams = extractUTMParameters()
  
  // Try to extract invitation ID from URL path if not in query params
  if (!invitationId && pathParts.length > 0) {
    // Look for patterns like /vendor-portal/invitation-123 or /vendor-portal/123
    const lastPart = pathParts[pathParts.length - 1]
    if (lastPart && (lastPart.startsWith('invitation-') || lastPart.startsWith('test-token-'))) {
      invitationId = lastPart
      console.log('📝 Extracted invitation ID from URL path:', invitationId)
    } else if (lastPart && /^\d+$/.test(lastPart)) {
      // If it's just a number, it might be an invitation ID
      invitationId = lastPart
      console.log('📝 Extracted numeric invitation ID from URL path:', invitationId)
    }
  }
  
  // For open RFP, generate a temporary invitation ID if we have rfpId but no invitationId
  if (isOpenRfp && rfpId && !invitationId) {
    invitationId = `open-rfp-${rfpId}-${Date.now()}`
    console.log('🌐 Generated temporary invitation ID for open RFP:', invitationId)
  }
  
  // Log parsed parameters
  console.log('📝 Parsed URL parameters:', {
    rfpId,
    vendorId,
    invitationId,
    org,
    vendorName,
    contactEmail,
    contactPhone,
    isOpenRfp,
    pathParts,
    fullPath: window.location.pathname
  })
  
  invitationData.value = {
    rfpId,
    vendorId,
    invitationId,  // This will be used in all API calls
    org,
    vendorName,
    contactEmail,
    contactPhone,
    isOpenRfp
  }
  
  // Store UTM parameters
  utmParameters.value = utmParams
  
  // Prefill form if parameters exist
  if (vendorName) formData.value.contactName = vendorName
  if (contactEmail) formData.value.email = contactEmail
  if (contactPhone) formData.value.phone = contactPhone
  if (org) formData.value.companyName = org
  
  // Log initialized data
  console.log('✅ Initialized invitation data:', invitationData.value)
  
  // Additional validation for debugging
  if (!invitationData.value.rfpId) {
    console.warn('⚠️ No RFP ID found in URL parameters')
  }
  if (!invitationData.value.vendorId && !invitationData.value.invitationId && !invitationData.value.isOpenRfp) {
    console.warn('⚠️ No vendor ID, invitation ID, or open RFP flag found')
  }
}

const fetchInvitationDetails = async () => {
  if (!invitationData.value.rfpId && !invitationData.value.isOpenRfp) {
    return
  }
  
  isLoading.value = true
  try {
    if (invitationData.value.isOpenRfp && invitationData.value.rfpId) {
      // Handle open RFP
      console.log('[fetchInvitationDetails] Fetching open RFP details...')
      console.log('[fetchInvitationDetails] API URL:', `${API_BASE_URL}/open-rfp/${invitationData.value.rfpId}/`)
      console.log('[fetchInvitationDetails] RFP ID:', invitationData.value.rfpId)
      
      const response = await fetch(`${API_BASE_URL}/open-rfp/${invitationData.value.rfpId}/`, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      })
      
      console.log('[fetchInvitationDetails] Response status:', response.status, response.statusText)
      const data = await parseJsonResponse(response, 'Unable to load open RFP details')
      console.log('[fetchInvitationDetails] Response data received:', {
        success: data.success,
        has_rfp: !!data.rfp,
        rfp_id: data.rfp?.rfp_id,
        rfp_type: data.rfp?.rfp_type,
        has_response_fields: !!data.rfp?.response_fields
      })
      
      if (response.ok && data.success) {
        rfpInfo.value = {
          rfpTitle: data.rfp.rfp_title,
          rfpNumber: data.rfp.rfp_number,
          deadline: data.rfp.submission_deadline ? new Date(data.rfp.submission_deadline).toLocaleDateString() : 'TBD',
          budget: data.rfp.estimated_value ? `$${parseInt(data.rfp.estimated_value).toLocaleString()}` : 'TBD',
          description: data.rfp.description || '',
          rfpType: data.rfp.rfp_type || '',
          category: data.rfp.category || '',
          criticality: data.rfp.criticality_level || ''
        }
        
        // Capture dynamic response fields if present
        console.log('[fetchInvitationDetails] Checking for response_fields in RFP data...')
        console.log('[fetchInvitationDetails] RFP data structure:', {
          has_response_fields: !!data.rfp.response_fields,
          response_fields_type: typeof data.rfp.response_fields,
          response_fields_value: data.rfp.response_fields,
          rfp_type: data.rfp.rfp_type
        })
        
        if (data.rfp.response_fields) {
          console.log('📋 [fetchInvitationDetails] Dynamic response fields received:', data.rfp.response_fields)
          console.log('[fetchInvitationDetails] Response fields type:', typeof data.rfp.response_fields, 'isArray:', Array.isArray(data.rfp.response_fields))
          
          // Parse response_fields - can be array or object with fields array
          if (Array.isArray(data.rfp.response_fields)) {
            console.log('[fetchInvitationDetails] Response fields is array, length:', data.rfp.response_fields.length)
            // Ensure each field has a unique name/id
            dynamicResponseFields.value = data.rfp.response_fields.map((field, idx) => ({
              ...field,
              name: field.name || field.id || field.label || `field_${idx}`,
              id: field.id || field.name || `field_${idx}`
            }))
          } else if (data.rfp.response_fields.fields && Array.isArray(data.rfp.response_fields.fields)) {
            console.log('[fetchInvitationDetails] Response fields has fields property, length:', data.rfp.response_fields.fields.length)
            // Ensure each field has a unique name/id
            dynamicResponseFields.value = data.rfp.response_fields.fields.map((field, idx) => ({
              ...field,
              name: field.name || field.id || field.label || `field_${idx}`,
              id: field.id || field.name || `field_${idx}`
            }))
          } else if (typeof data.rfp.response_fields === 'object') {
            console.log('[fetchInvitationDetails] Response fields is object, converting to array format')
            const keys = Object.keys(data.rfp.response_fields)
            console.log('[fetchInvitationDetails] Object keys:', keys)
            // Convert object to array format and ensure unique names
            dynamicResponseFields.value = keys.map((key, idx) => ({
              name: key,
              id: key,
              ...data.rfp.response_fields[key]
            }))
          }
          console.log('✅ [fetchInvitationDetails] Parsed dynamic response fields:', dynamicResponseFields.value)
          console.log('[fetchInvitationDetails] Number of dynamic fields:', dynamicResponseFields.value.length)
          // Log each field's name/id for debugging
          dynamicResponseFields.value.forEach((field, idx) => {
            console.log(`[fetchInvitationDetails] Field ${idx}: name="${field.name}", id="${field.id}", label="${field.label}"`)
          })
        } else {
          console.log('⚠️ [fetchInvitationDetails] No response_fields found in RFP data')
        }
        
        // Capture RFP-level documents field if present
        console.log('📋 Open RFP documents field:', data.rfp.documents)
        if (data.rfp.documents) {
          rfpDocuments.value = data.rfp.documents
          console.log('📋 Stored rfpDocuments:', rfpDocuments.value)
          // If right panel is on documents, resolve immediately
          if (rightPanelTab.value === 'documents') {
            await resolveRfpDocumentTabs()
          }
        } else {
          console.log('⚠️ No documents field found in open RFP response')
        }
      } else {
        throw new Error(data?.error || 'Failed to load RFP details')
      }
    } else if (invitationData.value.rfpId) {
      // Handle RFP with new parameter format
      const params = new URLSearchParams({
        rfpId: invitationData.value.rfpId,
        vendorId: invitationData.value.vendorId || '',
        invitationId: invitationData.value.invitationId || '',  // CRITICAL: Always include invitationId if available
        org: invitationData.value.org,
        vendorName: invitationData.value.vendorName,
        contactEmail: invitationData.value.contactEmail,
        contactPhone: invitationData.value.contactPhone
      })
      
      console.log('[fetchInvitationDetails] Fetching RFP details (invited RFP)...')
      console.log('[fetchInvitationDetails] API URL:', `${API_BASE_URL}/rfp-details/?${params}`)
      console.log('[fetchInvitationDetails] Query params:', params.toString())
      
      const response = await fetch(`${API_BASE_URL}/rfp-details/?${params}`, {
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        }
      })
      
      console.log('[fetchInvitationDetails] Response status:', response.status, response.statusText)
      const data = await parseJsonResponse(response, 'Unable to load RFP details')
      console.log('[fetchInvitationDetails] Response data received:', {
        success: data.success,
        has_rfp: !!data.rfp,
        rfp_id: data.rfp?.rfp_id,
        rfp_type: data.rfp?.rfp_type,
        has_response_fields: !!data.rfp?.response_fields,
        has_vendor: !!data.vendor
      })
      
      if (response.ok && data.success) {
        const rfp = data.rfp
        const vendor = data.vendor
        
        rfpInfo.value = {
          rfpTitle: rfp.rfp_title,
          rfpNumber: rfp.rfp_number,
          deadline: rfp.submission_deadline ? new Date(rfp.submission_deadline).toLocaleDateString() : 'TBD',
          budget: rfp.estimated_value ? `$${parseInt(rfp.estimated_value).toLocaleString()}` : 'TBD',
          description: rfp.description || '',
          rfpType: rfp.rfp_type || '',
          category: rfp.category || '',
          criticality: rfp.criticality_level || ''
        }
        
        // Capture dynamic response fields if present
        console.log('[fetchInvitationDetails] Checking for response_fields in RFP data (invited RFP)...')
        console.log('[fetchInvitationDetails] RFP data structure:', {
          has_response_fields: !!rfp.response_fields,
          response_fields_type: typeof rfp.response_fields,
          response_fields_value: rfp.response_fields,
          rfp_type: rfp.rfp_type,
          rfp_id: rfp.rfp_id
        })
        
        if (rfp.response_fields) {
          console.log('📋 [fetchInvitationDetails] Dynamic response fields received:', rfp.response_fields)
          console.log('[fetchInvitationDetails] Response fields type:', typeof rfp.response_fields, 'isArray:', Array.isArray(rfp.response_fields))
          
          // Parse response_fields - can be array or object with fields array
          if (Array.isArray(rfp.response_fields)) {
            console.log('[fetchInvitationDetails] Response fields is array, length:', rfp.response_fields.length)
            // Ensure each field has a unique name/id
            dynamicResponseFields.value = rfp.response_fields.map((field, idx) => ({
              ...field,
              name: field.name || field.id || field.label || `field_${idx}`,
              id: field.id || field.name || `field_${idx}`
            }))
          } else if (rfp.response_fields.fields && Array.isArray(rfp.response_fields.fields)) {
            console.log('[fetchInvitationDetails] Response fields has fields property, length:', rfp.response_fields.fields.length)
            // Ensure each field has a unique name/id
            dynamicResponseFields.value = rfp.response_fields.fields.map((field, idx) => ({
              ...field,
              name: field.name || field.id || field.label || `field_${idx}`,
              id: field.id || field.name || `field_${idx}`
            }))
          } else if (typeof rfp.response_fields === 'object') {
            console.log('[fetchInvitationDetails] Response fields is object, converting to array format')
            const keys = Object.keys(rfp.response_fields)
            console.log('[fetchInvitationDetails] Object keys:', keys)
            // Convert object to array format and ensure unique names
            dynamicResponseFields.value = keys.map((key, idx) => ({
              name: key,
              id: key,
              ...rfp.response_fields[key]
            }))
          }
          console.log('✅ [fetchInvitationDetails] Parsed dynamic response fields:', dynamicResponseFields.value)
          console.log('[fetchInvitationDetails] Number of dynamic fields:', dynamicResponseFields.value.length)
          // Log each field's name/id for debugging
          dynamicResponseFields.value.forEach((field, idx) => {
            console.log(`[fetchInvitationDetails] Field ${idx}: name="${field.name}", id="${field.id}", label="${field.label}"`)
          })
        } else {
          console.log('⚠️ [fetchInvitationDetails] No response_fields found in RFP data')
        }
        
        // Update form data with vendor details - prefill all available fields
        console.log('📋 Vendor data received:', vendor)
        
        // Basic company information
        if (vendor.org) formData.value.companyName = vendor.org
        if (vendor.legal_name) formData.value.legalName = vendor.legal_name
        if (vendor.business_type) formData.value.businessType = vendor.business_type
        if (vendor.industry_sector) formData.value.industrySector = vendor.industry_sector
        
        // Contact information
        if (vendor.vendor_name) formData.value.contactName = vendor.vendor_name
        if (vendor.contact_title) formData.value.contactTitle = vendor.contact_title
        if (vendor.contact_email) formData.value.email = vendor.contact_email
        if (vendor.contact_phone) formData.value.phone = vendor.contact_phone
        
        // Company details
        if (vendor.website) formData.value.website = vendor.website
        if (vendor.tax_id) formData.value.taxId = vendor.tax_id
        if (vendor.duns_number) formData.value.dunsNumber = vendor.duns_number
        if (vendor.incorporation_date) formData.value.incorporationDate = vendor.incorporation_date
        if (vendor.employee_count) formData.value.employeeCount = vendor.employee_count
        if (vendor.annual_revenue) formData.value.annualRevenue = vendor.annual_revenue
        if (vendor.headquarters_address) formData.value.headquartersAddress = vendor.headquarters_address
        if (vendor.headquarters_country) formData.value.headquartersCountry = vendor.headquarters_country
        if (vendor.years_in_business) formData.value.yearsInBusiness = vendor.years_in_business
        if (vendor.company_description) formData.value.companyDescription = vendor.company_description
        
        console.log('✅ Prefilled form with vendor data')

        // Capture RFP-level documents field if present (expects JSON with IDs)
        console.log('📋 RFP documents field:', rfp.documents)
        if (rfp.documents) {
          rfpDocuments.value = rfp.documents
          console.log('📋 Stored rfpDocuments:', rfpDocuments.value)
          // If right panel is on documents, resolve immediately
          if (rightPanelTab.value === 'documents') {
            await resolveRfpDocumentTabs()
          }
        } else {
          console.log('⚠️ No documents field found in RFP response')
        }
      } else {
        throw new Error(data?.error || 'Failed to fetch RFP details')
      }
    }
    
    // Load existing draft if available
    // This will load both draft and submitted response data
    await loadExistingDraft()
    
    // Note: loadExistingResponse is not called here because:
    // 1. The draft endpoint already handles both draft and submitted responses
    // 2. The /rfp-responses/ endpoint doesn't support GET requests (405 error)
    // 3. We use checkSubmissionStatusFromBackend for status checking instead
    
  } catch (error) {
    console.error('Error fetching RFP details:', error)
    showErrorToast('Error loading RFP details. Please refresh the page.')
  } finally {
    isLoading.value = false
  }
}

// Load existing RFP response data (for viewing/editing submitted responses)
// Note: This function is optional and will gracefully handle errors since draft loading is the primary method
const loadExistingResponse = async () => {
  try {
    if (!invitationData.value.rfpId) {
      return
    }
    
    // Skip if we already have data loaded from draft (to avoid duplicate loading)
    // The draft endpoint should handle both draft and submitted responses
    if (lastSavedAt.value) {
      console.log('ℹ️ Data already loaded from draft, skipping response loading')
      return
    }
    
    // Try using the check-status endpoint which we know works
    // This endpoint can provide response data if available
    const params = new URLSearchParams({
      rfpId: invitationData.value.rfpId
    })
    if (invitationData.value.vendorId) {
      params.append('vendorId', invitationData.value.vendorId)
    }
    if (invitationData.value.invitationId) {
      params.append('invitationId', invitationData.value.invitationId)
    }
    
    console.log('📥 Attempting to load existing response data via check-status...')
    
    const response = await fetch(`${API_BASE_URL}/rfp-responses/check-status/?${params}`, {
      headers: getAuthHeaders()
    })
    
    // Handle 404 gracefully - it's okay if there's no response
    if (response.status === 404) {
      console.log('ℹ️ No existing response found (404)')
      return
    }
    
    // Handle 405 (Method Not Allowed) or other errors gracefully
    if (response.status === 405) {
      console.log('ℹ️ Response endpoint not available (405) - this is normal, using draft data instead')
      return
    }
    
    if (!response.ok) {
      console.log(`ℹ️ Response endpoint returned ${response.status} - using draft data instead`)
      return
    }
    
    const data = await response.json()
    
    // The check-status endpoint might return response data in a different format
    // Only process if we have actual response documents
    if (data.success && data.response_id && data.response_documents) {
      console.log('✅ Found existing response data from check-status')
      
      const responseDocs = data.response_documents
      
      // Only load if fields are not already populated (from draft)
      // Load company info
      if (responseDocs.companyInfo) {
        Object.keys(responseDocs.companyInfo).forEach(key => {
          if (responseDocs.companyInfo[key] !== null && 
              responseDocs.companyInfo[key] !== undefined && 
              responseDocs.companyInfo[key] !== '' && 
              !formData.value[key]) {
            formData.value[key] = responseDocs.companyInfo[key]
          }
        })
      }
      
      // Load financial info
      if (responseDocs.financialInfo) {
        Object.keys(responseDocs.financialInfo).forEach(key => {
          if (responseDocs.financialInfo[key] !== null && 
              responseDocs.financialInfo[key] !== undefined && 
              responseDocs.financialInfo[key] !== '' && 
              !formData.value[key]) {
            formData.value[key] = responseDocs.financialInfo[key]
          }
        })
      }
      
      // Load RFP responses
      if (responseDocs.rfpResponses) {
        Object.keys(responseDocs.rfpResponses).forEach(key => {
          const value = responseDocs.rfpResponses[key]
          if (value !== undefined && value !== null) {
            setCriteriaResponse(key, value)
          }
        })
      }
      
      // Load team info
      if (responseDocs.teamInfo) {
        if (responseDocs.teamInfo.totalTeamSize && !formData.value.totalTeamSize) {
          formData.value.totalTeamSize = responseDocs.teamInfo.totalTeamSize
        }
        if (responseDocs.teamInfo.teamStructure && !formData.value.teamStructure) {
          formData.value.teamStructure = responseDocs.teamInfo.teamStructure
        }
        if (responseDocs.teamInfo.projectMethodology && !formData.value.projectMethodology) {
          formData.value.projectMethodology = responseDocs.teamInfo.projectMethodology
        }
        if (responseDocs.teamInfo.communicationPlan && !formData.value.communicationPlan) {
          formData.value.communicationPlan = responseDocs.teamInfo.communicationPlan
        }
        if (responseDocs.teamInfo.keyPersonnel && Array.isArray(responseDocs.teamInfo.keyPersonnel) && responseDocs.teamInfo.keyPersonnel.length > 0) {
          keyPersonnel.value = responseDocs.teamInfo.keyPersonnel
        }
      }
      
      // Load compliance info
      if (responseDocs.compliance) {
        Object.keys(responseDocs.compliance).forEach(key => {
          if (key === 'references' && Array.isArray(responseDocs.compliance[key]) && responseDocs.compliance[key].length > 0) {
            formData.value.references = responseDocs.compliance[key]
          } else if (responseDocs.compliance[key] !== null && responseDocs.compliance[key] !== undefined && !formData.value[key]) {
            formData.value[key] = responseDocs.compliance[key]
          }
        })
      }
      
      // Update completion status
      updateCompletionStatus()
      
      console.log('✅ Loaded existing response data from check-status')
    } else {
      console.log('ℹ️ No response documents found in check-status response')
    }
  } catch (error) {
    // Silently handle errors - this is an optional function
    // The draft loading should handle most cases
    console.log('ℹ️ Could not load response data (this is optional):', error.message)
  }
}

const fetchEvaluationCriteria = async () => {
  // Try to get RFP number from rfpInfo first
  let rfpNumber = rfpInfo.value?.rfpNumber
  
  // If not available, try to get it from invitationData
  if (!rfpNumber && invitationData.value?.rfpId) {
    console.log('⚠️ RFP number not in rfpInfo, will try to fetch from RFP ID:', invitationData.value.rfpId)
    // We'll fetch the RFP details to get the number
    try {
      const rfpResponse = await fetch(`${API_BASE_URL}/rfps/${invitationData.value.rfpId}/`, {
        headers: getAuthHeaders()
      })
      if (rfpResponse.ok) {
        const rfpData = await rfpResponse.json()
        if (rfpData.rfp_number) {
          rfpNumber = rfpData.rfp_number
          // Update rfpInfo with the number
          if (rfpInfo.value) {
            rfpInfo.value.rfpNumber = rfpNumber
          }
          console.log('✅ Retrieved RFP number from API:', rfpNumber)
        }
      }
    } catch (error) {
      console.error('Error fetching RFP number:', error)
    }
  }
  
  if (!rfpNumber) {
    console.warn('⚠️ Cannot fetch evaluation criteria: RFP number not available')
    console.log('Current rfpInfo:', rfpInfo.value)
    console.log('Current invitationData:', invitationData.value)
    return
  }
  
  console.log('📋 Fetching evaluation criteria for RFP:', rfpNumber)
  
  try {
    const response = await fetch(`${API_BASE_URL}/rfp/${rfpNumber}/evaluation-criteria/`, {
      headers: getAuthHeaders()
    })
    
    if (!response.ok) {
      console.error('❌ Failed to fetch evaluation criteria:', response.status, response.statusText)
      const errorText = await response.text()
      console.error('Error response:', errorText)
      return
    }
    
    const data = await response.json()
    console.log('📥 Evaluation criteria response:', data)
    
    if (data.success && data.criteria && Array.isArray(data.criteria)) {
      // Update evaluation criteria with real data
      evaluationCriteria.value = data.criteria.map(criterion => ({
        id: criterion.criteria_id,
        title: criterion.criteria_name,
        weight: criterion.weight_percentage,
        description: criterion.criteria_description,
        type: criterion.evaluation_type === 'narrative' ? 'narrative' : 'text',
        required: criterion.is_mandatory
      }))
      
      console.log('✅ Loaded evaluation criteria:', evaluationCriteria.value.length, 'criteria')
      
      // Initialize responses for each criterion
      evaluationCriteria.value.forEach(criterion => {
        const existing = responses.value?.[criterion.id]
        setCriteriaResponse(criterion.id, existing || createEmptyResponseEntry())

      })
      
      // Update completion status
      updateCompletionStatus()
    } else {
      console.warn('⚠️ No criteria found in response or invalid format:', data)
      evaluationCriteria.value = []
    }
  } catch (error) {
    console.error('❌ Error fetching evaluation criteria:', error)
    evaluationCriteria.value = []
  }
}

// Check submission status from backend
const checkSubmissionStatusFromBackend = async () => {
  try {
    if (!invitationData.value.rfpId) {
      console.log('⚠️ No RFP ID available for status check')
      return
    }
    
    const params = new URLSearchParams({
      rfpId: invitationData.value.rfpId
    })
    
    if (invitationData.value.vendorId) {
      params.append('vendorId', invitationData.value.vendorId)
    }
    if (invitationData.value.invitationId) {
      params.append('invitationId', invitationData.value.invitationId)
    }
    
    console.log('🔍 Checking submission status with params:', params.toString())
    
    const response = await fetch(`${API_BASE_URL}/rfp-responses/check-status/?${params}`, {
      headers: getAuthHeaders()
    })
    
    if (!response.ok) {
      console.log('⚠️ Backend status check failed with status:', response.status)
      return
    }
    
    const data = await response.json()
    console.log('📥 Backend status response:', data)
    
    // Only set as submitted if we have a valid response with actual submission data
    if (data.success && data.submitted && data.response_id) {
      console.log('✅ Found valid existing submission in database:', data)
      submissionStatus.value = 'SUBMITTED'
      submittedAt.value = data.submitted_at || new Date().toISOString()
      
      // Update localStorage with backend data
      localStorage.setItem('rfp_submission_status', 'SUBMITTED')
      localStorage.setItem('rfp_submitted_at', submittedAt.value)
      localStorage.setItem('rfp_response_id', data.response_id)
    } else if (data.success && data.response_id && data.is_draft) {
      console.log('📝 Found existing draft in database:', data)
      // Don't set as submitted, but keep the response_id for potential updates
      localStorage.setItem('rfp_response_id', data.response_id)
      // Clear submission status to allow new submission
      localStorage.removeItem('rfp_submission_status')
      localStorage.removeItem('rfp_submitted_at')
    } else {
      console.log('ℹ️ No valid existing submission found in database')
      // Clear any stale localStorage data
      localStorage.removeItem('rfp_submission_status')
      localStorage.removeItem('rfp_submitted_at')
      localStorage.removeItem('rfp_response_id')
    }
  } catch (error) {
    console.error('❌ Error checking submission status:', error)
    // Don't set any status on error - let the form remain in draft state
  }
}

// Load existing draft data
const loadExistingDraft = async () => {
  try {
    // Check if there's an existing response
    if (!invitationData.value.rfpId) {
      console.log('⚠️ No RFP ID available for draft loading')
      return
    }
    
    // Build query parameters - only include non-empty values
    const params = new URLSearchParams()
    if (invitationData.value.vendorId) {
      params.append('vendorId', invitationData.value.vendorId)
    }
    if (invitationData.value.invitationId) {
      params.append('invitationId', invitationData.value.invitationId)
    }
    
    const queryString = params.toString()
    const url = `${API_BASE_URL}/rfp-responses/draft/${invitationData.value.rfpId}/${queryString ? `?${queryString}` : ''}`
    
    console.log('📥 Loading draft from:', url)
    
    const response = await fetch(url, {
      headers: getAuthHeaders()
    })
    
    // Handle 404 gracefully - it's okay if there's no draft yet
    if (response.status === 404) {
      console.log('ℹ️ No existing draft found (404) - this is normal for new submissions')
      return
    }
    
    if (!response.ok) {
      console.error('❌ Error loading draft:', response.status, response.statusText)
      return
    }
    
    const data = await response.json()
    console.log('📥 Draft response:', data)
    
    if (data.success && data.draft) {
      console.log('✅ Found existing draft, loading data...')
      
      // Load draft data
      if (data.draft.proposal_data) {
        const proposalData = data.draft.proposal_data
        console.log('📋 Loading proposal data:', proposalData)
        
        // Load company info - merge carefully to preserve existing values
        if (proposalData.companyInfo) {
          Object.keys(proposalData.companyInfo).forEach(key => {
            if (proposalData.companyInfo[key] !== null && proposalData.companyInfo[key] !== undefined && proposalData.companyInfo[key] !== '') {
              formData.value[key] = proposalData.companyInfo[key]
            }
          })
          console.log('✅ Loaded company info')
        }
        
        // Load responses
        if (proposalData.responses) {
          Object.keys(proposalData.responses).forEach(key => {
            const value = proposalData.responses[key]
            if (value !== undefined && value !== null) {
              setCriteriaResponse(key, value)
            }
          })
          console.log('✅ Loaded responses:', Object.keys(proposalData.responses).length, 'responses')
        }
        
        // Load documents metadata (actual documents are loaded separately)
        if (proposalData.documents) {
          documents.value = proposalData.documents
          console.log('✅ Loaded documents metadata')
        }
        
        // Load key personnel
        if (proposalData.keyPersonnel && Array.isArray(proposalData.keyPersonnel)) {
          keyPersonnel.value = proposalData.keyPersonnel.length > 0 
            ? proposalData.keyPersonnel 
            : keyPersonnel.value
          console.log('✅ Loaded key personnel:', keyPersonnel.value.length, 'members')
        }
      }
      
      // Also check for responseDocuments structure (newer format)
      if (data.draft.response_documents) {
        const responseDocs = data.draft.response_documents
        console.log('📋 Loading response documents structure...')
        
        // Load company info from responseDocuments
        if (responseDocs.companyInfo) {
          Object.keys(responseDocs.companyInfo).forEach(key => {
            if (responseDocs.companyInfo[key] !== null && responseDocs.companyInfo[key] !== undefined && responseDocs.companyInfo[key] !== '') {
              formData.value[key] = responseDocs.companyInfo[key]
            }
          })
        }
        
        // Load financial info
        if (responseDocs.financialInfo) {
          Object.keys(responseDocs.financialInfo).forEach(key => {
            if (responseDocs.financialInfo[key] !== null && responseDocs.financialInfo[key] !== undefined && responseDocs.financialInfo[key] !== '') {
              formData.value[key] = responseDocs.financialInfo[key]
            }
          })
        }
        
        // Load RFP responses
        if (responseDocs.rfpResponses) {
          Object.keys(responseDocs.rfpResponses).forEach(key => {
            const value = responseDocs.rfpResponses[key]
            if (value !== undefined && value !== null) {
              setCriteriaResponse(key, value)
 
            }
          })
        }
        
        // Load team info
        if (responseDocs.teamInfo) {
          if (responseDocs.teamInfo.totalTeamSize) formData.value.totalTeamSize = responseDocs.teamInfo.totalTeamSize
          if (responseDocs.teamInfo.teamStructure) formData.value.teamStructure = responseDocs.teamInfo.teamStructure
          if (responseDocs.teamInfo.projectMethodology) formData.value.projectMethodology = responseDocs.teamInfo.projectMethodology
          if (responseDocs.teamInfo.communicationPlan) formData.value.communicationPlan = responseDocs.teamInfo.communicationPlan
          if (responseDocs.teamInfo.keyPersonnel && Array.isArray(responseDocs.teamInfo.keyPersonnel)) {
            keyPersonnel.value = responseDocs.teamInfo.keyPersonnel.length > 0 
              ? responseDocs.teamInfo.keyPersonnel 
              : keyPersonnel.value
          }
        }
        
        // Load compliance info
        if (responseDocs.compliance) {
          Object.keys(responseDocs.compliance).forEach(key => {
            if (key === 'references' && Array.isArray(responseDocs.compliance[key])) {
              formData.value.references = responseDocs.compliance[key]
            } else if (responseDocs.compliance[key] !== null && responseDocs.compliance[key] !== undefined) {
              formData.value[key] = responseDocs.compliance[key]
            }
          })
        }

        // Load custom dynamic field definitions if present
        if (Array.isArray(responseDocs.customDynamicFields) && responseDocs.customDynamicFields.length > 0) {
          console.log('[loadExistingDraft] Hydrating custom dynamic fields from responseDocs')
          hydrateCustomFieldDefinitions(responseDocs.customDynamicFields)
        }
        
        // Load dynamic fields
        console.log('[loadExistingDraft] Checking for dynamic fields in responseDocs...')
        console.log('[loadExistingDraft] responseDocs.dynamicFields:', responseDocs.dynamicFields)
        
        if (responseDocs.dynamicFields) {
          console.log('[loadExistingDraft] Loading dynamic fields from responseDocs.dynamicFields')
          const savedKeys = Object.keys(responseDocs.dynamicFields)
          console.log('[loadExistingDraft] Saved dynamic fields keys:', savedKeys)
          console.log('[loadExistingDraft] Available dynamicResponseFields:', allDynamicResponseFields.value.map(f => ({
            name: f.name,
            id: f.id,
            _originalName: f._originalName,
            _uniqueKey: f._uniqueKey
          })))
          
          // Map saved field names back to unique keys
          savedKeys.forEach(savedKey => {
            // Find the field that matches this saved key (by original name)
            const matchingField = allDynamicResponseFields.value.find(f => {
              const originalName = f._originalName || f.name || f.id
              return originalName === savedKey
            })
            
            if (matchingField) {
              // Get the unique key for this field
              const fieldIndex = allDynamicResponseFields.value.indexOf(matchingField)
              const uniqueKey = matchingField._uniqueKey || getFieldKey(matchingField, fieldIndex)
              
              // Load the value using the unique key
              const value = responseDocs.dynamicFields[savedKey]
              if (value !== null && value !== undefined && value !== '') {
                dynamicResponseData.value[uniqueKey] = value
                console.log(`[loadExistingDraft] Mapped dynamic field - savedKey: "${savedKey}" -> uniqueKey: "${uniqueKey}" = "${value}"`)
              }
            } else {
              // If no matching field found, try to hydrate from stored definitions or load directly
              console.warn(`[loadExistingDraft] No matching field found for saved key: "${savedKey}", attempting to hydrate definition`)
              const storedDefinition = Array.isArray(responseDocs.customDynamicFields)
                ? responseDocs.customDynamicFields.find(def => (def.name || def.id) === savedKey)
                : null

              const storedValue = responseDocs.dynamicFields[savedKey]
              if (storedDefinition) {
                const hydratedField = upsertCustomFieldDefinition(storedDefinition)
                if (hydratedField) {
                  const uniqueKey = hydratedField._uniqueKey || hydratedField.name
                  if (storedValue !== null && storedValue !== undefined && storedValue !== '') {
                    dynamicResponseData.value[uniqueKey] = storedValue
                  }
                }
              } else if (storedValue !== null && storedValue !== undefined) {
                const inferredDefinition = {
                  name: savedKey,
                  label: savedKey,
                  type: typeof storedValue === 'number' ? 'number' : 'text'
                }
                const newField = upsertCustomFieldDefinition(inferredDefinition)
                if (newField) {
                  const uniqueKey = newField._uniqueKey || newField.name
                  dynamicResponseData.value[uniqueKey] = storedValue
                } else {
                  dynamicResponseData.value[savedKey] = storedValue
                }
              }
            }
          })
          
          console.log('✅ [loadExistingDraft] Loaded dynamic fields:', dynamicResponseData.value)
          console.log('[loadExistingDraft] Total dynamic fields loaded:', Object.keys(dynamicResponseData.value).length)
        } else {
          console.log('[loadExistingDraft] No dynamicFields found in responseDocs')
        }
      }
      
      // Hydrate custom fields from proposal_data when available
      if (data.draft.proposal_data && Array.isArray(data.draft.proposal_data.customDynamicFields)) {
        console.log('[loadExistingDraft] Hydrating custom dynamic fields from proposal_data')
        hydrateCustomFieldDefinitions(data.draft.proposal_data.customDynamicFields)
      }

      // Also check proposal_data for dynamic fields (backward compatibility)
      if (data.draft.proposal_data && data.draft.proposal_data.dynamicFields) {
        const savedKeys = Object.keys(data.draft.proposal_data.dynamicFields)
        savedKeys.forEach(savedKey => {
          // Find the field that matches this saved key
          const matchingField = allDynamicResponseFields.value.find(f => {
            const originalName = f._originalName || f.name || f.id
            return originalName === savedKey
          })
          
          if (matchingField) {
            const fieldIndex = allDynamicResponseFields.value.indexOf(matchingField)
            const uniqueKey = matchingField._uniqueKey || getFieldKey(matchingField, fieldIndex)
            const value = data.draft.proposal_data.dynamicFields[savedKey]
            if (value !== null && value !== undefined && value !== '') {
              dynamicResponseData.value[uniqueKey] = value
              console.log(`[loadExistingDraft] Mapped dynamic field from proposal_data - savedKey: "${savedKey}" -> uniqueKey: "${uniqueKey}"`)
            }
          } else {
            // Fallback: load directly
            const storedValue = data.draft.proposal_data.dynamicFields[savedKey]
            if (storedValue !== null && storedValue !== undefined) {
              const inferredDefinition = {
                name: savedKey,
                label: savedKey,
                type: typeof storedValue === 'number' ? 'number' : 'text'
              }
              const newField = upsertCustomFieldDefinition(inferredDefinition)
              if (newField) {
                const uniqueKey = newField._uniqueKey || newField.name
                dynamicResponseData.value[uniqueKey] = storedValue
              } else {
                dynamicResponseData.value[savedKey] = storedValue
              }
            }
          }
        })
        console.log('✅ Loaded dynamic fields from proposal_data:', dynamicResponseData.value)
      }
      
      // Update status
      if (data.draft.submission_status) {
        submissionStatus.value = data.draft.submission_status
      }
      if (data.draft.last_saved_at) {
        lastSavedAt.value = data.draft.last_saved_at
      }
      if (data.draft.response_id) {
      localStorage.setItem('rfp_response_id', data.draft.response_id)
      }
 
      
      // Update completion status after loading
      updateCompletionStatus()
      
      console.log('✅ Draft data loaded successfully')
    } else {
      console.log('ℹ️ No draft data in response')
    }
  } catch (error) {
    console.error('❌ Error loading draft:', error)
    // Don't show error toast for draft loading failures - it's optional
  }
}

// Helper function to check if a field is filled
const isFieldFilled = (value) => {
  if (value === null || value === undefined) return false
  if (typeof value === 'boolean') return value
  if (typeof value === 'string') return value.trim().length > 0
  if (typeof value === 'number') return value > 0
  return false
}

// Update completion status based on form data
const updateCompletionStatus = () => {
  console.log('🔄 Updating completion status...')
  
  // Ensure all reactive data is properly initialized
  ensureReactiveData()
  
  // Company info completion
  const companyFields = [
    'companyName', 'legalName', 'businessType', 'industrySector',
    'contactName', 'contactTitle', 'email', 'phone',
    'taxId', 'incorporationDate', 'employeeCount', 'annualRevenue',
    'headquartersAddress', 'headquartersCountry', 'yearsInBusiness', 'companyDescription'
  ]
  const filledCompanyFields = companyFields.filter(field => isFieldFilled(formData.value[field]))
  completionStatus.value.company = Math.round((filledCompanyFields.length / companyFields.length) * 100)
  console.log(`📊 Company completion: ${completionStatus.value.company}% (${filledCompanyFields.length}/${companyFields.length} fields filled)`)
  
  // Financial info completion
  const financialFields = [
    'proposedValue', 'currency', 'pricingBreakdown', 'paymentTerms', 'projectDuration'
  ]
  const filledFinancialFields = financialFields.filter(field => isFieldFilled(formData.value[field]))
  completionStatus.value.financial = Math.round((filledFinancialFields.length / financialFields.length) * 100)
  
  // Responses completion
  const totalCriteria = (evaluationCriteria.value || []).length
  const filledResponses = (evaluationCriteria.value || []).reduce((count, criterion) => {
    return count + (responseHasContent(responses.value?.[criterion.id]) ? 1 : 0)
  }, 0)
 
  completionStatus.value.responses = totalCriteria > 0 ? Math.round((filledResponses / totalCriteria) * 100) : 0
  
  // Documents completion - updated for array structure
  const uploadedDocumentsCount = Array.isArray(uploadedDocuments.value) 
    ? uploadedDocuments.value.filter(doc => doc.uploaded).length 
    : 0
  const totalDocumentsCount = Array.isArray(uploadedDocuments.value) 
    ? uploadedDocuments.value.length 
    : 0
  
  // Give completion based on uploaded documents
  if (totalDocumentsCount > 0) {
    completionStatus.value.documents = Math.round((uploadedDocumentsCount / totalDocumentsCount) * 100)
  } else {
    completionStatus.value.documents = 0
  }
  console.log(`📄 Documents completion: ${completionStatus.value.documents}% (${uploadedDocumentsCount}/${totalDocumentsCount} documents uploaded)`)
  
  // Personnel completion - give base completion for having at least one person
  const totalPersonnel = (keyPersonnel.value || []).length
  const filledPersonnel = (keyPersonnel.value || []).filter(person => 
    isFieldFilled(person.name) && isFieldFilled(person.role) && isFieldFilled(person.email) && 
    isFieldFilled(person.experience) && isFieldFilled(person.relevantExperience)
  ).length
  
  if (totalPersonnel > 0) {
    // Give 50% base completion for having personnel, plus bonus for complete entries
    const basePersonnelCompletion = 50
    const bonusPerCompletePerson = 50 / totalPersonnel
    completionStatus.value.personnel = Math.min(100, basePersonnelCompletion + (filledPersonnel * bonusPerCompletePerson))
  } else {
    // Give 25% completion even if no personnel added yet
    completionStatus.value.personnel = 25
  }
  
  // Compliance completion - make more lenient
  const complianceFields = [
    'dataSecurityMeasures', 'complianceStandards', 'professionalLiability', 'generalLiability'
  ]
  const filledComplianceFields = complianceFields.filter(field => isFieldFilled(formData.value[field])).length
  const referencesComplete = (formData.value.references || []).every(ref => 
    isFieldFilled(ref.companyName) && isFieldFilled(ref.contactPerson) && 
    isFieldFilled(ref.email) && isFieldFilled(ref.projectDescription)
  )
  
  // Give 30% base completion for compliance section
  const baseComplianceCompletion = 30
  const complianceFieldScore = (filledComplianceFields / complianceFields.length) * 50 // Max 50% for fields
  const referencesScore = referencesComplete ? 20 : 0 // 20% for complete references
  completionStatus.value.compliance = Math.min(100, baseComplianceCompletion + complianceFieldScore + referencesScore)
}

const handleAutoSave = async () => {
  // AUTO-SAVE DISABLED: This function is now only called manually (on explicit save button click)
  // Don't auto-save if already submitted or currently submitting
  if (submissionStatus.value === 'SUBMITTED' || isSubmitting.value) {
    return
  }
  
  // CRITICAL: Only save if there's meaningful data (at least 30% completion for manual saves)
  // This prevents creating empty draft entries
  const currentProgress = overallProgress.value || 0
  if (currentProgress < 30) {
    console.log('⏭️ Skipping save - completion too low:', currentProgress + '%')
    showErrorToast('Please fill at least 30% of the form before saving')
    return
  }
  
  // Check if there's at least some basic company info filled
  const hasBasicInfo = formData.value.companyName || formData.value.contactName || formData.value.email
  if (!hasBasicInfo) {
    console.log('⏭️ Skipping save - no basic company info')
    showErrorToast('Please fill in basic company information before saving')
    return
  }
  
  try {
    // Update completion status first
    updateCompletionStatus()
    // Validate dynamic fields silently to surface inline errors
    validateAllDynamicFields(false)
    
    // Prepare draft data with safe values
    // Map dynamic fields from unique keys back to original names
    const mappedDynamicFields = buildDynamicFieldValueMap()
    
    const serializedResponses = {}
    Object.entries(responses.value || {}).forEach(([key, value]) => {
      serializedResponses[key] = normalizeResponseEntry(value, key)
    })
    serializedResponses.customFields = categoryCustomFieldData.value.responses || {}

    const companyInfoData = cloneDeep(formData.value, {}) || {}
    companyInfoData.customFields = categoryCustomFieldData.value.company || {}
 
    const draftData = {
      companyInfo: companyInfoData,
      financialInfo: {
        proposedValue: formData.value.proposedValue || '',
        currency: formData.value.currency || 'USD',
        pricingBreakdown: formData.value.pricingBreakdown || '',
        paymentTerms: formData.value.paymentTerms || '',
        projectDuration: formData.value.projectDuration || '',
        creditRating: formData.value.creditRating || '',
        insuranceCoverage: formData.value.insuranceCoverage || '',
        customFields: categoryCustomFieldData.value.financial || {}
      },
      responses: serializedResponses,
      documents: cloneDeep(documents.value, []),
      keyPersonnel: cloneDeep(keyPersonnel.value, []),
      teamInfo: {
        totalTeamSize: formData.value.totalTeamSize || '',
        teamStructure: formData.value.teamStructure || '',
        projectMethodology: formData.value.projectMethodology || '',
        communicationPlan: formData.value.communicationPlan || '',
        keyPersonnel: keyPersonnel.value || [],
        customFields: categoryCustomFieldData.value.team || {}
      },
      compliance: {
        iso9001: formData.value.iso9001 || false,
        iso27001: formData.value.iso27001 || false,
        iso14001: formData.value.iso14001 || false,
        soc2: formData.value.soc2 || false,
        pciDss: formData.value.pciDss || false,
        hippa: formData.value.hippa || false,
        dataSecurityMeasures: formData.value.dataSecurityMeasures || '',
        complianceStandards: formData.value.complianceStandards || '',
        professionalLiability: formData.value.professionalLiability || '',
        generalLiability: formData.value.generalLiability || '',
        references: formData.value.references || [],
        customFields: categoryCustomFieldData.value.compliance || {}
      },
      uploadedDocuments: (() => {
        // Convert array to object format for backend
        if (Array.isArray(uploadedDocuments.value) && uploadedDocuments.value.length > 0) {
          const docMap = {}
          uploadedDocuments.value.forEach((doc, index) => {
            if (doc && (doc.s3Id || doc.url || doc.name)) {
              const key = doc.s3Id || doc.name || `doc_${index}`
              docMap[key] = {
                name: doc.name || doc.fileName || `Document ${index + 1}`,
                fileName: doc.fileName || doc.name,
                fileSize: doc.fileSize || doc.size || 0,
                fileType: doc.fileType || doc.content_type || 'pdf',
                url: doc.url || null,
                key: doc.key || doc.s3_key || null,
                uploaded: doc.uploaded !== false,
                s3Id: doc.s3Id || null,
                isMerged: doc.isMerged || false
              }
            }
          })
          docMap.customFields = categoryCustomFieldData.value.documents || {}
          return docMap
        }
        // Fallback to object format if already an object
        return {
          ...(uploadedDocuments.value || {}),
          customFields: categoryCustomFieldData.value.documents || {}
        }
      })(),
      dynamicFields: mappedDynamicFields, // Include mapped dynamic fields
      customDynamicFields: serializeCustomFieldDefinitions(),
      completionPercentage: overallProgress.value,
      lastSaved: new Date().toISOString()
    }
    
    // Save draft to backend
    const response = await fetch(`${API_BASE_URL}/rfp-responses/draft/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        rfpId: invitationData.value.rfpId || null,
        vendorId: invitationData.value.vendorId ? parseInt(invitationData.value.vendorId) : null,
        invitationId: invitationData.value.invitationId || null,  // This is critical for linking to the invitation
        org: formData.value.companyName || '',
        vendorName: formData.value.contactName || '',
        contactEmail: formData.value.email || '',
        contactPhone: formData.value.phone || '',
        proposalData: draftData,
        submissionStatus: 'DRAFT',
        completionPercentage: Math.max(0, Math.min(100, overallProgress.value || 0)),
        
        // Debug info
        _debug: {
          invitationData: { ...invitationData.value },
          formData: { ...formData.value }
        }
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      lastSavedAt.value = new Date().toISOString()
      showSuccessToast('Draft saved successfully')
      if (data.response_id) {
        localStorage.setItem('rfp_response_id', data.response_id)
      }
    } else {
      console.error('Draft save failed:', data.error)
    }
  } catch (error) {
    console.error('Error saving draft:', error)
  }
}

const createUnmatchedVendor = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/rfp-responses/create-unmatched-vendor/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        rfpId: invitationData.value.rfpId,
        vendorName: formData.value.contactName || '',
        contactEmail: formData.value.email || '',
        org: formData.value.companyName || '',
        contactPhone: formData.value.phone || '',
        utmParameters: utmParameters.value,
        submissionData: {
          companyInfo: cloneDeep(formData.value, {}),
          responses: Object.entries(responses.value || {}).reduce((acc, [key, value]) => {
            acc[key] = normalizeResponseEntry(value, key)
            return acc
          }, {}),
          documents: cloneDeep(uploadedDocuments.value, {}),
          keyPersonnel: cloneDeep(keyPersonnel.value, [])

        },
        baseUrl: buildDynamicUrl()
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      // Update invitation data with the created unmatched vendor and invitation
      invitationData.value.vendorId = data.unmatched_vendor_id
      invitationData.value.invitationId = data.invitation_id
      invitationData.value.isOpenRfp = true
      
      console.log('✅ Created unmatched vendor:', data)
      return data
    } else {
      throw new Error(data.error || 'Failed to create unmatched vendor')
    }
  } catch (error) {
    console.error('Error creating unmatched vendor:', error)
    throw error
  }
}

// Trigger risk analysis for a submitted RFP response
const triggerRiskAnalysis = async (responseId) => {
  try {
    console.log('🔍 Triggering risk analysis for response ID:', responseId)
    
    const response = await fetch(`${API_BASE_URL}/test-risk-analysis/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({
        response_id: responseId
      })
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ Risk analysis request failed:', response.status, errorText)
      return {
        success: false,
        error: `HTTP ${response.status}: ${errorText}`
      }
    }
    
    const data = await response.json()
    console.log('📥 Risk analysis response:', data)
    
    return data
  } catch (error) {
    console.error('❌ Error calling risk analysis endpoint:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

// Submission lock to prevent multiple simultaneous submissions
const submissionInProgress = ref(false)

const handleSubmit = async () => {
  // CRITICAL: Prevent multiple simultaneous submissions
  if (submissionInProgress.value || isSubmitting.value) {
    console.warn('⏭️ Submission already in progress, ignoring duplicate call')
    return
  }
  
  if (submissionStatus.value === 'SUBMITTED') {
    showWarningToast('This proposal has already been submitted.')
    return
  }
  
  if (overallProgress.value < 50) {
    showWarningToast('Please complete at least 50% of the required sections before submitting.')
    return
  }
  
  // Set submission lock
  submissionInProgress.value = true
  isSubmitting.value = true
  
  try {
    if (!validateAllDynamicFields(true)) {
      submissionInProgress.value = false
      isSubmitting.value = false
      return
    }
    // Update completion status
    updateCompletionStatus()
    
    // For open submissions without existing vendor/invitation, create unmatched vendor first
    // Check if it's an open RFP: either flag is set OR both vendorId and invitationId are empty with rfpId present
    const isOpenRfpSubmission = invitationData.value.isOpenRfp || 
                                 (!invitationData.value.vendorId && 
                                  !invitationData.value.invitationId && 
                                  invitationData.value.rfpId)
    
    if (isOpenRfpSubmission && !invitationData.value.vendorId && !invitationData.value.invitationId) {
      console.log('🌐 Creating unmatched vendor for open submission...')
      console.log('🌐 Current invitationData:', invitationData.value)
      try {
        const unmatchedData = await createUnmatchedVendor()
        console.log('✅ Unmatched vendor created:', unmatchedData)
        console.log('✅ Updated invitationData:', invitationData.value)
        
        // Ensure IDs are set after creation
        if (unmatchedData && unmatchedData.success) {
          invitationData.value.vendorId = unmatchedData.unmatched_vendor_id || invitationData.value.vendorId
          invitationData.value.invitationId = unmatchedData.invitation_id || invitationData.value.invitationId
          invitationData.value.isOpenRfp = true
          console.log('✅ Final invitationData after unmatched vendor creation:', invitationData.value)
        }
      } catch (error) {
        console.error('❌ Failed to create unmatched vendor:', error)
        showErrorToast('Failed to initialize submission. Please try again.')
        submissionInProgress.value = false
        isSubmitting.value = false
        return
      }
    }
    
    // CRITICAL: Disable auto-save completely during submission
    // This prevents race conditions and duplicate saves
    
    // Prepare proposal data according to database schema
    console.log('[submitResponse] Preparing proposal data...')
    console.log('[submitResponse] Current responses.value:', responses.value)
    console.log('[submitResponse] Responses keys:', Object.keys(responses.value || {}))
    console.log('[submitResponse] Dynamic response data:', dynamicResponseData.value)
    console.log('[submitResponse] Dynamic response fields count:', allDynamicResponseFields.value.length)
    console.log('[submitResponse] Dynamic response data keys:', Object.keys(dynamicResponseData.value))
    
    // CRITICAL: Ensure ALL responses are properly collected
    // Include all responses (even empty ones) to maintain data structure
    const responsesToSubmit = {}
    Object.entries(responses.value || {}).forEach(([key, value]) => {
      const normalized = normalizeResponseEntry(value, key)
      // Always include the response to maintain structure
      // The backend can handle empty responses
      responsesToSubmit[key] = normalized
      console.log(`[submitResponse] Including response ${key}:`, {
        hasHtmlContent: !!normalized.htmlContent,
        htmlContentLength: normalized.htmlContent?.length || 0,
        hasAttachments: normalized.attachments?.length > 0,
        attachmentsCount: normalized.attachments?.length || 0,
        hasTextContent: !!normalized.textContent
      })
    })
    
    // Add custom fields
    responsesToSubmit.customFields = categoryCustomFieldData.value.responses || {}
    
    console.log('[submitResponse] Final serialized responses:', {
      totalResponses: Object.keys(responsesToSubmit).length,
      responseKeys: Object.keys(responsesToSubmit).filter(k => k !== 'customFields'),
      hasCustomFields: !!responsesToSubmit.customFields
    })
    
    const serializedResponses = responsesToSubmit
 
    const proposalCompanyInfo = cloneDeep(formData.value, {}) || {}
    proposalCompanyInfo.customFields = categoryCustomFieldData.value.company || {}

    // Handle uploadedDocuments - it's an array, convert to object format for backend
    let uploadedDocumentsPayload = {}
    if (Array.isArray(uploadedDocuments.value) && uploadedDocuments.value.length > 0) {
      // Convert array to object format for backend compatibility
      uploadedDocuments.value.forEach((doc, index) => {
        if (doc && doc.s3Id) {
          uploadedDocumentsPayload[doc.s3Id] = {
            name: doc.name || doc.fileName || `Document ${index + 1}`,
            fileName: doc.fileName || doc.name,
            fileSize: doc.fileSize || doc.size || 0,
            fileType: doc.fileType || doc.content_type || 'pdf',
            url: doc.url || null,
            key: doc.key || doc.s3_key || null,
            uploaded: doc.uploaded || true,
            s3Id: doc.s3Id,
            isMerged: doc.isMerged || false
          }
        } else if (doc && doc.name) {
          // Fallback for documents without s3Id
          uploadedDocumentsPayload[`doc_${index}`] = {
            name: doc.name || doc.fileName || `Document ${index + 1}`,
            fileName: doc.fileName || doc.name,
            fileSize: doc.fileSize || doc.size || 0,
            fileType: doc.fileType || doc.content_type || 'pdf',
            url: doc.url || null,
            key: doc.key || doc.s3_key || null,
            uploaded: doc.uploaded || true,
            s3Id: doc.s3Id || null,
            isMerged: doc.isMerged || false
          }
        }
      })
    }
    // Add custom fields
    if (uploadedDocumentsPayload && typeof uploadedDocumentsPayload === 'object') {
      uploadedDocumentsPayload.customFields = categoryCustomFieldData.value.documents || {}
    }

    const proposalData = {
      companyInfo: proposalCompanyInfo,
      responses: serializedResponses,
      documents: uploadedDocumentsPayload,
      additionalDocuments: cloneDeep(documents.value, []),
      keyPersonnel: cloneDeep(keyPersonnel.value, []),
      dynamicFields: buildDynamicFieldValueMap(), // Include dynamic response fields
      customDynamicFields: serializeCustomFieldDefinitions(),
      submissionDate: new Date().toISOString(),
      completionPercentage: overallProgress.value
    }
    
    console.log('[submitResponse] Proposal data prepared:', {
      has_dynamicFields: !!proposalData.dynamicFields,
      dynamicFields_count: Object.keys(proposalData.dynamicFields || {}).length,
      dynamicFields_keys: Object.keys(proposalData.dynamicFields || {})
    })
    
    // Prepare complete response documents with ALL proposal data
    const completeResponseDocuments = {
      // Company Information
      companyInfo: {
        companyName: formData.value.companyName || '',
        legalName: formData.value.legalName || '',
        businessType: formData.value.businessType || '',
        industrySector: formData.value.industrySector || '',
        contactName: formData.value.contactName || '',
        contactTitle: formData.value.contactTitle || '',
        email: formData.value.email || '',
        phone: formData.value.phone || '',
        website: formData.value.website || '',
        taxId: formData.value.taxId || '',
        dunsNumber: formData.value.dunsNumber || '',
        incorporationDate: formData.value.incorporationDate || '',
        employeeCount: formData.value.employeeCount || '',
        annualRevenue: formData.value.annualRevenue || '',
        headquartersAddress: formData.value.headquartersAddress || '',
        headquartersCountry: formData.value.headquartersCountry || '',
        yearsInBusiness: formData.value.yearsInBusiness || '',
        companyDescription: formData.value.companyDescription || '',
        // Custom fields for company category
        customFields: categoryCustomFieldData.value.company || {}
      },
      
      // Financial Information
      financialInfo: {
        proposedValue: formData.value.proposedValue || '',
        currency: formData.value.currency || 'USD',
        pricingBreakdown: formData.value.pricingBreakdown || '',
        paymentTerms: formData.value.paymentTerms || '',
        projectDuration: formData.value.projectDuration || '',
        creditRating: formData.value.creditRating || '',
        insuranceCoverage: formData.value.insuranceCoverage || '',
        // Custom fields for financial category
        customFields: categoryCustomFieldData.value.financial || {}
      },
      
      // RFP Responses
      rfpResponses: serializedResponses,
      
      // Team Information
      teamInfo: {
        totalTeamSize: formData.value.totalTeamSize || '',
        teamStructure: formData.value.teamStructure || '',
        projectMethodology: formData.value.projectMethodology || '',
        communicationPlan: formData.value.communicationPlan || '',
        keyPersonnel: cloneDeep(keyPersonnel.value, [])
 ,
        // Custom fields for team category
        customFields: categoryCustomFieldData.value.team || {}
      },
      
      // Compliance & Certifications
      compliance: {
        iso9001: formData.value.iso9001 || false,
        iso27001: formData.value.iso27001 || false,
        iso14001: formData.value.iso14001 || false,
        soc2: formData.value.soc2 || false,
        pciDss: formData.value.pciDss || false,
        hippa: formData.value.hippa || false,
        dataSecurityMeasures: formData.value.dataSecurityMeasures || '',
        complianceStandards: formData.value.complianceStandards || '',
        professionalLiability: formData.value.professionalLiability || '',
        generalLiability: formData.value.generalLiability || '',
        references: cloneDeep(formData.value.references, []),
        // Custom fields for compliance category
        customFields: categoryCustomFieldData.value.compliance || {}
      },
      
      // Uploaded Documents - ensure it's properly formatted
      uploadedDocuments: (() => {
        // If uploadedDocumentsPayload is empty object, try to build from array
        if (Object.keys(uploadedDocumentsPayload).length === 0 && Array.isArray(uploadedDocuments.value) && uploadedDocuments.value.length > 0) {
          const docMap = {}
          uploadedDocuments.value.forEach((doc, index) => {
            if (doc && (doc.s3Id || doc.url)) {
              const key = doc.s3Id || doc.name || `doc_${index}`
              docMap[key] = {
                name: doc.name || doc.fileName || `Document ${index + 1}`,
                fileName: doc.fileName || doc.name,
                fileSize: doc.fileSize || doc.size || 0,
                fileType: doc.fileType || doc.content_type || 'pdf',
                url: doc.url || null,
                key: doc.key || doc.s3_key || null,
                uploaded: doc.uploaded !== false,
                s3Id: doc.s3Id || null,
                isMerged: doc.isMerged || false
              }
            }
          })
          docMap.customFields = categoryCustomFieldData.value.documents || {}
          return docMap
        }
        return uploadedDocumentsPayload
      })(),
      
      // Dynamic Response Fields (based on RFP type) - saved as key:value pairs
      // Key = field name (normalized from label), Value = user-entered value
      dynamicFields: (() => {
        const mappedFields = buildDynamicFieldValueMap()
        console.log('[submitResponse] Final dynamicFields mapping (key:value pairs):', mappedFields)
        console.log('[submitResponse] Dynamic fields will be saved in response_documents.dynamicFields as JSON:', JSON.stringify(mappedFields, null, 2))
        return mappedFields
      })(),
      // Field definitions for reference (metadata)
      customDynamicFields: serializeCustomFieldDefinitions(),
      
      // Metadata
      metadata: {
        submissionDate: new Date().toISOString(),
        completionPercentage: overallProgress.value,
        submissionSource: invitationData.value.isOpenRfp ? 'open' : 'invited',
        utmParameters: utmParameters.value || {}
      }
    }
    
    // Prepare submission data matching rfp_responses table structure
    // CRITICAL: Ensure invitation_id and vendor_id are always included if available
    // Convert empty strings to null for proper validation
    // Re-read values after potentially creating unmatched vendor
    const vendorIdValue = invitationData.value.vendorId && invitationData.value.vendorId !== '' && invitationData.value.vendorId !== null
      ? (typeof invitationData.value.vendorId === 'string' ? parseInt(invitationData.value.vendorId) : invitationData.value.vendorId)
      : null
    const invitationIdValue = invitationData.value.invitationId && invitationData.value.invitationId !== '' && invitationData.value.invitationId !== null
      ? invitationData.value.invitationId 
      : null
    
    console.log('🔍 Extracted IDs for submission:', {
      vendorIdRaw: invitationData.value.vendorId,
      vendorIdValue: vendorIdValue,
      invitationIdRaw: invitationData.value.invitationId,
      invitationIdValue: invitationIdValue,
      isOpenRfp: invitationData.value.isOpenRfp
    })
    
    const submissionData = {
      // Basic info
      rfpId: invitationData.value.rfpId || null,
      vendorId: vendorIdValue,
      invitationId: invitationIdValue,  // CRITICAL: Always include invitationId if available
      org: formData.value.companyName || '',
      vendorName: formData.value.contactName || '',
      contactEmail: formData.value.email || '',
      contactPhone: formData.value.phone || '',
      
      // Submission details
      submissionStatus: 'SUBMITTED',
      submissionSource: invitationData.value.isOpenRfp ? 'open' : 'invited',
      submissionDate: new Date().toISOString(),
      
      // UTM parameters for open submissions
      utmParameters: utmParameters.value,
      
      // Complete Response Documents with ALL proposal data
      responseDocuments: completeResponseDocuments,
      
// Document URLs for easy access - include full metadata
      documentUrls: (() => {
        // Handle array format for uploadedDocuments
        if (Array.isArray(uploadedDocuments.value)) {
          const urls = {}
          uploadedDocuments.value.forEach((doc, index) => {
            if (doc && doc.url) {
              const key = doc.s3Id || doc.name || `doc_${index}`
              urls[key] = {
                url: doc.url || null,
                key: doc.key || doc.s3_key || null,
                filename: doc.fileName || doc.name || 'Unknown',
                size: doc.fileSize || doc.size || 0,
                content_type: doc.fileType || doc.content_type || 'application/octet-stream',
                upload_date: doc.upload_date || new Date().toISOString(),
                document_id: doc.s3Id || null,
                s3_file_id: doc.s3Id || null,
                document_type: doc.documentType || 'rfps' // Include document type
              }
            }
          })
          return urls
        }
        // Handle object format (legacy)
        return Object.entries(uploadedDocuments.value || {}).reduce((urls, [type, doc]) => {
          if (doc) {
            urls[type] = {
              url: doc.url || null,
              key: doc.key || null,
              filename: doc.filename || doc.fileName || 'Unknown',
              size: doc.size || doc.fileSize || 0,
              content_type: doc.content_type || doc.fileType || 'application/octet-stream',
              upload_date: doc.upload_date || new Date().toISOString(),
              document_id: doc.document_id || doc.s3Id || null,
              s3_file_id: doc.s3_file_id || doc.s3Id || null,
              document_type: doc.document_type || doc.documentType || 'rfps' // Include document type
            }
          }
          return urls
        }, {})
      })(),
 
      
      // Proposal data (for backward compatibility)
      proposalData: {
        ...proposalData,
        documents: (() => {
          // Convert array to object format
          if (Array.isArray(uploadedDocuments.value) && uploadedDocuments.value.length > 0) {
            const docMap = {}
            uploadedDocuments.value.forEach((doc, index) => {
              if (doc && (doc.s3Id || doc.url || doc.name)) {
                const key = doc.s3Id || doc.name || `doc_${index}`
                docMap[key] = {
                  name: doc.name || doc.fileName || `Document ${index + 1}`,
                  fileName: doc.fileName || doc.name,
                  fileSize: doc.fileSize || doc.size || 0,
                  fileType: doc.fileType || doc.content_type || 'pdf',
                  url: doc.url || null,
                  key: doc.key || doc.s3_key || null,
                  uploaded: doc.uploaded !== false,
                  s3Id: doc.s3Id || null,
                  isMerged: doc.isMerged || false
                }
              }
            })
            return docMap
          }
          return uploadedDocuments.value || {}
        })(),
        additionalDocuments: cloneDeep(documents.value, []),
        submissionDate: new Date().toISOString(),
        completionPercentage: Math.max(0, Math.min(100, overallProgress.value || 0))
      },

      customDynamicFields: serializeCustomFieldDefinitions(),
      
      // Financial info
      proposedValue: parseFloat(formData.value.proposedValue) || 0,
      
      // Progress
      completionPercentage: Math.max(0, Math.min(100, overallProgress.value || 0)),
      
      // Request info
      submittedBy: formData.value.contactName || ''
    }
    
    console.log('[submitResponse] Complete Response Documents Structure:', {
      hasCompanyInfo: !!completeResponseDocuments.companyInfo,
      hasFinancialInfo: !!completeResponseDocuments.financialInfo,
      hasRfpResponses: !!completeResponseDocuments.rfpResponses,
      hasTeamInfo: !!completeResponseDocuments.teamInfo,
      hasCompliance: !!completeResponseDocuments.compliance,
      hasUploadedDocuments: !!completeResponseDocuments.uploadedDocuments,
      hasDynamicFields: !!completeResponseDocuments.dynamicFields,
      hasMetadata: !!completeResponseDocuments.metadata,
      companyName: completeResponseDocuments.companyInfo?.companyName,
      contactName: completeResponseDocuments.companyInfo?.contactName,
      email: completeResponseDocuments.companyInfo?.email,
      dynamicFieldsKeys: completeResponseDocuments.dynamicFields ? Object.keys(completeResponseDocuments.dynamicFields) : []
    })
    
    console.log('[submitResponse] Submission data being sent:', {
      completionPercentage: submissionData.completionPercentage,
      type: typeof submissionData.completionPercentage,
      overallProgress: overallProgress.value,
      responseDocumentsSize: JSON.stringify(submissionData.responseDocuments).length,
      responseDocumentsKeys: Object.keys(submissionData.responseDocuments || {}),
      hasResponseDocuments: !!submissionData.responseDocuments,
      hasDynamicFieldsInResponse: !!submissionData.responseDocuments?.dynamicFields
    })
    
    console.log('[submitResponse] Full responseDocuments structure:', submissionData.responseDocuments)
    
    console.log('🚀 Sending submission data:', {
      rfpId: submissionData.rfpId,
      vendorId: submissionData.vendorId,
      invitationId: submissionData.invitationId,
      vendorName: submissionData.vendorName,
      contactEmail: submissionData.contactEmail,
      completionPercentage: submissionData.completionPercentage,
      hasResponseDocuments: !!submissionData.responseDocuments,
      hasUtmParameters: !!submissionData.utmParameters,
      utmParametersKeys: submissionData.utmParameters ? Object.keys(submissionData.utmParameters) : []
    })
    
    // CRITICAL: Validate that invitation_id or vendor_id is present (or it's an open RFP)
    // For open RFPs, the backend will create unmatched vendor if needed
    const isOpenRfp = invitationData.value.isOpenRfp || 
                      (!submissionData.vendorId && !submissionData.invitationId && submissionData.rfpId)
    
    if (!submissionData.vendorId && !submissionData.invitationId && !isOpenRfp) {
      console.error('❌ CRITICAL ERROR: Neither vendorId nor invitationId is available!')
      console.error('InvitationData:', invitationData.value)
      console.error('SubmissionData:', submissionData)
      console.error('IsOpenRfp:', isOpenRfp)
      showErrorToast('Missing vendor or invitation information. Please check the URL parameters.')
      isSubmitting.value = false
      return
    }
    
    // Log final submission data before sending
    console.log('📤 Final submission data (after validation):', {
      rfpId: submissionData.rfpId,
      vendorId: submissionData.vendorId,
      invitationId: submissionData.invitationId,
      isOpenRfp: isOpenRfp,
      submissionSource: isOpenRfp ? 'open' : 'invited'
    })
    
    // Ensure submissionSource is set correctly
    submissionData.submissionSource = isOpenRfp ? 'open' : 'invited'
    
    // CRITICAL: Validate that we have actual form data before submitting
    const hasCompanyInfo = !!(
      completeResponseDocuments.companyInfo?.companyName ||
      completeResponseDocuments.companyInfo?.contactName ||
      completeResponseDocuments.companyInfo?.email
    )
    
    // Check if we have any responses (even empty ones count as long as they exist in the structure)
    const hasResponses = Object.keys(completeResponseDocuments.rfpResponses || {}).filter(
      key => key !== 'customFields'
    ).length > 0
    
    const hasDynamicFields = Object.keys(completeResponseDocuments.dynamicFields || {}).length > 0
    
    const hasFormData = hasCompanyInfo || hasResponses || hasDynamicFields
    
    if (!hasFormData) {
      console.error('❌ CRITICAL ERROR: No form data to submit!')
      console.error('Complete Response Documents:', completeResponseDocuments)
      console.error('Validation:', {
        hasCompanyInfo,
        hasResponses,
        hasDynamicFields,
        rfpResponsesKeys: Object.keys(completeResponseDocuments.rfpResponses || {}),
        rfpResponsesCount: Object.keys(completeResponseDocuments.rfpResponses || {}).length
      })
      showErrorToast('No form data found. Please fill in at least some fields before submitting.')
      submissionInProgress.value = false
      isSubmitting.value = false
      return
    }
    
    // Log the actual data being sent for debugging
    console.log('📋 Submission Data Validation:', {
      hasCompanyInfo: !!completeResponseDocuments.companyInfo,
      companyInfoKeys: completeResponseDocuments.companyInfo ? Object.keys(completeResponseDocuments.companyInfo) : [],
      hasFinancialInfo: !!completeResponseDocuments.financialInfo,
      hasRfpResponses: !!completeResponseDocuments.rfpResponses,
      rfpResponsesKeys: completeResponseDocuments.rfpResponses ? Object.keys(completeResponseDocuments.rfpResponses) : [],
      hasTeamInfo: !!completeResponseDocuments.teamInfo,
      hasCompliance: !!completeResponseDocuments.compliance,
      hasUploadedDocuments: !!completeResponseDocuments.uploadedDocuments,
      hasDynamicFields: !!completeResponseDocuments.dynamicFields,
      dynamicFieldsKeys: completeResponseDocuments.dynamicFields ? Object.keys(completeResponseDocuments.dynamicFields) : []
    })
    
    const response = await fetch(`${API_BASE_URL}/rfp-responses/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(submissionData)
    })
    
    console.log('📡 Response status:', response.status)
    console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()))
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ HTTP Error:', response.status, errorText)
      showErrorToast(`Server error (${response.status}): ${errorText}`)
      submissionInProgress.value = false
      isSubmitting.value = false
      return
    }
    
    const data = await response.json()
    console.log('📥 Response data:', data)
    
    if (data.success) {
      console.log('✅ Submission successful:', data)
      
      // Show success notification
      showSuccessToast('🎉 Proposal submitted successfully!')
      
      // Create notification service notification (requires authenticated session)
      if (hasAuthToken()) {
        try {
          await notificationService.createRFPResponseNotification('response_submitted', {
            rfp_id: invitationData.value.rfpId,
            response_id: data.response_id,
            rfp_title: invitationData.value.rfpTitle || 'RFP',
            vendor_name: formData.value.companyName
          })
        } catch (notificationError) {
          console.warn('Vendor Portal: unable to create response notification', notificationError)
        }
      }
      
      // Update submission status
      submissionStatus.value = 'SUBMITTED'
      submittedAt.value = new Date().toISOString()
      
      // Update completion status to 100%
      completionStatus.value.company = 100
      completionStatus.value.responses = 100
      completionStatus.value.documents = 100
      completionStatus.value.personnel = 100
      completionStatus.value.compliance = 100
      completionStatus.value.financial = 100
      
      // Store submission status in localStorage to persist across page reloads
      localStorage.setItem('rfp_submission_status', 'SUBMITTED')
      localStorage.setItem('rfp_submitted_at', submittedAt.value)
      localStorage.setItem('rfp_response_id', data.response_id || '')
      
      // Trigger risk analysis after successful submission
      // The backend should trigger it automatically in a background thread, but we'll also trigger it here as a backup
      // Wait a moment to let the backend's automatic trigger start first
      if (data.response_id) {
        console.log('🔍 Will trigger risk analysis for response:', data.response_id)
        // Wait 2 seconds to let backend's automatic trigger start, then trigger manually as backup
        setTimeout(async () => {
          try {
            console.log('🔍 Triggering risk analysis for response:', data.response_id)
            const riskResult = await triggerRiskAnalysis(data.response_id)
            
            if (riskResult && riskResult.success) {
              const risksCount = riskResult.result?.risks_generated || 0
              if (risksCount > 0) {
                console.log(`✅ Risk analysis completed: ${risksCount} risks generated`)
                showInfo(`Risk analysis completed: ${risksCount} risk(s) identified for this proposal.`)
              } else {
                console.log('ℹ️ Risk analysis completed but no risks were found')
                showInfo('Risk analysis completed. No risks identified for this proposal.')
              }
            } else {
              console.warn('⚠️ Risk analysis may have failed or is still processing:', riskResult?.error || 'Unknown error')
              // Don't show error to user - risk analysis runs in background and may take time
              // The backend's automatic trigger might still be processing
            }
          } catch (error) {
            console.error('❌ Error triggering risk analysis:', error)
            // Don't show error to user - risk analysis is optional and runs in background
            // The backend's automatic trigger should still work
          }
        }, 2000) // Wait 2 seconds before triggering
      }
      
      // Show success modal/confirmation
      showSubmissionSuccessModal(data)
      
      console.log('📊 Submission data saved to localStorage')
    } else {
      console.error('❌ Submission failed:', data)
      showErrorToast(data.error || 'Failed to submit proposal. Please try again.')
      
      // Create error notification
      if (hasAuthToken()) {
        try {
          await notificationService.createRFPErrorNotification('submit_proposal', data.error, {
            title: 'Proposal Submission Failed',
            rfp_id: invitationData.value.rfpId,
            vendor_name: formData.value.companyName
          })
        } catch (notificationError) {
          console.warn('Vendor Portal: unable to create failure notification', notificationError)
        }
      }
    }
  } catch (error) {
    console.error('Error submitting proposal:', error)
    showErrorToast('Network error. Please check your connection and try again.')
    
    // Create error notification
    if (hasAuthToken()) {
      try {
        await notificationService.createRFPErrorNotification('submit_proposal', error.message, {
          title: 'Network Error',
          message: 'Network error. Please check your connection and try again.',
          rfp_id: invitationData.value.rfpId
        })
      } catch (notificationError) {
        console.warn('Vendor Portal: unable to create network error notification', notificationError)
      }
    }
  } finally {
    // CRITICAL: Always release submission lock
    submissionInProgress.value = false
    isSubmitting.value = false
  }
}

// Utility functions
const formatLastSaved = (dateString) => {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
  
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  
  const diffDays = Math.floor(diffHours / 24)
  return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// AUTO-SAVE DISABLED: Removed debounceAutoSave to prevent creating empty responses
// Users must explicitly click save button or submit to save data
// This prevents multiple empty responses from being created

// Watch for changes to trigger URL updates (auto-save disabled to prevent empty responses)
watch([formData, responses, documents, keyPersonnel, customDynamicFields], () => {
  updateCompletionStatus()
  // AUTO-SAVE DISABLED: Removed debounceAutoSave() to prevent creating empty responses
  // Auto-save will only happen when user explicitly clicks save or submits
  updateUrl() // Update URL as form is filled
}, { deep: true })

// Global error handler for Vue
const handleVueError = (error, instance, info) => {
  console.error('Vue Error:', error)
  console.error('Component:', instance)
  console.error('Info:', info)
  
  // Try to recover by re-initializing reactive data
  ensureReactiveData()
}

// Initialize component
onMounted(async () => {
  if (!props.previewPayload && hasAuthToken()) {
    try {
      await loggingService.logPageView('RFP', 'Vendor Portal')
    } catch (error) {
      console.warn('Vendor Portal: failed to log page view', error)
    }
  }
  try {
    if (!props.previewPayload) {
      document.body.classList.add('standalone-route')
      document.documentElement.classList.add('standalone-route')
      document.body.classList.add('vendor-portal')
      document.documentElement.classList.add('vendor-portal')
      appliedStandaloneClasses.value = true
    }
    
    // Ensure all reactive data is properly initialized first
    ensureReactiveData()
    
    // Parse query parameters first to get RFP and vendor info
    parseQueryParameters()
    
    if (previewMode.value) {
      if (props.previewPayload) {
        isLoading.value = true
        await applyPreviewPayload(props.previewPayload)
        isLoading.value = false
      } else {
        await loadPreviewData()
      }
      updateCompletionStatus()
      return
    }
    
    // Only check for existing submissions if we have valid RFP and vendor IDs
    if (invitationData.value.rfpId && (invitationData.value.vendorId || invitationData.value.invitationId)) {
      // Check backend for submission status first (more reliable than localStorage)
      await checkSubmissionStatusFromBackend()
      
      // Only check localStorage if backend check didn't find a submission
      if (submissionStatus.value !== 'SUBMITTED') {
        const savedSubmissionStatus = localStorage.getItem('rfp_submission_status')
        const savedSubmittedAt = localStorage.getItem('rfp_submitted_at')
        const savedResponseId = localStorage.getItem('rfp_response_id')
        
        // Only restore from localStorage if we have a valid response ID and it matches current session
        if (savedSubmissionStatus === 'SUBMITTED' && savedResponseId) {
          // Double-check that this response ID is valid for current RFP/vendor
          if (savedResponseId && savedResponseId !== '') {
            submissionStatus.value = 'SUBMITTED'
            submittedAt.value = savedSubmittedAt || new Date().toISOString()
            console.log('📋 Restored submission status from localStorage:', {
              status: savedSubmissionStatus,
              submittedAt: savedSubmittedAt,
              responseId: savedResponseId
            })
          } else {
            // Clear invalid localStorage data
            localStorage.removeItem('rfp_submission_status')
            localStorage.removeItem('rfp_submitted_at')
            localStorage.removeItem('rfp_response_id')
            console.log('🧹 Cleared invalid localStorage submission data')
          }
        }
      }
    } else {
      console.log('⚠️ No valid RFP ID or vendor information found, skipping submission status check')
      // Clear any stale localStorage data when no valid IDs are present
      localStorage.removeItem('rfp_submission_status')
      localStorage.removeItem('rfp_submitted_at')
      localStorage.removeItem('rfp_response_id')
    }
    
    // Fetch RFP details first (this also loads draft and response data)
    await fetchInvitationDetails()
    
    // Fetch evaluation criteria (needed for responses)
    // Wait a bit to ensure rfpInfo is populated
    await new Promise(resolve => setTimeout(resolve, 100))
    await fetchEvaluationCriteria()
    
    // If criteria still not loaded, try again after a short delay
    if (!evaluationCriteria.value || evaluationCriteria.value.length === 0) {
      console.log('⚠️ Criteria not loaded on first attempt, retrying...')
      await new Promise(resolve => setTimeout(resolve, 500))
      await fetchEvaluationCriteria()
    }
    
    // Load existing documents
    await loadExistingDocuments()

    // Always try to resolve RFP documents after fetching invitation details
    // This ensures documents are ready when user switches to Documents tab
    if (rfpDocuments.value) {
      console.log('🔄 Initial RFP documents found, resolving tabs...')
      await resolveRfpDocumentTabs()
    } else {
      console.log('⚠️ No RFP documents found in initial load')
    }
    
    // Update completion status after all data is loaded
    // Use nextTick to ensure all reactive updates are complete
    await new Promise(resolve => setTimeout(resolve, 100))
    updateCompletionStatus()
    
    console.log('📊 Final form state after loading:', {
      companyFields: Object.keys(formData.value).filter(k => formData.value[k]),
      responsesCount: Object.keys(responses.value).length,
      keyPersonnelCount: keyPersonnel.value.length,
      documentsCount: Array.isArray(uploadedDocuments.value) ? uploadedDocuments.value.length : 0
    })
    
    // Debug submission status for troubleshooting
    debugSubmissionStatus()
    debugInvitationData()
    
    console.log('✅ VendorPortal component initialized successfully')
  } catch (error) {
    console.error('❌ Error initializing VendorPortal:', error)
    // Try to recover
    ensureReactiveData()
  }
})

// Success modal state
const showSuccessModal = ref(false)
const submissionDetails = ref({})

// Show submission success modal
const showSubmissionSuccessModal = (data) => {
  console.log('🎉 [DEBUG] showSubmissionSuccessModal called with:', data)
  console.log('🎉 [DEBUG] Current submissionStatus:', submissionStatus.value)
  
  // Show modal if we have successful submission data
  if (data && data.success && data.response_id) {
    submissionDetails.value = {
      responseId: data.response_id,
      submittedAt: data.submitted_at || data.submission_date || new Date().toISOString(),
      rfpTitle: data.rfp_title || rfpInfo.value.rfpTitle,
      rfpNumber: data.rfp_number || rfpInfo.value.rfpNumber,
      vendorName: data.vendor_name || formData.value.contactName,
      contactEmail: data.contact_email || formData.value.email,
      proposedValue: formData.value.proposedValue,
      currency: formData.value.currency || 'USD'
    }
    showSuccessModal.value = true
    console.log('🎉 [DEBUG] Success modal should now be visible')
  } else {
    console.log('🎉 [DEBUG] Modal not shown - missing data:', {
      hasData: !!data,
      hasSuccess: data?.success,
      hasResponseId: !!data?.response_id
    })
  }
}

// Close success modal
const closeSuccessModal = () => {
  showSuccessModal.value = false
}

// Download submission confirmation as PDF
const downloadSubmissionConfirmation = () => {
  const confirmationData = {
    rfpNumber: submissionDetails.value.rfpNumber,
    rfpTitle: submissionDetails.value.rfpTitle,
    responseId: submissionDetails.value.responseId,
    vendorName: submissionDetails.value.vendorName,
    contactEmail: submissionDetails.value.contactEmail,
    submittedAt: submissionDetails.value.submittedAt,
    submittedBy: formData.value.contactName,
    companyName: formData.value.companyName,
    proposedValue: formData.value.proposedValue,
    currency: formData.value.currency
  }
  
  // Generate PDF content
  const pdfContent = generatePDFContent(confirmationData)
  
  // Create PDF blob
  const pdfBlob = new Blob([pdfContent], { type: 'application/pdf' })
  const url = URL.createObjectURL(pdfBlob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = `proposal-confirmation-${submissionDetails.value.responseId}.pdf`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  showSuccessToast('PDF confirmation downloaded successfully!')
}

// Generate PDF content using HTML to PDF conversion
const generatePDFContent = (data) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  // Create HTML content for the PDF
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>Proposal Submission Confirmation</title>
      <style>
        body {
          font-family: Arial, sans-serif;
          margin: 40px;
          line-height: 1.6;
          color: #333;
        }
        .header {
          text-align: center;
          border-bottom: 3px solid #2563eb;
          padding-bottom: 20px;
          margin-bottom: 30px;
        }
        .header h1 {
          color: #2563eb;
          margin: 0;
          font-size: 24px;
        }
        .section {
          margin-bottom: 25px;
        }
        .section h2 {
          color: #1f2937;
          border-bottom: 1px solid #e5e7eb;
          padding-bottom: 5px;
          margin-bottom: 15px;
        }
        .info-row {
          display: flex;
          margin-bottom: 10px;
        }
        .label {
          font-weight: bold;
          width: 150px;
          color: #374151;
        }
        .value {
          flex: 1;
          color: #6b7280;
        }
        .footer {
          margin-top: 40px;
          padding-top: 20px;
          border-top: 1px solid #e5e7eb;
          text-align: center;
          color: #6b7280;
          font-size: 12px;
        }
        .confirmation-message {
          background-color: #f0f9ff;
          border: 1px solid #0ea5e9;
          border-radius: 8px;
          padding: 20px;
          margin: 20px 0;
          text-align: center;
        }
        .confirmation-message h3 {
          color: #0c4a6e;
          margin: 0 0 10px 0;
        }
        .confirmation-message p {
          color: #075985;
          margin: 0;
        }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>PROPOSAL SUBMISSION CONFIRMATION</h1>
        <p>RFP Response System</p>
      </div>
      
      <div class="section">
        <h2>RFP Information</h2>
        <div class="info-row">
          <div class="label">RFP Number:</div>
          <div class="value">${data.rfpNumber}</div>
        </div>
        <div class="info-row">
          <div class="label">RFP Title:</div>
          <div class="value">${data.rfpTitle}</div>
        </div>
        <div class="info-row">
          <div class="label">Response ID:</div>
          <div class="value">${data.responseId}</div>
        </div>
      </div>
      
      <div class="section">
        <h2>Vendor Information</h2>
        <div class="info-row">
          <div class="label">Company Name:</div>
          <div class="value">${data.companyName}</div>
        </div>
        <div class="info-row">
          <div class="label">Contact Name:</div>
          <div class="value">${data.vendorName}</div>
        </div>
        <div class="info-row">
          <div class="label">Email Address:</div>
          <div class="value">${data.contactEmail}</div>
        </div>
      </div>
      
      <div class="section">
        <h2>Proposal Details</h2>
        <div class="info-row">
          <div class="label">Proposed Value:</div>
          <div class="value">${data.currency} ${data.proposedValue?.toLocaleString() || 'N/A'}</div>
        </div>
      </div>
      
      <div class="section">
        <h2>Submission Information</h2>
        <div class="info-row">
          <div class="label">Submitted At:</div>
          <div class="value">${formatDate(data.submittedAt)}</div>
        </div>
        <div class="info-row">
          <div class="label">Submitted By:</div>
          <div class="value">${data.submittedBy}</div>
        </div>
      </div>
      
      <div class="confirmation-message">
        <h3>✅ Submission Confirmed</h3>
        <p>Your proposal has been successfully submitted and received by our system. You will be notified of the evaluation results in due course.</p>
      </div>
      
      <div class="footer">
        <p>This is an automated confirmation document. Please retain this for your records.</p>
        <p>Generated on ${new Date().toLocaleDateString('en-US', { 
          year: 'numeric', 
          month: 'long', 
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        })}</p>
      </div>
    </body>
    </html>
  `
  
  // For now, we'll create a simple text-based PDF structure
  // In a production environment, you would use a proper PDF library
  // This creates a basic PDF that should be readable by most PDF viewers
  const pdfText = `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 1200
>>
stream
BT
/F1 14 Tf
50 750 Td
(PROPOSAL SUBMISSION CONFIRMATION) Tj
0 -25 Td
/F1 10 Tf
() Tj
0 -20 Td
(RFP Number: ${data.rfpNumber}) Tj
0 -20 Td
(RFP Title: ${data.rfpTitle}) Tj
0 -20 Td
(Response ID: ${data.responseId}) Tj
0 -20 Td
() Tj
0 -20 Td
(Vendor Information:) Tj
0 -20 Td
(Company Name: ${data.companyName}) Tj
0 -20 Td
(Contact Name: ${data.vendorName}) Tj
0 -20 Td
(Email: ${data.contactEmail}) Tj
0 -20 Td
() Tj
0 -20 Td
(Proposal Details:) Tj
0 -20 Td
(Proposed Value: ${data.currency} ${data.proposedValue}) Tj
0 -20 Td
() Tj
0 -20 Td
(Submission Information:) Tj
0 -20 Td
(Submitted At: ${formatDate(data.submittedAt)}) Tj
0 -20 Td
(Submitted By: ${data.submittedBy}) Tj
0 -20 Td
() Tj
0 -20 Td
(This document confirms that your proposal has been) Tj
0 -20 Td
(successfully submitted and received by our system.) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000830 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
1200
%%EOF`
  
  return pdfText
}

// Debug function to check submission status
const debugSubmissionStatus = () => {
  console.log('🔍 Debug - Current submission status:', {
    submissionStatus: submissionStatus.value,
    submittedAt: submittedAt.value,
    isSubmitting: isSubmitting.value,
    showSuccessModal: showSuccessModal.value,
    localStorage: {
      status: localStorage.getItem('rfp_submission_status'),
      submittedAt: localStorage.getItem('rfp_submitted_at'),
      responseId: localStorage.getItem('rfp_response_id')
    },
    invitationData: {
      rfpId: invitationData.value.rfpId,
      vendorId: invitationData.value.vendorId,
      invitationId: invitationData.value.invitationId
    }
  })
}

// Debug function to check invitation data
const debugInvitationData = () => {
  console.log('🔍 Debug - Invitation data:', {
    currentUrl: window.location.href,
    searchParams: window.location.search,
    pathname: window.location.pathname,
    invitationData: invitationData.value,
    hasRfpId: !!invitationData.value.rfpId,
    hasVendorId: !!invitationData.value.vendorId,
    hasInvitationId: !!invitationData.value.invitationId,
    canUpload: !!(invitationData.value.rfpId && (invitationData.value.vendorId || invitationData.value.invitationId))
  })
}

// Clean up when component unmounts
onUnmounted(() => {
  if (!appliedStandaloneClasses.value) {
    return
  }
  document.body.classList.remove('standalone-route')
  document.documentElement.classList.remove('standalone-route')
  document.body.classList.remove('vendor-portal')
  document.documentElement.classList.remove('vendor-portal')
})
</script>

<style scoped>
/* Custom styles to match the exact design from the TSX file */
.bg-gray-50 {
  background-color: #f9fafb;
}

.bg-white {
  background-color: #ffffff;
}

.border-gray-200 {
  border-color: #e5e7eb;
}

.border-gray-300 {
  border-color: #d1d5db;
}

.text-gray-900 {
  color: #111827;
}

.text-gray-700 {
  color: #374151;
}

.text-gray-600 {
  color: #4b5563;
}

.text-gray-500 {
  color: #6b7280;
}

.bg-green-100 {
  background-color: #dcfce7;
}

.text-green-800 {
  color: #166534;
}

.border-green-200 {
  border-color: #bbf7d0;
}

.bg-purple-100 {
  background-color: #f3e8ff;
}

.text-purple-800 {
  color: #6b21a8;
}

.bg-purple-600 {
  background-color: #9333ea;
}

.bg-purple-700 {
  background-color: #7c3aed;
}

.text-green-600 {
  color: #16a34a;
}

.text-orange-600 {
  color: #ea580c;
}

.text-yellow-600 {
  color: #ca8a04;
}

.text-red-500 {
  color: #ef4444;
}

/* Progress bar animation */
.transition-all {
  transition: all 0.3s ease;
}

/* Focus states */
.focus\:ring-blue-500:focus {
  --tw-ring-color: #3b82f6;
}

.focus\:border-blue-500:focus {
  border-color: #3b82f6;
}

/* Hover states */
.hover\:bg-gray-50:hover {
  background-color: #f9fafb;
}

.hover\:from-blue-700:hover {
  --tw-gradient-from: #1d4ed8;
}

.hover\:to-blue-800:hover {
  --tw-gradient-to: #1e40af;
}

/* Disabled states */
.disabled\:opacity-50:disabled {
  opacity: 0.5;
}

.disabled\:cursor-not-allowed:disabled {
  cursor: not-allowed;
}

/* Gradient backgrounds */
.bg-gradient-to-r {
  background-image: linear-gradient(to right, var(--tw-gradient-stops));
}

.from-blue-600 {
  --tw-gradient-from: #2563eb;
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(37, 99, 235, 0));
}

.to-blue-700 {
  --tw-gradient-to: #1d4ed8;
}

.from-purple-600 {
  --tw-gradient-from: #9333ea;
  --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(147, 51, 234, 0));
}

.to-purple-700 {
  --tw-gradient-to: #7c3aed;
}

/* Custom spacing and layout */
.space-y-6 > * + * {
  margin-top: 1.5rem;
}

.space-y-4 > * + * {
  margin-top: 1rem;
}

.space-y-3 > * + * {
  margin-top: 0.75rem;
}

.space-y-2 > * + * {
  margin-top: 0.5rem;
}

.gap-4 {
  gap: 1rem;
}

.gap-3 {
  gap: 0.75rem;
}

.gap-2 {
  gap: 0.5rem;
}

.gap-1 {
  gap: 0.25rem;
}

/* Grid layouts */
.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.grid-cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.md\:grid-cols-2 {
  @media (min-width: 768px) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

.md\:grid-cols-4 {
  @media (min-width: 768px) {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

/* Flexbox utilities */
.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.justify-center {
  justify-content: center;
}

.justify-between {
  justify-content: space-between;
}

.justify-start {
  justify-content: flex-start;
}

/* Text utilities */
.text-center {
  text-align: center;
}

.font-bold {
  font-weight: 700;
}

.font-semibold {
  font-weight: 600;
}

.font-medium {
  font-weight: 500;
}

.text-sm {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.text-xs {
  font-size: 0.75rem;
  line-height: 1rem;
}

.text-2xl {
  font-size: 1.5rem;
  line-height: 2rem;
}

.text-3xl {
  font-size: 1.875rem;
  line-height: 2.25rem;
}

.text-lg {
  font-size: 1.125rem;
  line-height: 1.75rem;
}

/* Border radius */
.rounded-lg {
  border-radius: 0.5rem;
}

.rounded-md {
  border-radius: 0.375rem;
}

.rounded-full {
  border-radius: 9999px;
}

/* Padding and margins */
.p-6 {
  padding: 1.5rem;
}

.p-4 {
  padding: 1rem;
}

.p-3 {
  padding: 0.75rem;
}

.p-2 {
  padding: 0.5rem;
}

.px-3 {
  padding-left: 0.75rem;
  padding-right: 0.75rem;
}

.py-1 {
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
}

.py-2 {
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
}

.px-4 {
  padding-left: 1rem;
  padding-right: 1rem;
}

.py-4 {
  padding-top: 1rem;
  padding-bottom: 1rem;
}

.px-6 {
  padding-left: 1.5rem;
  padding-right: 1.5rem;
}

.py-6 {
  padding-top: 1.5rem;
  padding-bottom: 1.5rem;
}

/* Margins */
.mx-auto {
  margin-left: auto;
  margin-right: auto;
}

.mb-2 {
  margin-bottom: 0.5rem;
}

.mb-4 {
  margin-bottom: 1rem;
}

.mt-1 {
  margin-top: 0.25rem;
}

.mt-2 {
  margin-top: 0.5rem;
}

.ml-1 {
  margin-left: 0.25rem;
}

.ml-2 {
  margin-left: 0.5rem;
}

.ml-auto {
  margin-left: auto;
}

.mr-2 {
  margin-right: 0.5rem;
}

/* Width and height */
.w-full {
  width: 100%;
}

.h-2 {
  height: 0.5rem;
}

.h-3 {
  height: 0.75rem;
}

.h-4 {
  height: 1rem;
}

.h-5 {
  height: 1.25rem;
}

.h-8 {
  height: 2rem;
}

.w-3 {
  width: 0.75rem;
}

.w-4 {
  width: 1rem;
}

.w-5 {
  width: 1.25rem;
}

.w-8 {
  width: 2rem;
}

/* Max width */
.max-w-4xl {
  max-width: 56rem;
}

/* Border styles */
.border {
  border-width: 1px;
}

.border-b {
  border-bottom-width: 1px;
}

.border-2 {
  border-width: 2px;
}

.border-dashed {
  border-style: dashed;
}

/* Shadow */
.shadow-sm {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

/* Display utilities */
.inline-flex {
  display: inline-flex;
}

/* Position utilities */
.relative {
  position: relative;
}

/* Z-index */
.z-10 {
  z-index: 10;
}

/* Responsive utilities */
@media (min-width: 640px) {
  .sm\:flex-row {
    flex-direction: row;
  }
}

@media (min-width: 768px) {
  .md\:grid-cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  
  .md\:grid-cols-4 {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

/* Custom focus and hover states */
.focus\:outline-none:focus {
  outline: 2px solid transparent;
  outline-offset: 2px;
}

.focus\:ring-2:focus {
  box-shadow: 0 0 0 2px var(--tw-ring-color);
}

.focus\:ring-offset-2:focus {
  box-shadow: 0 0 0 2px #ffffff, 0 0 0 4px var(--tw-ring-color);
}

.focus\:ring-blue-500:focus {
  --tw-ring-color: #3b82f6;
}

.focus\:border-blue-500:focus {
  border-color: #3b82f6;
}

/* Button states */
.hover\:bg-gray-50:hover {
  background-color: #f9fafb;
}

.hover\:bg-gray-200:hover {
  background-color: #e5e7eb;
}

.hover\:from-blue-700:hover {
  --tw-gradient-from: #1d4ed8;
}

.hover\:to-blue-800:hover {
  --tw-gradient-to: #1e40af;
}

/* Disabled states */
.disabled\:opacity-50:disabled {
  opacity: 0.5;
}

.disabled\:cursor-not-allowed:disabled {
  cursor: not-allowed;
}

/* Textarea specific styles */
.resize-none {
  resize: none;
}

.min-h-24 {
  min-height: 6rem;
}

.min-h-32 {
  min-height: 8rem;
}

/* Icon sizing */
.lucide {
  width: 1em;
  height: 1em;
}

/* Tab styles */
.tab-content {
  min-height: 400px;
}

.tab-content > div {
  animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Tab navigation hover effects */
.tab-navigation button {
  transition: all 0.2s ease;
}

.tab-navigation button:hover {
  transform: translateY(-1px);
}

/* Smooth scroll behavior */
html {
  scroll-behavior: smooth;
}

/* Custom scrollbar for tab overflow */
.overflow-x-auto::-webkit-scrollbar {
  height: 4px;
}

.overflow-x-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.overflow-x-auto::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.overflow-x-auto::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Sliding Panel Animations */
.fixed.inset-0 {
  animation: backdropFadeIn 0.3s ease-out;
}

@keyframes backdropFadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.absolute.right-0 {
  animation: slideInRight 0.3s ease-out;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

/* Floating Action Button */
.fixed.right-6 button {
  transition: all 0.3s ease;
}

.fixed.right-6 button:hover {
  transform: scale(1.1);
  box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3);
}

/* Full-width form improvements */
.max-w-7xl {
  max-width: 80rem;
}

@media (min-width: 1536px) {
  .max-w-7xl {
    max-width: 90rem;
  }
}

/* Improve form field widths for better readability */
.bg-white.border.border-gray-200.rounded-lg {
  transition: all 0.2s ease;
}

.bg-white.border.border-gray-200.rounded-lg:hover {
  border-color: #cbd5e1;
}

/* Panel shadow enhancement */
.shadow-2xl {
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

/* Z-index hierarchy */
.z-40 {
  z-index: 40;
}

.z-50 {
  z-index: 50;
}

/* Enhanced grid for full-width form */
@media (min-width: 1024px) {
  .grid.grid-cols-1.md\:grid-cols-2 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (min-width: 1280px) {
  .grid.grid-cols-1.md\:grid-cols-2 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

/* Better spacing for full-width layout */
.vendor-portal-standalone {
  min-height: 100vh;
  background-color: #f9fafb;
}

/* Pulse animation for floating button */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}

.fixed.right-6 button {
  animation: pulse 2s ease-in-out infinite;
}

.fixed.right-6 button:hover {
  animation: none;
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
</style>

