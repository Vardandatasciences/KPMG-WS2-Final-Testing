<template>
  <div class="space-y-8">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div class="space-y-2">
          <h1 class="text-3xl font-bold text-gray-900">Phase 3: Vendor Selection</h1>
          <p class="text-gray-600">
            Select qualified vendors using multiple methods: existing vendors, manual creation, or bulk upload.
          </p>
          <!-- RFP Context -->
          <div v-if="selectedRFP" class="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-sm font-medium text-blue-900">Processing RFP:</span>
              <span class="font-mono text-sm text-blue-700">{{ selectedRFP.rfp_number }}</span>
            </div>
            <p class="text-sm text-blue-800">{{ selectedRFP.rfp_title }}</p>
            <p class="text-xs text-blue-600 mt-1">Budget: {{ formatCurrency(selectedRFP.estimated_value) }} • Type: {{ selectedRFP.rfp_type }}</p>
          </div>
        </div>
        <div class="flex-shrink-0">
          <rfp-badge variant="outline" class="status-badge active">
            Phase 3 of 10
          </rfp-badge>
        </div>
      </div>

      <!-- Selection Method Tabs -->
      <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div class="border-b border-gray-200">
          <nav class="flex space-x-8 px-6" aria-label="Tabs">
            <button
              v-for="tab in (tabs || [])"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              <component :is="tab.icon" class="h-4 w-4 inline mr-2" />
              {{ tab.name }}
              <span v-if="tab.count !== undefined" class="ml-2 bg-gray-100 text-gray-600 py-0.5 px-2 rounded-full text-xs">
                {{ tab.count }}
              </span>
            </button>
          </nav>
        </div>


        <!-- Tab Content -->
        <div class="p-6">
          <!-- Existing Vendors Tab -->
          <div v-if="activeTab === 'existing'" class="space-y-6">
            <!-- Search and Filters -->
            <div class="space-y-4">
              <!-- Enhanced Search Section -->
              <div class="bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-xl p-6 shadow-sm">
                <div class="space-y-4">
                  <!-- Search Bar -->
                  <div class="relative">
                    <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                      <Search class="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      v-model="searchTerm"
                      type="text"
                      placeholder="Search approved vendors by name, capabilities, or certifications..."
                      class="w-full h-12 pl-12 pr-4 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-200 text-gray-900 placeholder-gray-400 shadow-sm"
                    />
                  </div>
                  
                  <!-- Filter Pills and View Toggle -->
                  <div class="flex flex-wrap items-center justify-between gap-2">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="text-sm font-medium text-gray-700 mr-2">Filter by:</span>
                    <button
                      @click="activeFilter = 'all'"
                      :class="[
                        'inline-flex items-center px-4 py-2 rounded-full text-sm font-medium transition-all duration-200',
                        activeFilter === 'all'
                          ? 'bg-blue-600 text-white shadow-md'
                          : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                      ]"
                    >
                      All Approved
                    </button>
                    <button
                      @click="activeFilter = 'high-match'"
                      :class="[
                        'inline-flex items-center px-4 py-2 rounded-full text-sm font-medium transition-all duration-200',
                        activeFilter === 'high-match'
                          ? 'bg-green-600 text-white shadow-md'
                          : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                      ]"
                    >
                      <Star class="h-3 w-3 mr-1.5" />
                      High Match (90%+)
                    </button>
                    <button
                      @click="activeFilter = 'certified'"
                      :class="[
                        'inline-flex items-center px-4 py-2 rounded-full text-sm font-medium transition-all duration-200',
                        activeFilter === 'certified'
                          ? 'bg-purple-600 text-white shadow-md'
                          : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                      ]"
                    >
                      <Award class="h-3 w-3 mr-1.5" />
                      Highly Certified
                    </button>
                    </div>
                    
                    <!-- View Toggle -->
                    <div class="flex items-center gap-1 bg-white border border-gray-300 rounded-lg p-1">
                      <button
                        @click="viewMode = 'list'"
                        :class="[
                          'inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-all duration-200',
                          viewMode === 'list'
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                        ]"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
                        List
                      </button>
                      <button
                        @click="viewMode = 'grid'"
                        :class="[
                          'inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-all duration-200',
                          viewMode === 'grid'
                            ? 'bg-blue-600 text-white shadow-sm'
                            : 'text-gray-600 hover:text-gray-900'
                        ]"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
                        Grid
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Bulk Actions -->
              <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5 shadow-sm">
                <div class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                  <!-- Action Buttons Group -->
                  <div class="flex flex-wrap items-center gap-2.5">
                    <button
                      @click="handleBulkSelect"
                      class="inline-flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-blue-50 text-blue-700 hover:text-blue-800 border border-blue-300 hover:border-blue-400 rounded-lg font-medium text-sm transition-all duration-200 shadow-sm hover:shadow-md"
                    >
                      <CheckCircle2 class="h-4 w-4" />
                      {{ selectedExistingVendors.length === existingVendors.length ? 'Deselect All' : 'Select All' }}
                    </button>
                    
                    <button 
                      @click="showBulkUpload = !showBulkUpload"
                      class="inline-flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-green-50 text-green-700 hover:text-green-800 border border-green-300 hover:border-green-400 rounded-lg font-medium text-sm transition-all duration-200 shadow-sm hover:shadow-md"
                    >
                      <Upload class="h-4 w-4" />
                      Bulk Upload CSV
                    </button>
                    
                    <button 
                      @click="handleExportList"
                      class="inline-flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-purple-50 text-purple-700 hover:text-purple-800 border border-purple-300 hover:border-purple-400 rounded-lg font-medium text-sm transition-all duration-200 shadow-sm hover:shadow-md"
                    >
                      <FileSpreadsheet class="h-4 w-4" />
                      Export List
                    </button>
                    
                    <button 
                      @click="downloadVendorTemplate"
                      class="inline-flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white border border-blue-600 hover:border-blue-700 rounded-lg font-medium text-sm transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
                    >
                      <Download class="h-4 w-4" />
                      Download Template
                    </button>
                  </div>
                  
                  <!-- Selection Counter -->
                  <div class="flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 rounded-lg shadow-sm">
                    <div class="flex items-center gap-2">
                      <div class="h-2 w-2 rounded-full bg-blue-500 animate-pulse"></div>
                      <span class="text-sm font-semibold text-gray-900">
                        {{ selectedExistingVendors?.length || 0 }}
                      </span>
                      <span class="text-sm text-gray-500">of</span>
                      <span class="text-sm font-semibold text-gray-700">
                        {{ filteredExistingVendors?.length || 0 }}
                      </span>
                      <span class="text-sm text-gray-500">selected</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Bulk Upload Area -->
            <div v-if="showBulkUpload" class="space-y-4 p-6 bg-gray-50 rounded-lg border border-gray-200">
              <div class="flex items-center justify-between">
                <h4 class="text-lg font-semibold text-gray-900">Bulk Upload Vendors</h4>
                <rfp-button variant="outline" size="sm" @click="showBulkUpload = false">
                  Close
                </rfp-button>
              </div>
              
              <!-- Upload Instructions -->
              <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h5 class="font-medium text-blue-900 mb-2">Upload Instructions</h5>
                <ul class="text-sm text-blue-800 space-y-1">
                  <li>• Upload a CSV or Excel file (.csv, .xlsx, .xls) with vendor information</li>
                  <li>• Required columns: company_name, vendor_name, vendor_email, vendor_phone</li>
                  <li>• Optional columns: website, industry_sector, description</li>
                  <li>• Download the template below for the correct format</li>
                </ul>
              </div>

              <!-- File Upload -->
              <div 
                class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center transition-colors"
                :class="{ 'border-blue-400 bg-blue-50': isDragOver }"
                @click="openFileDialog"
                @dragover.prevent="isDragOver = true"
                @dragleave.prevent="isDragOver = false"
                @drop.prevent="handleFileDrop"
              >
                <input
                  ref="fileInput"
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  @change="handleFileSelect"
                  class="hidden"
                />
                <div v-if="!selectedFile" class="cursor-pointer hover:bg-gray-50 transition-colors rounded-lg p-4">
                  <Upload class="h-12 w-12 mx-auto mb-4" :class="isDragOver ? 'text-blue-500' : 'text-gray-400'" />
                  <p class="text-lg font-medium text-gray-900 mb-2">Upload vendor file</p>
                  <p class="text-gray-600" v-if="!isDragOver">Click to browse or drag and drop CSV/Excel files (.csv, .xlsx, .xls)</p>
                  <p class="text-blue-600 font-medium" v-else>Drop your file here</p>
                </div>
                
                <div v-else class="space-y-4">
                  <div class="flex items-center justify-center space-x-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <CheckCircle class="h-8 w-8 text-green-500" />
                    <div class="text-left">
                      <p class="font-medium text-green-900">{{ selectedFile.name }}</p>
                      <p class="text-sm text-green-700">{{ formatFileSize(selectedFile.size) }}</p>
                    </div>
                    <button
                      @click.stop="selectedFile = null; uploadResults.show = false"
                      class="text-red-500 hover:text-red-700 transition-colors"
                    >
                      <X class="h-5 w-5" />
                    </button>
                  </div>
                  
                  <rfp-button 
                    @click="handleBulkUpload" 
                    :disabled="isUploading"
                    class="w-full"
                  >
                    <span v-if="isUploading">Uploading...</span>
                    <span v-else>Upload & Process File</span>
                  </rfp-button>
                </div>
              </div>

              <!-- Upload Results -->
              <div v-if="uploadResults.show" class="mt-4 p-4 rounded-lg border" 
                   :class="uploadResults.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'">
                <div class="flex items-start space-x-3">
                  <component :is="uploadResults.success ? CheckCircle : AlertCircle" 
                             :class="uploadResults.success ? 'text-green-500' : 'text-red-500'"
                             class="h-5 w-5 mt-0.5" />
                  <div>
                    <h5 :class="uploadResults.success ? 'text-green-900' : 'text-red-900'" class="font-medium">
                      {{ uploadResults.success ? 'Upload Successful' : 'Upload Failed' }}
                    </h5>
                    <p :class="uploadResults.success ? 'text-green-700' : 'text-red-700'" class="text-sm mt-1">
                      {{ uploadResults.message }}
                    </p>
                    <div v-if="uploadResults.results" class="mt-2 text-sm">
                      <p :class="uploadResults.success ? 'text-green-700' : 'text-red-700'">
                        Success: {{ uploadResults.results.success }} | Failed: {{ uploadResults.results.failed }}
                      </p>
                      <div v-if="uploadResults.results.errors && uploadResults.results.errors.length > 0" class="mt-2">
                        <p class="font-medium text-red-800">Errors:</p>
                        <ul class="list-disc list-inside text-red-700 space-y-1">
                          <li v-for="error in uploadResults.results.errors.slice(0, 5)" :key="error">{{ error }}</li>
                          <li v-if="uploadResults.results.errors.length > 5" class="text-red-600">
                            ... and {{ uploadResults.results.errors.length - 5 }} more errors
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Existing Vendors List View -->
            <div v-if="viewMode === 'list'" class="space-y-3">
              <div 
                v-for="vendor in filteredExistingVendors" 
                :key="vendor.vendor_id"
                :class="[
                  'group relative bg-white border-2 rounded-xl shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden',
                  selectedExistingVendors.includes(vendor.vendor_id) 
                    ? 'border-blue-500 ring-2 ring-blue-200' 
                    : 'border-gray-200 hover:border-blue-300'
                ]"
              >
                <!-- Compact List Item -->
                <div class="p-4">
                  <div class="flex items-center gap-4">
                    <!-- Checkbox -->
                    <Checkbox
                      :modelValue="selectedExistingVendors.includes(vendor.vendor_id)"
                      @update:modelValue="(checked) => handleVendorSelect(vendor.vendor_id, checked)"
                      class="flex-shrink-0"
                    />
                    
                    <!-- Avatar -->
                    <div class="flex items-center justify-center w-12 h-12 rounded-full bg-blue-600 text-white font-bold text-lg shadow-md flex-shrink-0">
                      {{ vendor.company_name?.charAt(0) || 'V' }}
                    </div>
                    
                    <!-- Main Content - Company Info -->
                    <div class="flex-1 min-w-0 grid grid-cols-1 md:grid-cols-4 gap-4">
                      <!-- Company Name & Location -->
                      <div class="md:col-span-1">
                        <h3 class="font-bold text-base text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                          {{ vendor.company_name }}
                        </h3>
                        <div class="flex items-center gap-1 text-xs text-gray-600 mt-0.5">
                          <MapPin class="h-3 w-3" />
                          <span>{{ vendor.headquarters_country || 'Unknown' }}</span>
                        </div>
                      </div>
                      
                      <!-- Contact Info -->
                      <div class="md:col-span-1">
                        <p class="text-sm font-medium text-gray-900 truncate">{{ getPrimaryContactName(vendor) }}</p>
                        <p class="text-xs text-gray-600 truncate">{{ getPrimaryContactEmail(vendor) }}</p>
                        <p class="text-xs text-gray-600">{{ getPrimaryContactPhone(vendor) }}</p>
                      </div>
                      
                      <!-- Capabilities & Certifications -->
                      <div class="md:col-span-1">
                        <p class="text-xs font-medium text-gray-700 mb-1">Capabilities</p>
                        <div class="flex flex-wrap gap-1">
                          <span 
                            v-for="capability in (vendor.capabilities || []).slice(0, 2)" 
                            :key="capability"
                            class="inline-flex items-center px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs"
                          >
                            {{ capability }}
                          </span>
                          <span v-if="(vendor.capabilities || []).length > 2" class="inline-flex items-center px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                            +{{ (vendor.capabilities || []).length - 2 }}
                          </span>
                        </div>
                      </div>
                      
                      <!-- Stats & Details -->
                      <div class="md:col-span-1 flex flex-col items-end justify-center gap-2">
                        <div 
                          class="relative"
                          @click="vendor.showBreakdown = !vendor.showBreakdown"
                        >
                          <button 
                            :class="[
                              'flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold shadow-sm hover:shadow-md active:scale-95 transition-all',
                              getMatchBadgeColor(vendor.match_score)
                            ]"
                            :title="vendor.match_breakdown ? 'Click to see match breakdown' : 'Match score breakdown loading...'"
                          >
                            <span>{{ vendor.match_score || 0 }}% match</span>
                            <svg 
                              :class="[
                                'h-3.5 w-3.5 transition-transform',
                                vendor.showBreakdown ? 'rotate-180' : ''
                              ]"
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                            >
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          </button>
                          
                          <!-- Tooltip/Dropdown -->
                          <div 
                            v-if="vendor.showBreakdown"
                            class="absolute right-0 top-full mt-2 w-80 bg-white border-2 border-blue-500 rounded-lg shadow-2xl p-4 z-[9999] animate-in"
                          >
                            <div v-if="vendor.match_breakdown" class="space-y-3">
                              <div class="flex items-center justify-between pb-2 border-b border-gray-200">
                                <h4 class="font-bold text-gray-900">Match Score Breakdown</h4>
                                <span class="text-lg font-bold text-blue-600">{{ vendor.match_score || 0 }}%</span>
                              </div>
                              
                              <!-- Location Score -->
                              <div class="space-y-1">
                                <div class="flex items-center justify-between">
                                  <div class="flex items-center gap-2">
                                    <MapPin class="h-4 w-4 text-blue-600" />
                                    <span class="text-sm font-semibold text-gray-700">Location Match</span>
                                  </div>
                                  <span class="text-sm font-bold text-gray-900">{{ vendor.match_breakdown.location }}/30</span>
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-2">
                                  <div 
                                    class="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                    :style="{ width: `${(vendor.match_breakdown.location / 30) * 100}%` }"
                                  ></div>
                                </div>
                              </div>
                              
                              <!-- Industry Score -->
                              <div class="space-y-1">
                                <div class="flex items-center justify-between">
                                  <div class="flex items-center gap-2">
                                    <Building2 class="h-4 w-4 text-purple-600" />
                                    <span class="text-sm font-semibold text-gray-700">Industry Match</span>
                                  </div>
                                  <span class="text-sm font-bold text-gray-900">{{ vendor.match_breakdown.industry }}/25</span>
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-2">
                                  <div 
                                    class="bg-purple-500 h-2 rounded-full transition-all duration-300"
                                    :style="{ width: `${(vendor.match_breakdown.industry / 25) * 100}%` }"
                                  ></div>
                                </div>
                              </div>
                              
                              <!-- Budget Score -->
                              <div class="space-y-1">
                                <div class="flex items-center justify-between">
                                  <div class="flex items-center gap-2">
                                    <svg class="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <span class="text-sm font-semibold text-gray-700">Budget Match</span>
                                  </div>
                                  <span class="text-sm font-bold text-gray-900">{{ vendor.match_breakdown.budget }}/25</span>
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-2">
                                  <div 
                                    class="bg-green-500 h-2 rounded-full transition-all duration-300"
                                    :style="{ width: `${(vendor.match_breakdown.budget / 25) * 100}%` }"
                                  ></div>
                                </div>
                              </div>
                              
                              <!-- Business Type Score -->
                              <div class="space-y-1">
                                <div class="flex items-center justify-between">
                                  <div class="flex items-center gap-2">
                                    <svg class="h-4 w-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                    </svg>
                                    <span class="text-sm font-semibold text-gray-700">Business Type</span>
                                  </div>
                                  <span class="text-sm font-bold text-gray-900">{{ vendor.match_breakdown.business_type }}/20</span>
                                </div>
                                <div class="w-full bg-gray-200 rounded-full h-2">
                                  <div 
                                    class="bg-orange-500 h-2 rounded-full transition-all duration-300"
                                    :style="{ width: `${(vendor.match_breakdown.business_type / 20) * 100}%` }"
                                  ></div>
                                </div>
                              </div>
                              
                              <div class="pt-2 border-t border-gray-200">
                                <p class="text-xs text-gray-600 text-center">
                                  Based on RFP requirements vs vendor profile
                                </p>
                              </div>
                            </div>
                            
                            <!-- Fallback message when breakdown is not available -->
                            <div v-else class="text-center py-2">
                              <p class="text-sm text-gray-700 font-semibold mb-1">Match Score: {{ vendor.match_score || 0 }}%</p>
                              <p class="text-xs text-gray-500">Calculating detailed breakdown...</p>
                              <p class="text-xs text-gray-400 mt-2">Refresh the page if score doesn't update</p>
                            </div>
                          </div>
                        </div>
                        <div class="px-2.5 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold shadow-sm">
                          {{ vendor.status || 'APPROVED' }}
                        </div>
                      </div>
                    </div>
                    
                    <!-- Expand Button -->
                    <button 
                      @click="vendor.expanded = !vendor.expanded"
                      class="flex-shrink-0 p-2 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <ChevronDown 
                        :class="['h-5 w-5 text-gray-600 transition-transform', vendor.expanded ? 'rotate-180' : '']"
                      />
                    </button>
                  </div>
                </div>
                
                <!-- Expandable Details Section -->
                <div v-if="vendor.expanded" class="border-t border-gray-200 bg-gray-50 px-6 py-4 space-y-4">
                  <!-- Primary Contact Information (from vendor_contacts table) -->
                  <div class="space-y-3">
                    <div class="flex items-center gap-2">
                      <div class="h-1 w-6 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"></div>
                      <h4 class="font-semibold text-sm text-gray-900">Primary Contact</h4>
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg border border-blue-100">
                      <div class="flex items-start gap-2 text-sm">
                        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex-shrink-0">
                          <Users class="h-4 w-4" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-xs text-gray-500 mb-0.5">Contact Name</p>
                          <p class="font-medium text-gray-900 truncate">{{ getPrimaryContactName(vendor) }}</p>
                          <p v-if="getPrimaryContactDesignation(vendor)" class="text-xs text-gray-600 truncate">{{ getPrimaryContactDesignation(vendor) }}</p>
                        </div>
                      </div>
                      <div class="flex items-start gap-2 text-sm">
                        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-green-100 text-green-600 flex-shrink-0">
                          <Mail class="h-4 w-4" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-xs text-gray-500 mb-0.5">Email</p>
                          <p class="font-medium text-gray-900 truncate" :title="getPrimaryContactEmail(vendor)">{{ getPrimaryContactEmail(vendor) }}</p>
                        </div>
                      </div>
                      <div class="flex items-start gap-2 text-sm">
                        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-100 text-purple-600 flex-shrink-0">
                          <Phone class="h-4 w-4" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-xs text-gray-500 mb-0.5">Phone</p>
                          <p class="font-medium text-gray-900">{{ getPrimaryContactPhone(vendor) }}</p>
                        </div>
                      </div>
                      <div class="flex items-start gap-2 text-sm">
                        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-orange-100 text-orange-600 flex-shrink-0">
                          <Building2 class="h-4 w-4" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-xs text-gray-500 mb-0.5">Department</p>
                          <p class="font-medium text-gray-900 truncate">{{ getPrimaryContactDepartment(vendor) || 'N/A' }}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Vendor Information -->
                  <div class="grid grid-cols-2 gap-3 p-4 bg-gray-50 rounded-lg">
                    <div class="flex items-center gap-2 text-sm">
                      <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-100 text-purple-600">
                        <Globe class="h-4 w-4" />
                      </div>
                      <div class="flex-1 min-w-0">
                        <p class="text-xs text-gray-500">Website</p>
                        <p class="font-medium text-gray-900 truncate" :title="vendor.website">{{ vendor.website || 'N/A' }}</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-2 text-sm">
                      <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-orange-100 text-orange-600">
                        <Award class="h-4 w-4" />
                      </div>
                      <div class="flex-1 min-w-0">
                        <p class="text-xs text-gray-500">Experience</p>
                        <p class="font-medium text-gray-900">{{ vendor.experience_years || 0 }} years</p>
                      </div>
                    </div>
                  </div>

                  <!-- Capabilities -->
                  <div class="space-y-2">
                    <div class="flex items-center gap-2">
                      <div class="h-1 w-6 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"></div>
                      <h4 class="font-semibold text-sm text-gray-900">Capabilities</h4>
                    </div>
                    <div class="flex flex-wrap gap-1.5">
                      <span 
                        v-for="capability in (vendor.capabilities || [])" 
                        :key="capability"
                        class="inline-flex items-center px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium border border-blue-200"
                      >
                        {{ capability }}
                      </span>
                      <span v-if="!vendor.capabilities || vendor.capabilities.length === 0" class="text-xs text-gray-500 italic">No capabilities listed</span>
                    </div>
                  </div>

                  <!-- Certifications -->
                  <div class="space-y-2">
                    <div class="flex items-center gap-2">
                      <div class="h-1 w-6 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                      <h4 class="font-semibold text-sm text-gray-900">Certifications</h4>
                    </div>
                    <div class="flex flex-wrap gap-1.5">
                      <span 
                        v-for="cert in (vendor.certifications || [])" 
                        :key="cert"
                        class="inline-flex items-center px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-xs font-medium border border-purple-200"
                      >
                        {{ cert }}
                      </span>
                      <span v-if="!vendor.certifications || vendor.certifications.length === 0" class="text-xs text-gray-500 italic">No certifications listed</span>
                    </div>
                  </div>

                  <!-- Additional Details -->
                  <div class="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                    <div class="p-3 bg-gray-50 rounded-lg">
                      <span class="text-xs font-medium text-gray-500 block mb-1">Company Size</span>
                      <p class="text-sm font-semibold text-gray-900">{{ formatEmployeeCount(vendor.employee_count) }}</p>
                    </div>
                    <div class="p-3 bg-gray-50 rounded-lg">
                      <span class="text-xs font-medium text-gray-500 block mb-1">Risk Level</span>
                      <p class="text-sm font-semibold text-gray-900">{{ vendor.risk_level || 'Unknown' }}</p>
                    </div>
                    <div class="p-3 bg-gray-50 rounded-lg">
                      <span class="text-xs font-medium text-gray-500 block mb-1">Business Type</span>
                      <p class="text-sm font-semibold text-gray-900">{{ vendor.business_type || 'N/A' }}</p>
                    </div>
                    <div class="p-3 bg-gray-50 rounded-lg">
                      <span class="text-xs font-medium text-gray-500 block mb-1">Industry</span>
                      <p class="text-sm font-semibold text-gray-900">{{ vendor.industry_sector || 'N/A' }}</p>
                    </div>
                  </div>
                  
                  <div v-if="vendor.annual_revenue" class="p-3 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg">
                    <span class="text-xs font-medium text-gray-500 block mb-1">Annual Revenue</span>
                    <p class="text-sm font-bold text-green-700">{{ formatCurrency(vendor.annual_revenue) }}</p>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Existing Vendors Grid View -->
            <div v-if="viewMode === 'grid'" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div 
                v-for="vendor in filteredExistingVendors" 
                :key="vendor.vendor_id"
                :class="[
                  'group relative bg-white border-2 rounded-xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden',
                  selectedExistingVendors.includes(vendor.vendor_id) 
                    ? 'border-blue-500 ring-4 ring-blue-200' 
                    : 'border-gray-200 hover:border-blue-300'
                ]"
              >
                <!-- Card Header -->
                <div class="p-6 pb-4">
                  <div class="flex items-start justify-between gap-4">
                    <div class="flex items-start gap-3 flex-1">
                      <Checkbox
                        :modelValue="selectedExistingVendors.includes(vendor.vendor_id)"
                        @update:modelValue="(checked) => handleVendorSelect(vendor.vendor_id, checked)"
                        class="mt-1"
                      />
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-2">
                          <div class="flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 text-white font-bold text-lg shadow-md flex-shrink-0">
                            {{ vendor.company_name?.charAt(0) || 'V' }}
                          </div>
                          <div class="flex-1 min-w-0">
                            <h3 class="font-bold text-lg text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                              {{ vendor.company_name }}
                            </h3>
                            <div class="flex items-center gap-3 text-sm text-gray-600 mt-1">
                              <div class="flex items-center gap-1">
                                <MapPin class="h-3.5 w-3.5" />
                                <span>{{ vendor.headquarters_country || 'Unknown' }}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div class="flex flex-col gap-2 items-end">
                      <div 
                        class="relative"
                        @click="vendor.showBreakdown = !vendor.showBreakdown"
                      >
                        <button 
                          :class="[
                            'flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold shadow-sm hover:shadow-md active:scale-95 transition-all',
                            getMatchBadgeColor(vendor.match_score)
                          ]"
                          :title="vendor.match_breakdown ? 'Click to see match breakdown' : 'Match score breakdown loading...'"
                        >
                          <span>{{ vendor.match_score || 0 }}% match</span>
                          <svg 
                            :class="[
                              'h-3.5 w-3.5 transition-transform',
                              vendor.showBreakdown ? 'rotate-180' : ''
                            ]"
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </button>
                        
                        <!-- Tooltip/Dropdown -->
                        <div 
                          v-if="vendor.showBreakdown"
                          class="absolute right-0 top-full mt-2 w-80 bg-white border-2 border-blue-500 rounded-lg shadow-2xl p-4 z-[9999] animate-in"
                        >
                          <div v-if="vendor.match_breakdown" class="space-y-3">
                            <div class="flex items-center justify-between pb-2 border-b border-gray-200">
                              <h4 class="font-bold text-gray-900">Match Score Breakdown</h4>
                              <span class="text-lg font-bold text-blue-600">{{ vendor.match_score || 0 }}%</span>
                            </div>
                            
                            <!-- Location Score -->
                            <div class="space-y-1">
                              <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                  <MapPin class="h-4 w-4 text-blue-600" />
                                  <span class="text-sm font-semibold text-gray-700">Location Match</span>
                                </div>
                                <span class="text-sm font-bold text-gray-900">{{ vendor.match_breakdown.location }}/30</span>
                              </div>
                              <div class="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                  class="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                  :style="{ width: `${(vendor.match_breakdown.location / 30) * 100}%` }"
                                ></div>
                              </div>
                            </div>
                            
                            <!-- Industry Score -->
                            <div class="space-y-1">
                              <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                  <Building2 class="h-4 w-4 text-purple-600" />
                                  <span class="text-sm font-semibold text-gray-700">Industry Match</span>
                                </div>
                                <span class="text-sm font-bold text-gray-900">{{ vendor.match_breakdown.industry }}/25</span>
                              </div>
                              <div class="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                  class="bg-purple-500 h-2 rounded-full transition-all duration-300"
                                  :style="{ width: `${(vendor.match_breakdown.industry / 25) * 100}%` }"
                                ></div>
                              </div>
                            </div>
                            
                            <!-- Budget Score -->
                            <div class="space-y-1">
                              <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                  <svg class="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                  <span class="text-sm font-semibold text-gray-700">Budget Match</span>
                                </div>
                                <span class="text-sm font-bold text-gray-900">{{ vendor.match_breakdown.budget }}/25</span>
                              </div>
                              <div class="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                  class="bg-green-500 h-2 rounded-full transition-all duration-300"
                                  :style="{ width: `${(vendor.match_breakdown.budget / 25) * 100}%` }"
                                ></div>
                              </div>
                            </div>
                            
                            <!-- Business Type Score -->
                            <div class="space-y-1">
                              <div class="flex items-center justify-between">
                                <div class="flex items-center gap-2">
                                  <svg class="h-4 w-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                  </svg>
                                  <span class="text-sm font-semibold text-gray-700">Business Type</span>
                                </div>
                                <span class="text-sm font-bold text-gray-900">{{ vendor.match_breakdown.business_type }}/20</span>
                              </div>
                              <div class="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                  class="bg-orange-500 h-2 rounded-full transition-all duration-300"
                                  :style="{ width: `${(vendor.match_breakdown.business_type / 20) * 100}%` }"
                                ></div>
                              </div>
                            </div>
                            
                            <div class="pt-2 border-t border-gray-200">
                              <p class="text-xs text-gray-600 text-center">
                                Based on RFP requirements vs vendor profile
                              </p>
                            </div>
                          </div>
                          
                          <!-- Fallback message when breakdown is not available -->
                          <div v-else class="text-center py-2">
                            <p class="text-sm text-gray-700 font-semibold mb-1">Match Score: {{ vendor.match_score || 0 }}%</p>
                            <p class="text-xs text-gray-500">Calculating detailed breakdown...</p>
                            <p class="text-xs text-gray-400 mt-2">Refresh the page if score doesn't update</p>
                          </div>
                        </div>
                      </div>
                      <div class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold shadow-sm">
                        {{ vendor.status || 'APPROVED' }}
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Card Body -->
                <div class="px-6 pb-6 space-y-4">
                  <!-- Primary Contact Information -->
                  <div class="space-y-3">
                    <div class="flex items-center gap-2">
                      <div class="h-1 w-6 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full"></div>
                      <h4 class="font-semibold text-sm text-gray-900">Primary Contact</h4>
                    </div>
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg border border-blue-100">
                      <div class="flex items-start gap-2 text-sm">
                        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-100 text-blue-600 flex-shrink-0">
                          <Users class="h-4 w-4" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-xs text-gray-500 mb-0.5">Contact Name</p>
                          <p class="font-medium text-gray-900 truncate">{{ getPrimaryContactName(vendor) }}</p>
                          <p v-if="getPrimaryContactDesignation(vendor)" class="text-xs text-gray-600 truncate">{{ getPrimaryContactDesignation(vendor) }}</p>
                        </div>
                      </div>
                      <div class="flex items-start gap-2 text-sm">
                        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-green-100 text-green-600 flex-shrink-0">
                          <Mail class="h-4 w-4" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-xs text-gray-500 mb-0.5">Email</p>
                          <p class="font-medium text-gray-900 truncate" :title="getPrimaryContactEmail(vendor)">{{ getPrimaryContactEmail(vendor) }}</p>
                        </div>
                      </div>
                      <div class="flex items-start gap-2 text-sm">
                        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-100 text-purple-600 flex-shrink-0">
                          <Phone class="h-4 w-4" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-xs text-gray-500 mb-0.5">Phone</p>
                          <p class="font-medium text-gray-900">{{ getPrimaryContactPhone(vendor) }}</p>
                        </div>
                      </div>
                      <div class="flex items-start gap-2 text-sm">
                        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-orange-100 text-orange-600 flex-shrink-0">
                          <Building2 class="h-4 w-4" />
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-xs text-gray-500 mb-0.5">Department</p>
                          <p class="font-medium text-gray-900 truncate">{{ getPrimaryContactDepartment(vendor) || 'N/A' }}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Vendor Information -->
                  <div class="grid grid-cols-2 gap-3 p-4 bg-gray-50 rounded-lg">
                    <div class="flex items-center gap-2 text-sm">
                      <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-100 text-purple-600">
                        <Globe class="h-4 w-4" />
                      </div>
                      <div class="flex-1 min-w-0">
                        <p class="text-xs text-gray-500">Website</p>
                        <p class="font-medium text-gray-900 truncate" :title="vendor.website">{{ vendor.website || 'N/A' }}</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-2 text-sm">
                      <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-orange-100 text-orange-600">
                        <Award class="h-4 w-4" />
                      </div>
                      <div class="flex-1 min-w-0">
                        <p class="text-xs text-gray-500">Experience</p>
                        <p class="font-medium text-gray-900">{{ vendor.experience_years || 0 }} years</p>
                      </div>
                    </div>
                  </div>

                  <!-- Capabilities -->
                  <div class="space-y-2">
                    <div class="flex items-center gap-2">
                      <div class="h-1 w-6 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"></div>
                      <h4 class="font-semibold text-sm text-gray-900">Capabilities</h4>
                    </div>
                    <div class="flex flex-wrap gap-1.5">
                      <span 
                        v-for="capability in (vendor.capabilities || [])" 
                        :key="capability"
                        class="inline-flex items-center px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium border border-blue-200"
                      >
                        {{ capability }}
                      </span>
                      <span v-if="!vendor.capabilities || vendor.capabilities.length === 0" class="text-xs text-gray-500 italic">No capabilities listed</span>
                    </div>
                  </div>

                  <!-- Certifications -->
                  <div class="space-y-2">
                    <div class="flex items-center gap-2">
                      <div class="h-1 w-6 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                      <h4 class="font-semibold text-sm text-gray-900">Certifications</h4>
                    </div>
                    <div class="flex flex-wrap gap-1.5">
                      <span 
                        v-for="cert in (vendor.certifications || [])" 
                        :key="cert"
                        class="inline-flex items-center px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-xs font-medium border border-purple-200"
                      >
                        {{ cert }}
                      </span>
                      <span v-if="!vendor.certifications || vendor.certifications.length === 0" class="text-xs text-gray-500 italic">No certifications listed</span>
                    </div>
                  </div>

                  <!-- Additional Details -->
                  <div class="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                    <div class="p-3 bg-gray-50 rounded-lg">
                      <span class="text-xs font-medium text-gray-500 block mb-1">Company Size</span>
                      <p class="text-sm font-semibold text-gray-900">{{ formatEmployeeCount(vendor.employee_count) }}</p>
                    </div>
                    <div class="p-3 bg-gray-50 rounded-lg">
                      <span class="text-xs font-medium text-gray-500 block mb-1">Risk Level</span>
                      <p class="text-sm font-semibold text-gray-900">{{ vendor.risk_level || 'Unknown' }}</p>
                    </div>
                    <div class="p-3 bg-gray-50 rounded-lg">
                      <span class="text-xs font-medium text-gray-500 block mb-1">Business Type</span>
                      <p class="text-sm font-semibold text-gray-900">{{ vendor.business_type || 'N/A' }}</p>
                    </div>
                    <div class="p-3 bg-gray-50 rounded-lg">
                      <span class="text-xs font-medium text-gray-500 block mb-1">Industry</span>
                      <p class="text-sm font-semibold text-gray-900">{{ vendor.industry_sector || 'N/A' }}</p>
                    </div>
                  </div>
                  
                  <div v-if="vendor.annual_revenue" class="p-3 bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg">
                    <span class="text-xs font-medium text-gray-500 block mb-1">Annual Revenue</span>
                    <p class="text-sm font-bold text-green-700">{{ formatCurrency(vendor.annual_revenue) }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Manual Creation Tab -->
          <div v-if="activeTab === 'manual'" class="space-y-6">
            <div class="max-w-6xl mx-auto">
              <!-- Header Section -->
              <div class="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl p-6 mb-6 shadow-sm">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <div>
                    <h3 class="text-2xl font-bold text-gray-900 mb-1">Create Multiple Vendors</h3>
                    <p class="text-sm text-gray-600">Add new vendors manually by filling in their details below</p>
                  </div>
                  <div class="flex gap-2.5">
                    <button 
                      @click="addVendorForm" 
                      class="inline-flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-purple-50 text-purple-700 hover:text-purple-800 border border-purple-300 hover:border-purple-400 rounded-lg font-medium text-sm transition-all duration-200 shadow-sm hover:shadow-md"
                    >
                      <Plus class="h-4 w-4" />
                      Add Vendor Form
                    </button>
                    <button 
                      @click="resetAllForms" 
                      class="inline-flex items-center gap-2 px-4 py-2.5 bg-white hover:bg-red-50 text-red-700 hover:text-red-800 border border-red-300 hover:border-red-400 rounded-lg font-medium text-sm transition-all duration-200 shadow-sm hover:shadow-md"
                    >
                      <X class="h-4 w-4" />
                      Reset All
                    </button>
                  </div>
                </div>
              </div>
              
              <!-- Vendor Forms -->
              <div class="space-y-6">
                <div 
                  v-for="(form, formIndex) in vendorForms" 
                  :key="form.id" 
                  class="group relative bg-white border-2 border-gray-200 hover:border-purple-300 rounded-xl p-6 shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <!-- Form Header -->
                  <div class="flex justify-between items-center mb-6 pb-4 border-b border-gray-200">
                    <div class="flex items-center gap-3">
                      <div class="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 text-white font-bold text-lg shadow-md">
                        {{ formIndex + 1 }}
                      </div>
                      <div>
                        <h4 class="font-semibold text-lg text-gray-900">Vendor {{ formIndex + 1 }}</h4>
                        <p class="text-xs text-gray-500">Fill in the details below</p>
                      </div>
                    </div>
                    <button 
                      v-if="vendorForms.length > 1" 
                      @click="removeVendorForm(form.id)" 
                      class="inline-flex items-center gap-2 px-3 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 border border-transparent hover:border-red-200 rounded-lg font-medium text-sm transition-all duration-200"
                    >
                      <X class="h-4 w-4" />
                      Remove
                    </button>
                  </div>
                  
                  <!-- Form Fields -->
                  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <!-- Basic Information -->
                    <div class="space-y-5">
                      <div class="flex items-center gap-2 mb-4">
                        <div class="h-1 w-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                        <h4 class="font-semibold text-gray-900 text-base">Basic Information</h4>
                      </div>
                      
                      <div class="space-y-1">
                        <label class="block text-sm font-semibold text-gray-700">
                          Company Name <span class="text-red-500">*</span>
                        </label>
                        <input
                          v-model="form.company_name"
                          type="text"
                          required
                          class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-200 text-gray-900 placeholder-gray-400"
                          placeholder="Enter company name"
                        />
                      </div>
                      
                      <div class="space-y-1">
                        <label class="block text-sm font-semibold text-gray-700">
                          Contact Person Name <span class="text-red-500">*</span>
                        </label>
                        <input
                          v-model="form.vendor_name"
                          type="text"
                          required
                          class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-200 text-gray-900 placeholder-gray-400"
                          placeholder="Enter contact person name"
                        />
                      </div>
                      
                      <div class="space-y-1">
                        <label class="block text-sm font-semibold text-gray-700">Industry Sector</label>
                        <input
                          v-model="form.industry_sector"
                          type="text"
                          class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-200 text-gray-900 placeholder-gray-400"
                          placeholder="e.g., Technology, Healthcare, Finance"
                        />
                      </div>
                      
                      <div class="space-y-1">
                        <label class="block text-sm font-semibold text-gray-700">Website</label>
                        <input
                          v-model="form.website"
                          type="url"
                          class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition-all duration-200 text-gray-900 placeholder-gray-400"
                          placeholder="https://www.company.com"
                        />
                      </div>
                    </div>

                    <!-- Contact Information -->
                    <div class="space-y-5">
                      <div class="flex items-center gap-2 mb-4">
                        <div class="h-1 w-8 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"></div>
                        <h4 class="font-semibold text-gray-900 text-base">Contact Information</h4>
                      </div>
                      
                      <div class="space-y-1">
                        <label class="block text-sm font-semibold text-gray-700">
                          Email <span class="text-red-500">*</span>
                        </label>
                        <input
                          v-model="form.vendor_email"
                          type="email"
                          required
                          class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-200 text-gray-900 placeholder-gray-400"
                          placeholder="contact@company.com"
                        />
                      </div>
                      
                      <div class="space-y-1">
                        <label class="block text-sm font-semibold text-gray-700">
                          Phone <span class="text-red-500">*</span>
                        </label>
                        <input
                          v-model="form.vendor_phone"
                          type="tel"
                          required
                          class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-200 text-gray-900 placeholder-gray-400"
                          placeholder="+1 (555) 123-4567"
                        />
                      </div>
                      
                      <div class="space-y-1">
                        <label class="block text-sm font-semibold text-gray-700">Description</label>
                        <textarea
                          v-model="form.description"
                          rows="4"
                          class="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all duration-200 text-gray-900 placeholder-gray-400 resize-none"
                          placeholder="Brief description of the vendor's business and capabilities"
                        ></textarea>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Form Actions -->
              <div class="mt-8 bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200 rounded-xl p-6">
                <div class="flex flex-col sm:flex-row justify-between items-center gap-4">
                  <div class="flex items-center gap-3">
                    <div class="flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-emerald-500 text-white font-bold shadow-md">
                      <CheckCircle class="h-5 w-5" />
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-900">Ready to create {{ vendorForms.length }} vendor(s)</p>
                      <p class="text-xs text-gray-500">Review the information before submitting</p>
                    </div>
                  </div>
                  <div class="flex gap-3">
                    <button 
                      type="button" 
                      @click="resetAllForms"
                      class="inline-flex items-center gap-2 px-6 py-3 bg-white hover:bg-gray-50 text-gray-700 hover:text-gray-900 border-2 border-gray-300 hover:border-gray-400 rounded-lg font-semibold text-sm transition-all duration-200 shadow-sm hover:shadow-md"
                    >
                      <X class="h-4 w-4" />
                      Reset All
                    </button>
                    <button 
                      @click="handleMultipleVendorCreation" 
                      :disabled="isCreatingVendor"
                      class="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-400 disabled:to-gray-500 text-white border-2 border-green-600 hover:border-green-700 disabled:border-gray-400 rounded-lg font-semibold text-sm transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5 disabled:transform-none disabled:cursor-not-allowed"
                    >
                      <CheckCircle2 class="h-4 w-4" />
                      <span v-if="isCreatingVendor">Creating {{ vendorForms.length }} Vendor(s)...</span>
                      <span v-else>Create {{ vendorForms.length }} Vendor(s)</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>


        </div>
      </div>

      <!-- Selection Summary -->
      <div v-if="allSelectedVendors.total > 0" class="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl shadow-lg p-6">
        <div class="space-y-6">
          <!-- Header Section -->
          <div class="flex items-center justify-between border-b border-blue-200 pb-4">
            <div>
              <h3 class="text-2xl font-bold text-gray-900 mb-1">Selection Summary</h3>
              <p class="text-sm text-gray-600">
                <span class="font-semibold text-blue-700">{{ allSelectedVendors.total }}</span> 
                vendor{{ allSelectedVendors.total !== 1 ? 's' : '' }} selected for invitation
              </p>
            </div>
            <div class="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow-sm border border-blue-200">
              <div class="flex items-center gap-2 text-sm">
                <span class="font-medium text-gray-700">Existing:</span>
                <span class="font-bold text-green-600">{{ allSelectedVendors.existing.length }}</span>
              </div>
              <div class="h-4 w-px bg-gray-300"></div>
              <div class="flex items-center gap-2 text-sm">
                <span class="font-medium text-gray-700">Manual:</span>
                <span class="font-bold text-yellow-600">{{ allSelectedVendors.manual.length }}</span>
              </div>
              <div class="h-4 w-px bg-gray-300"></div>
              <div class="flex items-center gap-2 text-sm">
                <span class="font-medium text-gray-700">Bulk:</span>
                <span class="font-bold text-purple-600">{{ allSelectedVendors.bulk.length }}</span>
              </div>
            </div>
          </div>
          
          <!-- Vendor Lists Section -->
          <div class="space-y-4">
              <!-- Existing Vendors -->
            <div v-if="allSelectedVendors.existing.length > 0" class="bg-white rounded-lg p-4 border border-green-200 shadow-sm">
              <div class="flex items-center gap-2 mb-3">
                <div class="flex items-center justify-center w-8 h-8 rounded-full bg-green-100">
                  <CheckCircle2 class="h-4 w-4 text-green-600" />
                </div>
                <p class="font-semibold text-gray-900">Existing Vendors ({{ allSelectedVendors.existing.length }})</p>
              </div>
                <div class="flex flex-wrap gap-2">
                <span
                    v-for="vendor in allSelectedVendors.existing" 
                    :key="vendor.vendor_id" 
                  class="inline-flex items-center px-3 py-1.5 bg-green-50 text-green-800 border border-green-200 rounded-lg text-sm font-medium shadow-sm"
                  >
                    {{ vendor.company_name }}
                </span>
                </div>
              </div>
              
              <!-- Manual Vendors -->
            <div v-if="allSelectedVendors.manual.length > 0" class="bg-white rounded-lg p-4 border border-yellow-200 shadow-sm">
              <div class="flex items-center gap-2 mb-3">
                <div class="flex items-center justify-center w-8 h-8 rounded-full bg-yellow-100">
                  <Plus class="h-4 w-4 text-yellow-600" />
                </div>
                <p class="font-semibold text-gray-900">Manually Created Vendors ({{ allSelectedVendors.manual.length }})</p>
              </div>
                <div class="flex flex-wrap gap-2">
                <span
                    v-for="vendor in allSelectedVendors.manual" 
                    :key="vendor.id" 
                  class="inline-flex items-center px-3 py-1.5 bg-yellow-50 text-yellow-800 border border-yellow-200 rounded-lg text-sm font-medium shadow-sm"
                  >
                    {{ vendor.company_name }}
                </span>
                </div>
              </div>
              
              <!-- Bulk Vendors -->
            <div v-if="allSelectedVendors.bulk.length > 0" class="bg-white rounded-lg p-4 border border-purple-200 shadow-sm">
              <div class="flex items-center gap-2 mb-3">
                <div class="flex items-center justify-center w-8 h-8 rounded-full bg-purple-100">
                  <Upload class="h-4 w-4 text-purple-600" />
                </div>
                <p class="font-semibold text-gray-900">Bulk Uploaded Vendors ({{ allSelectedVendors.bulk.length }})</p>
              </div>
                <div class="flex flex-wrap gap-2">
                <span
                    v-for="vendor in allSelectedVendors.bulk" 
                    :key="vendor.unmatched_id" 
                  class="inline-flex items-center px-3 py-1.5 bg-purple-50 text-purple-800 border border-purple-200 rounded-lg text-sm font-medium shadow-sm"
                  >
                    {{ vendor.company_name }}
                </span>
                </div>
              </div>
            </div>
          
          <!-- Action Buttons -->
          <div class="flex items-center justify-end gap-3 pt-4 border-t border-blue-200">
            <a 
              href="/rfp-approval" 
              class="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-gray-700 bg-white border-2 border-gray-300 rounded-lg hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 shadow-sm hover:shadow-md"
            >
              <ArrowRight class="h-4 w-4 rotate-180" />
        Previous
      </a>
              <button 
                @click="handleGenerateURLs"
              class="inline-flex items-center gap-2 px-6 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 border-2 border-blue-600 hover:border-blue-700 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
              >
                  Generate URLs & Send Invitations
              <ArrowRight class="h-4 w-4" />
              </button>
            </div>
          </div>
      </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'
import { 
  Search, 
  Upload, 
  Star, 
  MapPin, 
  Award,
  Building2,
  Mail,
  Phone,
  Globe,
  ArrowRight,
  CheckCircle2,
  CheckCircle,
  AlertCircle,
  FileSpreadsheet,
  X,
  Users,
  Plus,
  FileText,
  Download,
  ChevronDown
} from 'lucide-vue-next'
import { rfpUseToast } from '@/composables/rfpUseToast.js'
import { useRfpApi } from '@/composables/useRfpApi.js'
import api from '@/utils/api_rfp.js'
import Checkbox from '@/components_rfp/ui/Checkbox.vue'
import rfpBadge from '@/components_rfp/rfpBadge.vue'
import rfpButton from '@/components_rfp/rfpButton.vue'
import rfpCard from '@/components_rfp/rfpCard.vue'
import rfpCardHeader from '@/components_rfp/rfpCardHeader.vue'
import rfpCardContent from '@/components_rfp/rfpCardContent.vue'

const { success, error } = rfpUseToast()

// Authentication
const { getAuthHeaders } = useRfpApi()

// Tab management
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const activeTab = ref('existing')
const tabs = ref([
  { id: 'existing', name: 'Approved Vendors', icon: Users, count: 0 },
  { id: 'manual', name: 'Manual Creation', icon: Plus, count: 0 }
])

// Ensure tabs array is always initialized
if (!tabs.value) {
  tabs.value = []
}

// Search and filtering
const searchTerm = ref('')
const selectedVendors = ref<string[]>([])
const activeFilter = ref('all')
const selectedRFP = ref(null)
const viewMode = ref('list') // 'list' or 'grid'

// Unified vendor selection state
const selectedExistingVendors = ref<string[]>([])  // Existing approved vendors
const selectedManualVendors = ref<any[]>([])       // Manually created vendors
const selectedBulkVendors = ref<any[]>([])         // Bulk uploaded vendors

// Ensure selectedVendors is always initialized
if (!selectedVendors.value) {
  selectedVendors.value = []
}

// Vendor data
const existingVendors = ref([])

// Ensure vendor arrays are always initialized
if (!existingVendors.value) {
  existingVendors.value = []
}

// Bulk upload visibility
const showBulkUpload = ref(false)

// Computed property for all selected vendors (unified)
const allSelectedVendors = computed(() => {
  const existing = (existingVendors.value || []).filter(v => selectedExistingVendors.value.includes(v.vendor_id))
  const manual = selectedManualVendors.value || []
  const bulk = selectedBulkVendors.value || []
  
  return {
    existing: existing,
    manual: manual,
    bulk: bulk,
    total: existing.length + manual.length + bulk.length
  }
})

// Manual vendor creation - Multiple vendors support
const isCreatingVendor = ref(false)
const vendorForms = ref([
  {
    id: 1,
    company_name: '',
    vendor_name: '',
    vendor_email: '',
    vendor_phone: '',
    website: '',
    industry_sector: '',
    description: ''
  }
])

// Ensure vendor forms arrays are always initialized
const initializeVendorForm = (form: any) => {
  // Initialize required fields if not present
  if (!form.company_name) form.company_name = ''
  if (!form.vendor_name) form.vendor_name = ''
  if (!form.vendor_email) form.vendor_email = ''
  if (!form.vendor_phone) form.vendor_phone = ''
  if (!form.website) form.website = ''
  if (!form.industry_sector) form.industry_sector = ''
  if (!form.description) form.description = ''
}

// Initialize the first form
initializeVendorForm(vendorForms.value[0])

// Bulk upload
const selectedFile = ref(null)
const isDragOver = ref(false)
const isUploading = ref(false)
const uploadProgress = ref({
  show: false,
  percentage: 0,
  message: ''
})
const uploadResults = ref({
  show: false,
  successCount: 0,
  errorCount: 0,
  errors: []
})

// Ensure upload results arrays are always initialized
if (!uploadResults.value.errors) {
  uploadResults.value.errors = []
}

// Computed properties
const filteredExistingVendors = computed(() => {
  if (!existingVendors.value || !Array.isArray(existingVendors.value)) {
    return []
  }
  
  return existingVendors.value.filter(vendor => {
    if (!vendor) return false
    
    const searchLower = searchTerm.value.toLowerCase()
    const matchesSearch = (vendor.company_name || '').toLowerCase().includes(searchLower) ||
                         (vendor.capabilities || []).some(cap => cap.toLowerCase().includes(searchLower)) ||
                         (vendor.certifications || []).some(cert => cert.toLowerCase().includes(searchLower))
    
    if (activeFilter.value === "all") return matchesSearch
    if (activeFilter.value === "high-match") return matchesSearch && (vendor.match_score || 0) >= 90
    if (activeFilter.value === "certified") return matchesSearch && (vendor.certifications || []).length > 2
    return matchesSearch
  })
})

// Update tab counts
const updateTabCounts = () => {
  if (tabs.value && tabs.value.length > 0) {
    tabs.value[0].count = existingVendors.value?.length || 0
  }
}

// Utility functions
const getMatchBadgeColor = (score: number) => {
  if (score >= 90) return "status-badge awarded"
  if (score >= 80) return "status-badge evaluation"
  return "status-badge draft"
}

const getMatchingStatusBadgeColor = (status: string) => {
  switch (status) {
    case 'matched': return "status-badge awarded"
    case 'pending_review': return "status-badge evaluation"
    case 'rejected': return "status-badge draft"
    default: return "status-badge draft"
  }
}

const formatEmployeeCount = (count: number) => {
  if (!count) return "Unknown"
  if (count < 50) return "< 50"
  if (count < 200) return "50-200"
  if (count < 500) return "200-500"
  if (count < 1000) return "500-1000"
  return "1000+"
}

const extractPrimaryContact = (vendor: any) => {
  return vendor?.primary_contact || vendor?.contact_info || null
}

const normalizeContactResponse = (contactData: any, vendorId: number) => {
  if (!contactData) return null
  
  let contacts: any[] = []
  if (Array.isArray(contactData)) {
    contacts = contactData
  } else if (Array.isArray(contactData.results)) {
    contacts = contactData.results
  } else if (Array.isArray(contactData.contacts)) {
    contacts = contactData.contacts
  } else if (Array.isArray(contactData.data)) {
    contacts = contactData.data
  } else if (contactData.contact) {
    contacts = [contactData.contact]
  }
  
  if (!contacts.length) return null
  
  const numericVendorId = Number(vendorId)
  let primary = contacts.find(contact => Number(contact.vendor) === numericVendorId && (contact.contact_type === 'PRIMARY' || contact.is_primary))
  if (!primary) {
    primary = contacts.find(contact => Number(contact.vendor) === numericVendorId)
  }
  if (!primary && contacts.length) {
    primary = contacts[0]
  }
  return primary || null
}

const getPrimaryContactName = (vendor: any) => {
  const contact = extractPrimaryContact(vendor)
  if (contact) {
    const first = contact.first_name || contact.name || ''
    const last = contact.last_name || ''
    const combined = `${first} ${last}`.trim()
    if (combined) return combined
    if (contact.vendor_full_name) return contact.vendor_full_name
    if (contact.contact_name) return contact.contact_name
  }
  return vendor?.contact_name || vendor?.vendor_name || 'N/A'
}

const getPrimaryContactEmail = (vendor: any) => {
  const contact = extractPrimaryContact(vendor)
  return contact?.email || vendor?.email || 'N/A'
}

const getPrimaryContactPhone = (vendor: any) => {
  const contact = extractPrimaryContact(vendor)
  return contact?.mobile || contact?.phone || vendor?.phone || 'N/A'
}

const getPrimaryContactDesignation = (vendor: any) => {
  const contact = extractPrimaryContact(vendor)
  return contact?.designation || vendor?.contact_designation || ''
}

const getPrimaryContactDepartment = (vendor: any) => {
  const contact = extractPrimaryContact(vendor)
  return contact?.department || vendor?.contact_department || ''
}

const formatCurrency = (amount: number) => {
  if (!amount) return "N/A"
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(amount)
}


const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}


// Vendor selection methods
const handleVendorSelect = (vendorId: string, checked: boolean) => {
  if (checked) {
    if (!selectedExistingVendors.value.includes(vendorId)) {
      selectedExistingVendors.value = [...selectedExistingVendors.value, vendorId]
    }
  } else {
    selectedExistingVendors.value = selectedExistingVendors.value.filter(id => id !== vendorId)
  }
}

const handleBulkSelect = () => {
  const existingCount = existingVendors.value?.length || 0
  if (selectedExistingVendors.value.length === existingCount) {
    selectedExistingVendors.value = []
    success("All existing vendors deselected")
  } else {
    selectedExistingVendors.value = (existingVendors.value || []).map(v => v.vendor_id)
    success("All existing vendors selected")
  }
}

// Multiple vendor form management
const addVendorForm = () => {
  const newId = Math.max(...vendorForms.value.map(f => f.id)) + 1
  const newForm = {
    id: newId,
    company_name: '',
    vendor_name: '',
    vendor_email: '',
    vendor_phone: '',
    website: '',
    industry_sector: '',
    description: ''
  }
  initializeVendorForm(newForm)
  vendorForms.value.push(newForm)
}

const removeVendorForm = (formId: number) => {
  if (vendorForms.value.length > 1) {
    vendorForms.value = vendorForms.value.filter(form => form.id !== formId)
  } else {
    error("Cannot remove", "At least one vendor form is required.")
  }
}

// Manual vendor creation methods - removed capability and certification management

const resetAllForms = () => {
  vendorForms.value = [
    {
      id: 1,
      company_name: '',
      vendor_name: '',
      vendor_email: '',
      vendor_phone: '',
      website: '',
      industry_sector: '',
      description: ''
    }
  ]
  initializeVendorForm(vendorForms.value[0])
  success("Forms Reset", "All vendor forms have been reset to default values.")
}

const handleMultipleVendorCreation = async () => {
  isCreatingVendor.value = true
  try {
    // Validate all forms
    const validForms = []
    const errors = []
    
    for (let i = 0; i < vendorForms.value.length; i++) {
      const form = vendorForms.value[i]
      
      // Basic validation
      if (!form.company_name?.trim()) {
        errors.push(`Vendor ${i + 1}: Company name is required`)
        continue
      }
      if (!form.vendor_name?.trim()) {
        errors.push(`Vendor ${i + 1}: Contact person name is required`)
        continue
      }
      if (!form.vendor_email?.trim()) {
        errors.push(`Vendor ${i + 1}: Email is required`)
        continue
      }
      if (!form.vendor_phone?.trim()) {
        errors.push(`Vendor ${i + 1}: Phone is required`)
        continue
      }
      
      validForms.push(form)
    }
    
    if (errors.length > 0) {
      error("Validation Failed", errors.join('\n'))
      return
    }
    
    if (validForms.length === 0) {
      error("No Valid Forms", "Please fill in at least one valid vendor form.")
      return
    }
    
    // Create vendors one by one
    const results = {
      success: 0,
      failed: 0,
      errors: []
    }
    
    for (const vendorData of validForms) {
      try {
        // Prepare data for rfp_unmatched_vendors table
        const unmatchedVendorData = {
          vendor_name: vendorData.vendor_name,
          vendor_email: vendorData.vendor_email,
          vendor_phone: vendorData.vendor_phone,
          company_name: vendorData.company_name,
          submission_data: {
            website: vendorData.website,
            industry_sector: vendorData.industry_sector,
            description: vendorData.description
          },
          matching_status: 'unmatched'
        }
        
        const response = await api.post(`/rfps/${selectedRFP.value.rfp_id}/unmatched-vendors/create/`, unmatchedVendorData, {
          headers: getAuthHeaders()
        })
        
        if (response.status === 200 || response.status === 201) {
          const responseData = response.data
          results.success++
          
          // Add to selected manual vendors for unified selection
          selectedManualVendors.value.push({
            ...vendorData,
            id: responseData.unmatched_id || Date.now() + Math.random(), // Use response ID or generate temp ID
            type: 'manual'
          })
        } else {
          results.failed++
          results.errors.push(`${vendorData.company_name}: ${response.data?.message || 'Failed to create'}`)
        }
      } catch (err) {
        results.failed++
        results.errors.push(`${vendorData.company_name}: Network error`)
      }
    }
    
    // Show results
    if (results.success > 0) {
      success("Vendors Created", `${results.success} vendor(s) created successfully and added to unmatched vendors.`)
    }
    
    if (results.failed > 0) {
      error("Some Vendors Failed", `${results.failed} vendor(s) failed to create:\n${results.errors.join('\n')}`)
    }
    
    // Reset forms if all successful
    if (results.failed === 0) {
      resetAllForms()
    }
    
  } catch (err) {
    console.error('Error creating vendors:', err)
    error("Creation Failed", "An error occurred while creating the vendors.")
  } finally {
    isCreatingVendor.value = false
  }
}

// Bulk upload methods
const openFileDialog = () => {
  try {
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement
    if (fileInput) {
      fileInput.click()
    } else {
      console.error('File input not found')
      error("File Dialog Error", "File input element not found.")
    }
  } catch (error) {
    console.error('Error opening file dialog:', error)
    error("File Dialog Error", "Unable to open file selection dialog.")
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    const file = target.files[0]
    validateAndSetFile(file)
  }
}

const handleFileDrop = (event: DragEvent) => {
  isDragOver.value = false
  const files = event.dataTransfer?.files
  if (files && files[0]) {
    validateAndSetFile(files[0])
  }
}

const validateAndSetFile = (file: File) => {
  // Validate file type
  const allowedTypes = ['.csv', '.xlsx', '.xls']
  const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'))
  
  if (!allowedTypes.includes(fileExtension)) {
    error("Invalid File Type", "Please select a CSV or Excel file (.csv, .xlsx, .xls)")
    return
  }
  
  selectedFile.value = file
  uploadResults.value.show = false
  
  console.log('File selected:', file.name, file.size)
  success("File Selected", `Selected ${file.name} for upload`)
}

const removeFile = () => {
  selectedFile.value = null
  uploadProgress.value.show = false
  uploadResults.value.show = false
}

const handleBulkUpload = async () => {
  if (!selectedFile.value) return
  
  isUploading.value = true
  uploadProgress.value = {
    show: true,
    percentage: 0,
    message: 'Preparing upload...'
  }
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    
    uploadProgress.value.message = 'Uploading file...'
    uploadProgress.value.percentage = 50
    
    const response = await api.post(`/rfps/${selectedRFP.value.rfp_id}/unmatched-vendors/bulk-upload/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...getAuthHeaders()
      }
    })
    
    uploadProgress.value.percentage = 100
    uploadProgress.value.message = 'Processing complete!'
    
    if (response.status === 200 || response.status === 201) {
      const result = response.data
      uploadResults.value = {
        show: true,
        successCount: result.results?.success || 0,
        errorCount: result.results?.failed || 0,
        errors: result.results?.errors || []
      }
      
      if (result.results?.success > 0) {
        success("Upload Complete", `${result.results.success} vendors imported successfully and added to unmatched vendors.`)
        
        // Fetch the newly uploaded vendors to add to selected bulk vendors
        try {
          const vendorsResponse = await api.get(`/rfps/${selectedRFP.value.rfp_id}/unmatched-vendors/`, {
            headers: getAuthHeaders()
          })
          if (vendorsResponse.status === 200) {
            const vendors = vendorsResponse.data
            // Add all unmatched vendors to bulk selection (they were just uploaded)
            selectedBulkVendors.value = vendors.map((vendor: any) => ({
              ...vendor,
              type: 'bulk'
            }))
          }
        } catch (err) {
          console.error('Error fetching uploaded vendors:', err)
        }
      }
      
      if (result.results?.failed > 0) {
        error("Some Vendors Failed", `${result.results.failed} vendors failed to import:\n${result.results.errors.join('\n')}`)
      }
    } else {
      error("Upload Failed", response.data?.message || "Failed to upload vendors.")
    }
  } catch (err) {
    error("Upload Failed", "An error occurred during upload.")
  } finally {
    isUploading.value = false
    setTimeout(() => {
      uploadProgress.value.show = false
    }, 2000)
  }
}


// Calculate match scores based on RFP requirements
const calculateMatchScores = async (vendorIds) => {
  if (!selectedRFP.value || !vendorIds || vendorIds.length === 0) {
    console.log('⚠️ [DEBUG] Skipping match score calculation - no RFP or vendors')
    return
  }
  
  try {
    console.log('🎯 [DEBUG] Calculating match scores for vendors...')
    console.log('📊 [DEBUG] RFP ID:', selectedRFP.value.rfp_id)
    console.log('📊 [DEBUG] Vendor IDs:', vendorIds)
    
    const response = await api.post(`/rfps/${selectedRFP.value.rfp_id}/calculate-match-scores/`, {
      vendor_ids: vendorIds
    }, {
      headers: getAuthHeaders()
    })
    
    if (response.status === 200 && response.data.success) {
      console.log('✅ [DEBUG] Match scores calculated successfully')
      console.log('📊 [DEBUG] Results:', response.data.results)
      
      // Update vendors with new match scores
      response.data.results.forEach(result => {
        const vendor = existingVendors.value.find(v => v.vendor_id === result.vendor_id)
        if (vendor) {
          vendor.match_score = result.match_score
          vendor.match_breakdown = result.breakdown // Store breakdown for tooltip
          console.log(`✅ [DEBUG] Updated ${vendor.company_name}: ${result.match_score}%`)
          console.log(`📊 [DEBUG] Breakdown - Location: ${result.breakdown.location}/30, Industry: ${result.breakdown.industry}/25, Budget: ${result.breakdown.budget}/25, Type: ${result.breakdown.business_type}/20`)
          console.log(`🔍 [DEBUG] Match breakdown stored:`, vendor.match_breakdown)
        } else {
          console.warn(`⚠️ [DEBUG] Vendor ${result.vendor_id} not found in existingVendors array`)
        }
      })
      
      console.log(`✅ [DEBUG] Total vendors with breakdown: ${existingVendors.value.filter(v => v.match_breakdown).length}/${existingVendors.value.length}`)
      
      showInfo("Match Scores Calculated", `Match scores calculated for ${response.data.results.length} vendors based on RFP requirements`)
    }
  } catch (err) {
    console.error('❌ [DEBUG] Error calculating match scores:', err)
    // Don't show error to user - scores will just remain at 0
  }
}

// Data loading methods
const loadExistingVendors = async () => {
  try {
    console.log('🏢 [DEBUG] Loading existing vendors from database...')
    
    // Load all APPROVED vendors from the vendors table via vendor-core API
    const response = await api.get('/vendor-core/vendors/', {
      params: {
        status: 'APPROVED'
      },
      headers: getAuthHeaders()
    })
    const data = response.data
    console.log('✅ [DEBUG] Loaded vendors response:', data)
    
    // Handle different response formats
    let vendors = []
    if (data && typeof data === 'object') {
      if (data.vendors && Array.isArray(data.vendors)) {
        vendors = data.vendors
      } else if (data.success && data.vendors && Array.isArray(data.vendors)) {
        vendors = data.vendors
      } else if (Array.isArray(data)) {
        vendors = data
      } else if (data.data && Array.isArray(data.data)) {
        vendors = data.data
      } else if (data.results && Array.isArray(data.results)) {
        vendors = data.results
      }
    }
    
    console.log(`📊 [DEBUG] Found ${vendors.length} approved vendors`)
    
    // Load primary contacts for each vendor from vendor_contacts table
    const vendorsWithContacts = []
    for (const vendor of vendors) {
      try {
        console.log(`📞 [DEBUG] Fetching primary contact for vendor ${vendor.vendor_id} (${vendor.company_name})`)
        
        // Fetch primary contact from vendor_contacts table via vendor-core API
        // Filter by contact_type='PRIMARY' to get the primary contact
        const contactResponse = await api.get('/vendor-core/vendor-contacts/', {
          params: {
            vendor_id: vendor.vendor_id,
            contact_type: 'PRIMARY',
            is_active: 1
          },
          headers: getAuthHeaders()
        })
        
        const contactData = contactResponse.data
        console.log(`✅ [DEBUG] Contact data for vendor ${vendor.vendor_id}:`, contactData)
        
        const primaryContact = normalizeContactResponse(contactData, vendor.vendor_id)
        
        // Map vendor with primary contact information
        const vendorWithContact = {
          ...vendor,
          // Primary contact information from vendor_contacts table
          primary_contact: primaryContact,
          contact_name: primaryContact ? `${primaryContact.first_name || ''} ${primaryContact.last_name || ''}`.trim() : 'No contact',
          email: primaryContact ? primaryContact.email : 'No email',
          phone: primaryContact ? (primaryContact.mobile || primaryContact.phone || 'No phone') : 'No phone',
          contact_designation: primaryContact ? primaryContact.designation : '',
          contact_department: primaryContact ? primaryContact.department : '',
          // Vendor information from vendors table
          company_name: vendor.company_name || 'Unknown Company',
          website: vendor.website || '',
          headquarters_country: vendor.headquarters_country || 'Unknown',
          industry_sector: vendor.industry_sector || 'N/A',
          business_type: vendor.business_type || 'N/A',
          risk_level: vendor.risk_level || 'Unknown',
          annual_revenue: vendor.annual_revenue || 0,
          employee_count: vendor.employee_count || 0,
          // Initialize empty arrays for capabilities and certifications if not present
          capabilities: vendor.capabilities ? (Array.isArray(vendor.capabilities) ? vendor.capabilities : []) : [],
          certifications: vendor.certifications ? (Array.isArray(vendor.certifications) ? vendor.certifications : []) : [],
          // Calculated/display fields
          match_score: vendor.match_score || 0,
          rating: calculateVendorRating(vendor),
          experience_years: calculateExperienceYears(vendor.onboarding_date, vendor.incorporation_date),
          status: vendor.status || 'APPROVED',
          // UI state for expandable list view
          expanded: false,
          // Match breakdown for tooltip (will be populated by calculateMatchScores)
          match_breakdown: null,
          showBreakdown: false
        }
        
        vendorsWithContacts.push(vendorWithContact)
        console.log(`✅ [DEBUG] Processed vendor: ${vendorWithContact.company_name} with contact: ${vendorWithContact.email}`)
        
      } catch (contactError) {
        console.warn(`⚠️ [DEBUG] Failed to load contact for vendor ${vendor.vendor_id}:`, contactError)
        
        // Add vendor without contact information
        vendorsWithContacts.push({
          ...vendor,
          primary_contact: null,
          contact_name: 'No contact',
          email: 'No email',
          phone: 'No phone',
          contact_designation: '',
          contact_department: '',
          company_name: vendor.company_name || 'Unknown Company',
          website: vendor.website || '',
          headquarters_country: vendor.headquarters_country || 'Unknown',
          industry_sector: vendor.industry_sector || 'N/A',
          business_type: vendor.business_type || 'N/A',
          risk_level: vendor.risk_level || 'Unknown',
          annual_revenue: vendor.annual_revenue || 0,
          employee_count: vendor.employee_count || 0,
          capabilities: vendor.capabilities ? (Array.isArray(vendor.capabilities) ? vendor.capabilities : []) : [],
          certifications: vendor.certifications ? (Array.isArray(vendor.certifications) ? vendor.certifications : []) : [],
          match_score: vendor.match_score || 0,
          rating: calculateVendorRating(vendor),
          experience_years: calculateExperienceYears(vendor.onboarding_date, vendor.incorporation_date),
          status: vendor.status || 'APPROVED',
          // UI state for expandable list view
          expanded: false,
          // Match breakdown for tooltip (will be populated by calculateMatchScores)
          match_breakdown: null,
          showBreakdown: false
        })
      }
    }
    
    console.log(`✅ [DEBUG] Successfully processed ${vendorsWithContacts.length} vendors with contact information`)
    
    if (vendorsWithContacts.length > 0) {
      existingVendors.value = vendorsWithContacts
      updateTabCounts()
      
      // Calculate match scores for all vendors
      await calculateMatchScores(vendorsWithContacts.map(v => v.vendor_id))
      
      success("Vendors Loaded", `Loaded ${vendorsWithContacts.length} approved vendor(s) with contact information from database`)
    } else {
      console.warn('⚠️ [DEBUG] No vendors found in database')
      existingVendors.value = []
      error("No Vendors Found", "No approved vendors found in the database. Please add vendors first.")
    }
    
  } catch (err) {
    console.error('❌ [DEBUG] Error loading vendors:', err)
    
    // Clear existing vendors on error
    existingVendors.value = []
    
    // Show specific error messages
    if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error') || err.message?.includes('fetch') || err.message?.includes('ERR_CONNECTION_REFUSED')) {
      error("Server Unavailable", "Cannot connect to the backend server. Please ensure the Django server is running on the correct port.")
    } else if (err.response?.status === 404) {
      error("API Not Found", "The vendor API endpoint is not available. Please check the backend configuration.")
    } else if (err.response?.status === 500) {
      error("Server Error", `Internal server error: ${err.response?.data?.message || 'Unknown error'}`)
    } else {
      error("Failed to Load Vendors", err.response?.data?.message || err.message || "Unknown error occurred while fetching vendors.")
    }
  }
}

// Helper function to calculate vendor rating
const calculateVendorRating = (vendor: any): number => {
  // If rating exists, use it
  if (vendor.rating) return vendor.rating
  
  // Otherwise calculate based on available data
  let rating = 3.0 // Default rating
  
  // Increase rating based on criteria
  if (vendor.risk_level === 'LOW') rating += 1.0
  else if (vendor.risk_level === 'MEDIUM') rating += 0.5
  
  if (vendor.preferred_vendor_flag) rating += 0.5
  if (vendor.is_critical_vendor) rating += 0.3
  if (vendor.sustainability_rating) rating += 0.2
  
  return Math.min(rating, 5.0)
}

// Helper function to calculate experience years
const calculateExperienceYears = (onboardingDate: string | null, incorporationDate: string | null): number => {
  const referenceDate = onboardingDate || incorporationDate
  if (!referenceDate) return 0
  
  try {
    const date = new Date(referenceDate)
    const now = new Date()
    const years = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24 * 365.25))
    return Math.max(years, 0)
  } catch {
    return 0
  }
}

const handleGenerateURLs = async () => {
  if (allSelectedVendors.value.total === 0) {
    error("No vendors selected", "Please select at least one vendor to proceed.")
    return
  }
  
  try {
    console.log('🚀 [DEBUG] Preparing vendors for Phase 4...')
    console.log('📊 [DEBUG] Selected vendors:', allSelectedVendors.value)
    
    // Prepare unified vendor data for the next phase with complete information including primary contacts
    const allVendors = {
      existing: allSelectedVendors.value.existing.map(vendor => ({
        vendor_id: parseInt(vendor.vendor_id), // Ensure vendor_id is a number
        company_name: vendor.company_name,
        vendor_type: 'existing',
        is_matched_vendor: true,
        // Primary contact information from vendor_contacts table
        contact_info: vendor.primary_contact ? {
          contact_id: vendor.primary_contact.contact_id,
          first_name: vendor.primary_contact.first_name,
          last_name: vendor.primary_contact.last_name,
          email: vendor.primary_contact.email,
          phone: vendor.primary_contact.phone,
          mobile: vendor.primary_contact.mobile,
          designation: vendor.primary_contact.designation,
          department: vendor.primary_contact.department,
          contact_type: vendor.primary_contact.contact_type,
          is_primary: vendor.primary_contact.is_primary
        } : null,
        // Quick access fields
        contact_name: getPrimaryContactName(vendor) || '',
        contact_email: getPrimaryContactEmail(vendor) || '',
        contact_phone: getPrimaryContactPhone(vendor) || '',
        contact_designation: getPrimaryContactDesignation(vendor) || '',
        contact_department: getPrimaryContactDepartment(vendor) || '',
        // Include all relevant vendor data from vendors table
        capabilities: vendor.capabilities || [],
        certifications: vendor.certifications || [],
        rating: vendor.rating || 0,
        match_score: vendor.match_score || 0,
        headquarters_country: vendor.headquarters_country || '',
        website: vendor.website || '',
        experience_years: vendor.experience_years || 0,
        employee_count: vendor.employee_count || 0,
        risk_level: vendor.risk_level || 'Unknown',
        business_type: vendor.business_type || 'N/A',
        industry_sector: vendor.industry_sector || 'N/A',
        annual_revenue: vendor.annual_revenue || 0,
        status: vendor.status || 'APPROVED'
      })),
      manual: allSelectedVendors.value.manual.map(vendor => ({
        id: vendor.id,
        company_name: vendor.company_name,
        vendor_name: vendor.vendor_name,
        vendor_email: vendor.vendor_email,
        vendor_phone: vendor.vendor_phone,
        website: vendor.website || '',
        industry_sector: vendor.industry_sector || '',
        description: vendor.description || '',
        vendor_type: 'manual',
        is_matched_vendor: false
      })),
      bulk: allSelectedVendors.value.bulk.map(vendor => ({
        unmatched_id: vendor.unmatched_id,
        company_name: vendor.company_name,
        vendor_name: vendor.vendor_name,
        vendor_email: vendor.vendor_email,
        vendor_phone: vendor.vendor_phone,
        website: vendor.website || '',
        industry_sector: vendor.industry_sector || '',
        description: vendor.description || '',
        vendor_type: 'bulk',
        is_matched_vendor: false
      })),
      total: allSelectedVendors.value.total
    }
    
    // Store the selected vendors for Phase 4
    localStorage.setItem('selectedVendors', JSON.stringify(allVendors))
    localStorage.setItem('selectedRFP', JSON.stringify(selectedRFP.value))
    
    console.log('💾 [DEBUG] Stored vendors in localStorage:', allVendors)
    console.log('💾 [DEBUG] Stored RFP in localStorage:', selectedRFP.value)
    
    // Verify the data was stored correctly
    const storedVendors = localStorage.getItem('selectedVendors')
    const storedRFP = localStorage.getItem('selectedRFP')
    console.log('✅ [DEBUG] Verification - Stored vendors:', storedVendors)
    console.log('✅ [DEBUG] Verification - Stored RFP:', storedRFP)
    
    // Navigate to next phase - Phase 4 will handle contact fetching and invitation creation
    success("Ready for Next Phase", `All ${allSelectedVendors.value.total} vendors are ready for contact review and invitation distribution.`)
    
    // Navigate to Phase 4
    setTimeout(() => {
      window.location.href = '/rfp-url-generation'
    }, 1000)
    
  } catch (err) {
    console.error('❌ [DEBUG] Error preparing for next phase:', err)
    error("Failed to prepare for next phase", "An error occurred while preparing vendor data.")
  }
}

// Download vendor upload template
const downloadVendorTemplate = () => {
  try {
    // Create CSV content with headers and sample data
    const csvContent = `company_name,vendor_name,vendor_email,vendor_phone,website,industry_sector,description
Acme Corporation,John Doe,john.doe@acme.com,+1-555-0101,https://www.acme.com,Technology,Leading provider of enterprise software solutions
Tech Solutions Inc,Jane Smith,jane.smith@techsolutions.com,+1-555-0102,https://www.techsolutions.com,IT Services,Full-service IT consulting and implementation
Global Systems Ltd,Mike Johnson,mike.johnson@globalsystems.com,+1-555-0103,https://www.globalsystems.com,Software,Cloud-based business management solutions`

    // Create a Blob with the CSV content
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    
    // Create a link element to trigger download
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.href = url
    link.download = 'vendor_upload_template.csv'
    document.body.appendChild(link)
    link.click()
    
    // Clean up
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    success("Template Downloaded", "Vendor upload template has been downloaded successfully.")
  } catch (err) {
    console.error('Error downloading template:', err)
    error("Download Failed", "Failed to download the vendor upload template.")
  }
}

// Export vendor list to CSV
const handleExportList = () => {
  try {
    // Get the vendors to export (filtered vendors)
    const vendorsToExport = filteredExistingVendors.value || []
    
    if (vendorsToExport.length === 0) {
      error("No Vendors to Export", "There are no vendors available to export. Please load vendors first.")
      return
    }
    
    // Create CSV headers
    const headers = [
      'Company Name',
      'Contact Name',
      'Email',
      'Phone',
      'Website',
      'Country',
      'Rating',
      'Match Score',
      'Experience Years',
      'Employee Count',
      'Risk Level',
      'Business Type',
      'Industry Sector',
      'Annual Revenue',
      'Capabilities',
      'Certifications',
      'Status'
    ]
    
    // Convert vendors to CSV rows with primary contact information
    const csvRows = vendorsToExport.map(vendor => {
      return [
        vendor.company_name || '',
        getPrimaryContactName(vendor) || '',  // Primary contact name from vendor_contacts table
        getPrimaryContactEmail(vendor) || '',  // Primary contact email from vendor_contacts table
        getPrimaryContactPhone(vendor) || '',  // Primary contact phone from vendor_contacts table
        vendor.website || '',
        vendor.headquarters_country || '',
        vendor.rating || 'N/A',
        `${vendor.match_score || 0}%`,
        vendor.experience_years || 0,
        vendor.employee_count || 0,
        vendor.risk_level || 'Unknown',
        vendor.business_type || 'N/A',
        vendor.industry_sector || 'N/A',
        vendor.annual_revenue ? formatCurrency(vendor.annual_revenue) : 'N/A',
        (vendor.capabilities || []).join('; '),
        (vendor.certifications || []).join('; '),
        vendor.status || 'APPROVED'
      ].map(field => {
        // Escape commas and quotes in CSV fields
        const fieldStr = String(field)
        if (fieldStr.includes(',') || fieldStr.includes('"') || fieldStr.includes('\n')) {
          return `"${fieldStr.replace(/"/g, '""')}"`
        }
        return fieldStr
      })
    })
    
    // Combine headers and rows
    const csvContent = [
      headers.join(','),
      ...csvRows.map(row => row.join(','))
    ].join('\n')
    
    // Create a Blob with the CSV content
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    
    // Create a link element to trigger download
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.href = url
    
    // Generate filename with timestamp
    const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    const rfpNumber = selectedRFP.value?.rfp_number || 'RFP'
    link.download = `vendor_list_${rfpNumber}_${timestamp}.csv`
    
    document.body.appendChild(link)
    link.click()
    
    // Clean up
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    
    success("Export Successful", `Successfully exported ${vendorsToExport.length} vendor(s) to CSV file.`)
  } catch (err) {
    console.error('Error exporting vendor list:', err)
    error("Export Failed", "Failed to export vendor list. Please try again.")
  }
}

// Load selected RFP on component mount
onMounted(async () => {
  await loggingService.logPageView('RFP', 'Phase 3 - Vendor Selection')
  try {
    console.log('🚀 [DEBUG] Phase 3 component mounted, starting initialization...')
    
    const rfpData = localStorage.getItem('selectedRFP')
    if (rfpData) {
      try {
        selectedRFP.value = JSON.parse(rfpData)
        console.log('📋 [DEBUG] Loaded RFP from localStorage:', selectedRFP.value)
      } catch (error) {
        console.error('❌ [DEBUG] Error parsing RFP data:', error)
        error("Invalid RFP Data", "Failed to load RFP data from localStorage. Please select an RFP first.")
        return
      }
    } else {
      error("No RFP Selected", "No RFP data found. Please select an RFP first.")
      return
    }
    
    // Load real vendors from database only
    console.log('🚀 [DEBUG] Loading vendors from database...')
    await loadExistingVendors()
    
    console.log('✅ [DEBUG] Phase 3 component initialization complete')
  } catch (error) {
    console.error('❌ [DEBUG] Error in onMounted:', error)
    error("Initialization Failed", "Failed to initialize Phase 3. Please refresh the page and try again.")
  }
})

// No mock data - only load from database
</script>

<style scoped>
.phase-card {
  @apply bg-white border border-gray-200 rounded-lg shadow-sm;
}

.vendor-card {
  @apply bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow;
}

.status-badge.active {
  @apply bg-green-100 text-green-800 border-green-200;
}

.status-badge.awarded {
  @apply bg-green-100 text-green-800 border-green-200;
}

.status-badge.evaluation {
  @apply bg-yellow-100 text-yellow-800 border-yellow-200;
}

.status-badge.draft {
  @apply bg-gray-100 text-gray-800 border-gray-200;
}

.gradient-primary {
  @apply bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-in {
  animation: slideDown 0.2s ease-out;
}
</style>
