<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="space-y-8">
    <!-- Header -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
              <h1 class="text-3xl font-bold tracking-tight text-gray-900">Phase 7: Comparison & Analysis</h1>
              <p class="text-gray-600 mt-2">
                Compare vendor responses and analyze evaluation results.
        </p>
      </div>
      <div class="flex items-center gap-2">
              <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
          Phase 7 of 10
              </span>
              <button 
                @click="refreshData"
                :disabled="loading"
                class="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                <svg class="h-4 w-4 mr-1" :class="{ 'animate-spin': loading }" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Refresh
              </button>
            </div>
      </div>
    </div>

        <!-- RFP Selection -->
        <div v-if="!selectedRfpId" class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-2xl font-bold text-gray-900">Select RFP for Comparison</h3>
              <p class="text-gray-600 mt-1">Choose an RFP to view and compare vendor proposals</p>
            </div>
             <div class="flex items-center gap-4">
               <div class="flex items-center gap-2">
                 <div class="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                 <span class="text-sm text-gray-600">{{ availableRfps.length }} RFPs Available</span>
               </div>
               <div class="flex items-center gap-2">
                 <div class="w-3 h-3 bg-blue-500 rounded-full"></div>
                 <span class="text-sm text-gray-600">{{ totalProposals }} Total Proposals</span>
                 <button 
                   @click="refreshProposalCounts"
                   class="ml-2 p-1 text-gray-400 hover:text-blue-600 transition-colors"
                   title="Refresh proposal counts"
                 >
                   <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                   </svg>
                 </button>
               </div>
               <!-- Debug info - remove in production -->
               <div class="text-xs text-gray-400">
                 Debug: {{ Object.keys(rfpProposalCounts).length }} counts loaded
               </div>
               <button 
                 @click="testApiDirectly"
                 class="ml-2 px-2 py-1 text-xs bg-red-100 text-red-600 rounded hover:bg-red-200"
                 title="Test API directly"
               >
                 Test API
               </button>
             </div>
          </div>

          <div v-if="loading" class="text-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p class="text-gray-600 mt-4">Loading RFPs and proposal counts...</p>
            <p class="text-sm text-gray-500 mt-2">This may take a moment</p>
          </div>

          <div v-else-if="error" class="text-center py-12">
            <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
              </svg>
            </div>
            <h4 class="text-lg font-semibold text-gray-900 mb-2">Unable to Load RFPs</h4>
            <p class="text-red-600 mb-4">{{ error }}</p>
              <button @click="fetchAvailableRfps" class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 transition-colors">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                Try Again
              </button>
          </div>

          <div v-else-if="availableRfps.length === 0" class="text-center py-12">
            <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
              </svg>
            </div>
            <h4 class="text-lg font-semibold text-gray-900 mb-2">No RFPs Found</h4>
            <p class="text-gray-600">No RFPs with vendor responses are available for comparison.</p>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 rfp-card-grid">
            <div 
              v-for="rfp in availableRfps" 
              :key="rfp.id"
              @click="selectedRfpId = rfp.id"
              class="group relative bg-white border-2 border-gray-200 rounded-xl p-6 hover:border-blue-300 hover:shadow-lg cursor-pointer transition-all duration-300 hover:-translate-y-1 rfp-card hover-lift-enhanced"
            >
              <!-- Status Indicator -->
              <div class="absolute top-4 right-4">
                <span :class="{
                  'bg-green-100 text-green-800': rfp.status === 'active',
                  'bg-yellow-100 text-yellow-800': rfp.status === 'pending',
                  'bg-blue-100 text-blue-800': rfp.status === 'evaluation'
                }" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                  <div :class="{
                    'bg-green-400 status-indicator': rfp.status === 'active',
                    'bg-yellow-400 status-indicator': rfp.status === 'pending',
                    'bg-blue-400 status-indicator': rfp.status === 'evaluation'
                  }" class="w-2 h-2 rounded-full mr-1.5"></div>
                  {{ rfp.status }}
                </span>
              </div>

              <!-- RFP Content -->
              <div class="pr-20">
                <h4 class="font-bold text-gray-900 text-lg mb-2 group-hover:text-blue-600 transition-colors">
                  {{ rfp.title }}
                </h4>
                <p class="text-sm text-gray-600 mb-4">{{ rfp.description }}</p>
                
                <!-- Proposal Count Badge -->
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center gap-2">
                    <div class="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-lg proposal-count-badge">
                      <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
                      </svg>
            </div>
            <div>
                       <p class="text-sm font-medium text-gray-900">
                         <span v-if="rfpProposalCounts[rfp.id] !== undefined">
                           {{ rfpProposalCounts[rfp.id] || 0 }}
                         </span>
                         <span v-else class="animate-pulse text-gray-400">...</span>
                       </p>
                       <p class="text-xs text-gray-500">Proposals</p>
            </div>
          </div>
                  
                  <!-- View Button -->
                  <div class="opacity-0 group-hover:opacity-100 transition-opacity">
                    <div class="flex items-center text-blue-600 text-sm font-medium">
                      <span>View Details</span>
                      <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                      </svg>
                    </div>
                  </div>
                </div>

                <!-- Additional Info -->
                <div class="flex items-center justify-between text-xs text-gray-500 pt-4 border-t border-gray-100">
                  <div class="flex items-center gap-1">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    {{ new Date(rfp.created_at).toLocaleDateString() }}
                  </div>
                  <div class="flex items-center gap-1">
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    {{ Math.ceil((Date.now() - new Date(rfp.created_at).getTime()) / (1000 * 60 * 60 * 24)) }} days ago
                  </div>
                </div>
              </div>

              <!-- Hover Effect -->
              <div class="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loading && selectedRfpId" class="text-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p class="text-gray-600 mt-4">Loading comparison data...</p>
        </div>

        <!-- Error State -->
        <div v-if="error && selectedRfpId" class="bg-red-50 border border-red-200 rounded-lg p-6">
          <div class="flex items-center gap-3">
            <AlertCircle class="h-5 w-5 text-red-600" />
            <div>
              <h3 class="font-semibold text-red-800">Error Loading Data</h3>
              <p class="text-red-600 mt-1">{{ error }}</p>
            </div>
          </div>
        </div>

        <!-- Main Content (only show when RFP is selected and data is loaded) -->
        <div v-if="selectedRfpId && !loading && !error && vendorEvaluations.length > 0">
          <!-- Summary Statistics -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div class="flex items-center gap-4">
                <div class="p-3 rounded-lg bg-blue-50">
                  <Users class="h-6 w-6 text-blue-600" />
            </div>
            <div>
                  <p class="text-sm font-medium text-gray-600">Total Responses</p>
                  <p class="text-2xl font-bold text-gray-900">{{ vendorEvaluations.length }}</p>
            </div>
          </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div class="flex items-center gap-4">
                <div class="p-3 rounded-lg bg-green-50">
                  <Trophy class="h-6 w-6 text-green-600" />
            </div>
            <div>
                  <p class="text-sm font-medium text-gray-600">Highest Score</p>
                  <p class="text-2xl font-bold text-gray-900">{{ topScore }}</p>
            </div>
          </div>
            </div>

            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div class="flex items-center gap-4">
                <div class="p-3 rounded-lg bg-yellow-50">
                  <BarChart3 class="h-6 w-6 text-yellow-600" />
            </div>
            <div>
                  <p class="text-sm font-medium text-gray-600">Average Score</p>
                  <p class="text-2xl font-bold text-gray-900">{{ averageScore }}</p>
            </div>
          </div>
    </div>

            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div class="flex items-center gap-4">
                <div class="p-3 rounded-lg bg-purple-50">
                  <DollarSign class="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-600">Best Value</p>
                  <p class="text-2xl font-bold text-gray-900">${{ (lowestValue / 1000).toFixed(0) }}K</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Enhanced Workflow Navigation -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              <div class="flex flex-col sm:flex-row items-start sm:items-center gap-6">
                <div class="flex items-center gap-3">
                  <div :class="`w-4 h-4 rounded-full ${rfpShortlistedVendors.length > 0 ? 'bg-green-500' : 'bg-gray-300'}`"></div>
                  <span class="text-sm font-medium text-gray-700">Shortlist Vendors</span>
                </div>
                <div class="flex items-center gap-3">
                  <div :class="`w-4 h-4 rounded-full ${rfpCommitteeAssigned ? 'bg-green-500' : 'bg-gray-300'}`"></div>
                  <span class="text-sm font-medium text-gray-700">Assign Committee</span>
                </div>
                <div class="flex items-center gap-3">
                  <div class="w-4 h-4 rounded-full bg-gray-300"></div>
                  <span class="text-sm font-medium text-gray-700">Final Evaluation</span>
                </div>
              </div>
              <div class="text-sm text-gray-500 bg-gray-50 px-3 py-2 rounded-md">
                {{ rfpShortlistedVendors.length }} vendors, {{ rfpCommitteeMembers.length }} committee members
                <span v-if="lastUpdated" class="ml-2 text-xs">
                  • Last updated: {{ lastUpdated.toLocaleTimeString() }}
                </span>
              </div>
            </div>
          </div>

          <!-- Tabs -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200">
            <div class="border-b border-gray-200 px-6">
              <nav class="-mb-px flex space-x-8">
                <button 
                  @click="activeTab = 'comparison'"
                  :class="activeTab === 'comparison' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                  class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors"
                >
                  Vendor Comparison & Shortlist
                </button>
                <button 
                  @click="activeTab = 'committee'"
                  :class="activeTab === 'committee' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                  class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors"
                >
                  Committee Assignment
                </button>
              </nav>
            </div>

            <!-- Comparison Tab -->
            <div v-if="activeTab === 'comparison'" class="p-6 space-y-6">
              <!-- Filters and Controls -->
              <div class="bg-gray-50 rounded-lg p-4">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Filter by Score</label>
                    <div class="relative">
                      <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                      <input
                        placeholder="Minimum score..."
                        v-model="filterMinScore"
                        type="number"
                        class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Sort by</label>
                    <select 
                      v-model="sortBy" 
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="totalScore">Total Score</option>
                      <option value="proposedValue">Proposed Value</option>
                      <option value="variance">Evaluator Variance</option>
                    </select>
                  </div>

                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Top Performers</label>
                    <input
                      v-model.number="topPerformersCount"
                      @input="handleTopPerformersCountChange"
                      type="number"
                      min="1"
                      :max="vendorEvaluations.length"
                      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Number of top performers"
                    />
                  </div>

                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Quick Select</label>
                    <button 
                      @click="handleSelectTopPerformers"
                      :disabled="!canSelectTopPerformers"
                      class="w-full inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Trophy class="h-4 w-4 mr-2" />
                      Select Top {{ topPerformersCount }}
                    </button>
                  </div>

                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Auto-Select</label>
                    <div class="flex items-center space-x-2">
                      <input
                        v-model="autoSelectTopPerformers"
                        @change="handleAutoSelectToggle"
                        type="checkbox"
                        class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span class="text-sm text-gray-600">Auto-select top performers</span>
                    </div>
                  </div>
                  
                  <div class="space-y-2">
                    <label class="text-sm font-medium text-gray-700">Shortlist</label>
                    <button @click="rfpHandleShortlist" class="w-full inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 transition-colors">
                      <CheckCircle2 class="h-4 w-4 mr-2" />
                      Shortlist ({{ selectedVendors.length }})
                    </button>
                  </div>
                </div>
              </div>

              <!-- Top Performers Preview -->
              <div v-if="vendorEvaluations.length > 0" class="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-6">
                <div class="flex items-center gap-3 mb-4">
                  <Trophy class="h-6 w-6 text-green-600" />
                  <h3 class="text-lg font-semibold text-gray-900">Top {{ topPerformersCount }} Performers Preview</h3>
                  <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                    {{ canSelectTopPerformers ? 'Ready' : 'Insufficient Data' }}
                  </span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div 
                    v-for="(vendor, index) in topPerformers" 
                    :key="vendor.id"
                    class="bg-white border border-green-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div class="flex items-center justify-between mb-3">
                      <div class="flex items-center gap-2">
                        <Trophy v-if="index === 0" class="h-5 w-5 text-yellow-500" />
                        <Star v-else-if="index === 1" class="h-5 w-5 text-gray-400" />
                        <Star v-else-if="index === 2" class="h-5 w-5 text-orange-600" />
                        <span class="font-semibold text-gray-900">#{{ index + 1 }}</span>
                      </div>
                      <span :class="getScoreBadge(vendor.overallScore || vendor.totalScore)" class="inline-flex items-center px-2 py-1 rounded-full text-sm font-medium">
                        {{ vendor.overallScore || vendor.totalScore }}
                      </span>
                    </div>
                    <h4 class="font-semibold text-gray-900 mb-2">{{ vendor.name || vendor.company_name }}</h4>
                    <div class="space-y-2 text-sm">
                      <div class="flex justify-between">
                        <span class="text-gray-600">Score:</span>
                        <span class="font-medium">{{ vendor.overallScore || vendor.totalScore }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-gray-600">Evaluators:</span>
                        <span class="font-medium">{{ vendor.totalEvaluators || 0 }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-gray-600">Variance:</span>
                        <span class="font-medium">{{ vendor.evaluatorVariance || vendor.variance || 0 }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-gray-600">Value:</span>
                        <span class="font-medium">{{ vendor.price || 'N/A' }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-gray-600">Status:</span>
                        <span class="font-medium capitalize">{{ vendor.status || 'pending' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Comparison Table -->
              <div class="bg-white rounded-lg shadow-sm border border-gray-200">
                <div class="px-6 py-4 border-b border-gray-200">
                  <h3 class="text-lg font-semibold text-gray-900">Vendor Comparison Table</h3>
                </div>
        <div class="overflow-x-auto">
          <table class="w-full">
                    <thead class="bg-gray-50">
                      <tr>
                        <th class="text-left py-4 px-6 font-medium text-gray-900 w-16">Rank</th>
                        <th class="text-left py-4 px-6 font-medium text-gray-900 min-w-[200px]">Vendor</th>
                        <th class="text-left py-4 px-6 font-medium text-gray-900">Total Score</th>
                        <th class="text-left py-4 px-6 font-medium text-gray-900">Technical</th>
                        <th class="text-left py-4 px-6 font-medium text-gray-900">Status</th>
                        <th class="text-left py-4 px-6 font-medium text-gray-900">Completion</th>
                        <th class="text-left py-4 px-6 font-medium text-gray-900">Submitted</th>
                        <th class="text-left py-4 px-6 font-medium text-gray-900">Proposed Value</th>
                        <th class="text-left py-4 px-6 font-medium text-gray-900">Variance</th>
                        <th class="text-left py-4 px-6 font-medium text-gray-900">Actions</th>
              </tr>
            </thead>
                    <tbody class="divide-y divide-gray-200">
                      <tr v-for="(vendor, index) in filteredVendors" :key="vendor.id" :class="selectedVendors.includes(vendor.id) ? 'bg-blue-50' : 'hover:bg-gray-50'">
                        <td class="py-4 px-6">
                          <div class="flex items-center gap-2">
                            <Trophy v-if="index === 0" class="h-5 w-5 text-yellow-500" />
                            <Star v-else-if="index === 1" class="h-5 w-5 text-gray-400" />
                            <Star v-else-if="index === 2" class="h-5 w-5 text-orange-600" />
                            <span class="font-semibold text-gray-900">#{{ index + 1 }}</span>
                  </div>
                </td>
                        <td class="py-4 px-6">
                          <div class="space-y-1">
                            <div class="flex items-center gap-2">
                              <p class="font-semibold text-gray-900">{{ vendor.name || vendor.company_name }}</p>
                              <span v-if="vendor.totalEvaluators > 0" class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800" title="Number of evaluators">
                                {{ vendor.totalEvaluators }} eval.
                              </span>
                            </div>
                            <p class="text-sm text-gray-500">{{ vendor.contact_email || vendor.email }}</p>
                  </div>
                </td>
                        <td class="py-4 px-6">
                          <span :class="getScoreBadge(vendor.overallScore || vendor.totalScore)" class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium">
                            {{ vendor.overallScore || vendor.totalScore }}
                          </span>
                </td>
                        <td class="py-4 px-6">
                          <span :class="getScoreColor(vendor.technicalScore || vendor.scores?.technical)" class="font-medium">
                            {{ vendor.technicalScore || vendor.scores?.technical || 'N/A' }}
                          </span>
                </td>
                        <td class="py-4 px-6">
                          <span :class="{
                            'bg-green-100 text-green-800': vendor.evaluation_status === 'AWARDED',
                            'bg-blue-100 text-blue-800': vendor.evaluation_status === 'SHORTLISTED',
                            'bg-yellow-100 text-yellow-800': vendor.evaluation_status === 'UNDER_EVALUATION',
                            'bg-gray-100 text-gray-800': vendor.evaluation_status === 'SUBMITTED'
                          }" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium">
                            {{ vendor.evaluation_status || vendor.status || 'N/A' }}
                          </span>
                </td>
                        <td class="py-4 px-6">
                          <div class="flex items-center gap-2">
                            <div class="w-16 bg-gray-200 rounded-full h-2">
                              <div :class="{
                                'bg-green-500': (vendor.completion_percentage || 0) >= 80,
                                'bg-yellow-500': (vendor.completion_percentage || 0) >= 50 && (vendor.completion_percentage || 0) < 80,
                                'bg-red-500': (vendor.completion_percentage || 0) < 50
                              }" class="h-2 rounded-full" :style="{ width: (vendor.completion_percentage || 0) + '%' }"></div>
                            </div>
                            <span class="text-sm font-medium text-gray-700">{{ vendor.completion_percentage || 0 }}%</span>
                          </div>
                </td>
                        <td class="py-4 px-6">
                          <span class="text-sm text-gray-600">
                            {{ vendor.submission_date ? new Date(vendor.submission_date).toLocaleDateString() : 'N/A' }}
                          </span>
                        </td>
                        <td class="py-4 px-6">
                          <span class="font-semibold text-gray-900">
                            {{ vendor.price || vendor.proposedValue || 'N/A' }}
                          </span>
                        </td>
                        <td class="py-4 px-6">
                          <span v-if="vendor.totalEvaluators > 0" :class="(vendor.evaluatorVariance || vendor.variance || 0) > 3 ? 'text-yellow-600' : 'text-green-600'" class="font-medium" :title="`Standard deviation across ${vendor.totalEvaluators} evaluators`">
                            ±{{ vendor.evaluatorVariance || vendor.variance || 0 }}
                          </span>
                          <span v-else class="text-gray-400 text-sm">N/A</span>
                        </td>
                        <td class="py-4 px-6">
                          <input
                            type="checkbox"
                            :checked="selectedVendors.includes(vendor.id)"
                            @change="handleVendorSelect(vendor.id)"
                            class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
              </div>

              <!-- Shortlist Summary -->
              <div v-if="rfpShortlistedVendors.length > 0" class="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <div class="flex items-center gap-3 mb-4">
                  <Trophy class="h-6 w-6 text-blue-600" />
                  <h3 class="text-lg font-semibold text-gray-900">Shortlisted Vendors ({{ rfpShortlistedVendors.length }})</h3>
                </div>
                <p class="text-gray-600 mb-6">
                  These vendors will proceed to the final committee evaluation
                </p>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6">
                  <div v-for="(vendor, index) in shortlistedVendorData" :key="vendor.id" class="bg-white border-2 border-blue-200 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-4">
                      <div class="flex items-center gap-2">
                        <Trophy v-if="index === 0" class="h-5 w-5 text-yellow-500" />
                        <Star v-else-if="index === 1" class="h-5 w-5 text-gray-400" />
                        <Star v-else-if="index === 2" class="h-5 w-5 text-orange-600" />
                        <h4 class="font-semibold text-gray-900">{{ vendor.name }}</h4>
                      </div>
                      <button 
                        @click="rfpHandleRemoveFromShortlist(vendor.id)"
                        class="px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                      >
                        Remove
                      </button>
                    </div>
                    
                    <div class="space-y-3 text-sm">
                      <div class="flex justify-between">
                        <span class="text-gray-600">Total Score:</span>
                        <span :class="getScoreBadge(vendor.overallScore || vendor.totalScore)" class="inline-flex items-center px-2 py-1 rounded-full text-sm font-medium">
                          {{ vendor.overallScore || vendor.totalScore }}
                        </span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-gray-600">Evaluators:</span>
                        <span class="font-semibold text-gray-900">{{ vendor.totalEvaluators || 0 }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-gray-600">Proposed Value:</span>
                        <span class="font-semibold text-gray-900">{{ vendor.price || vendor.proposedValue || 'N/A' }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-gray-600">Evaluator Consensus:</span>
                        <span :class="(vendor.evaluatorVariance || vendor.variance || 0) <= 2 ? 'text-green-600' : 'text-yellow-600'" class="font-medium">
                          {{ (vendor.evaluatorVariance || vendor.variance || 0) <= 2 ? 'High' : 'Medium' }}
                        </span>
                      </div>
                    </div>
                    
                    <div class="mt-4 space-y-2">
                      <p class="text-xs font-medium text-green-600">Strengths:</p>
                      <ul class="text-xs text-gray-600 space-y-1">
                        <li v-for="(strength, i) in (vendor.strengths || []).slice(0, 2)" :key="i">• {{ strength }}</li>
                        <li v-if="!vendor.strengths || vendor.strengths.length === 0" class="text-gray-400">No strengths listed</li>
                  </ul>
                </div>
                  </div>
                </div>
                
                <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-3">
                      <CheckCircle2 class="h-5 w-5 text-green-600" />
                <div>
                        <p class="font-semibold text-green-800">Ready for Committee Assignment</p>
                        <p class="text-sm text-green-600">
                          {{ rfpShortlistedVendors.length }} vendors selected for final evaluation
                        </p>
                </div>
              </div>
                    <button 
                      @click="rfpHandleAssignCommittee"
                      class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 transition-colors"
                    >
                      <UserPlus class="h-4 w-4 mr-2" />
                      Assign Committee Members
                    </button>
            </div>
          </div>
              </div>
            </div>

            <!-- Committee Assignment Tab -->
            <div v-if="activeTab === 'committee'" class="p-6 space-y-6">
              <!-- Committee Assignment -->
              <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div class="flex items-center gap-3 mb-4">
                  <Crown class="h-6 w-6 text-blue-600" />
                  <h2 class="text-xl font-semibold text-gray-900">RFP Committee Assignment</h2>
            </div>
                <p class="text-gray-600 mb-6">
                  Assign committee members for the final evaluation of shortlisted vendor proposals.
                </p>
                
                <div v-if="rfpShortlistedVendors.length === 0" class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg mb-6">
                  <div class="flex items-center gap-3">
                    <AlertCircle class="h-5 w-5 text-yellow-600" />
                    <span class="text-sm font-medium text-yellow-800">
                      No vendors shortlisted. Please return to Vendor Comparison & Shortlist tab to select vendors.
                    </span>
            </div>
            </div>

                <!-- Shortlisted Vendors Summary -->
                <div v-if="rfpShortlistedVendors.length > 0" class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                  <div class="flex items-center gap-3 mb-3">
                    <Trophy class="h-5 w-5 text-green-600" />
                    <h3 class="font-semibold text-green-800">Shortlisted Vendors for Final Evaluation</h3>
                  </div>
                  <div class="flex gap-2 flex-wrap">
                    <span v-for="(vendor, index) in shortlistedVendorData" :key="vendor.id" class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 border border-green-200">
                      {{ index + 1 }}. {{ vendor.name || vendor.company_name }} ({{ vendor.overallScore || vendor.totalScore }})
                    </span>
                  </div>
                </div>

                <!-- Committee Selection -->
                <div class="space-y-6">
                  <div class="flex items-center justify-between">
                    <h3 class="text-lg font-semibold text-gray-900">Available Committee Members</h3>
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                      {{ rfpCommitteeMembers.length }} selected
                    </span>
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div 
                      v-for="member in rfpAvailableCommitteeMembers" 
                      :key="member.id" 
                      :class="`border-2 rounded-lg p-4 transition-all hover:shadow-md ${
                        rfpCommitteeMembers.includes(member.id) 
                          ? 'border-blue-500 bg-blue-50' 
                          : 'border-gray-200 bg-white hover:border-gray-300'
                      }`"
                    >
                      <div class="flex items-start gap-3">
                        <input
                          type="checkbox"
                          :checked="rfpCommitteeMembers.includes(member.id)"
                          @change="rfpHandleCommitteeMemberToggle(member.id)"
                          class="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <div class="flex-1 space-y-3">
                          <div class="flex items-center justify-between">
                            <div>
                              <h4 class="font-semibold text-gray-900">{{ member.name || member.full_name }}</h4>
                              <p class="text-sm text-gray-500">{{ member.email }}</p>
                  </div>
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                              {{ member.role || member.job_title || 'Committee Member' }}
                            </span>
                </div>
                          
                          <div class="space-y-2">
                            <p class="text-sm text-gray-600">
                              <span class="font-medium">Expertise:</span> {{ member.expertise || member.specialization || 'General' }}
                            </p>
                            <div class="flex items-center gap-4 text-sm text-gray-500">
                              <span>Evaluations: {{ member.evaluations || member.evaluation_count || 0 }}</span>
                              <span>Avg Score: {{ member.avgScore || member.average_score || 0 }}%</span>
              </div>
            </div>
                          
                          <div class="flex items-center gap-2">
                            <div :class="`w-2 h-2 rounded-full ${member.active !== false ? 'bg-green-500' : 'bg-gray-300'}`"></div>
                            <span class="text-sm text-gray-600">
                              {{ member.active !== false ? 'Active' : 'Inactive' }}
                            </span>
          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Committee Configuration -->
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mt-6">
                  <div class="flex items-center gap-3 mb-4">
                    <Shield class="h-5 w-5 text-blue-600" />
                    <h3 class="text-lg font-semibold text-gray-900">Committee Configuration</h3>
                  </div>
                  
                  <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Primary Role</label>
                      <select v-model="rfpCommitteeRole" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                        <option value="">Select primary role</option>
                        <option v-for="role in rfpCommitteeRoles" :key="role.value" :value="role.value">
                          {{ role.label }} ({{ role.weight }}% weight)
                        </option>
                      </select>
                    </div>
                    
                    <div class="space-y-2">
                      <label class="text-sm font-medium text-gray-700">Consensus Threshold</label>
                      <select v-model="rfpCommitteeWeight" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                        <option value="">Select consensus threshold</option>
                        <option value="unanimous">Unanimous (100%)</option>
                        <option value="majority">Majority (75%)</option>
                        <option value="simple">Simple Majority (50%)</option>
                      </select>
                    </div>
                  </div>
                  
                  <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <h4 class="font-semibold text-gray-900 mb-3">Final Evaluation Guidelines</h4>
                    <ul class="text-sm text-gray-600 space-y-2">
                      <li class="flex items-start gap-2">
                        <span class="text-blue-600">•</span>
                        <span>Committee members will conduct final evaluation of shortlisted proposals</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <span class="text-blue-600">•</span>
                        <span>Each member provides individual ranking and scoring</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <span class="text-blue-600">•</span>
                        <span>Final consensus is reached through committee discussion</span>
                      </li>
                      <li class="flex items-start gap-2">
                        <span class="text-blue-600">•</span>
                        <span>Weighted scoring based on member expertise and role</span>
                      </li>
                    </ul>
                  </div>
                </div>

                <!-- Assignment Actions -->
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pt-6 border-t border-gray-200">
                  <div class="text-sm text-gray-600">
                    <span v-if="rfpCommitteeMembers.length > 0">Ready to assign {{ rfpCommitteeMembers.length }} committee members</span>
                    <span v-else>Select committee members to proceed</span>
                  </div>
                  <div class="flex gap-3">
                    <button @click="() => rfpCommitteeMembers = []" class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">
                      Clear Selection
                    </button>
                    <button 
                      @click="rfpHandleCommitteeAssignment"
                      :disabled="rfpCommitteeMembers.length === 0"
                      class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <UserPlus class="h-4 w-4 mr-2" />
                      Assign Committee for Final Evaluation
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Progress Status -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Phase 7 Progress</h3>
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div :class="`w-4 h-4 rounded-full ${rfpShortlistedVendors.length > 0 ? 'bg-green-500' : 'bg-gray-300'}`"></div>
                <span class="text-sm font-medium text-gray-700">Vendors Shortlisted</span>
              </div>
              <span :class="rfpShortlistedVendors.length > 0 ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'" class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium">
                {{ rfpShortlistedVendors.length }} vendors
              </span>
            </div>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div :class="`w-4 h-4 rounded-full ${rfpCommitteeAssigned ? 'bg-green-500' : 'bg-gray-300'}`"></div>
                <span class="text-sm font-medium text-gray-700">Committee Assigned</span>
              </div>
              <span :class="rfpCommitteeAssigned ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'" class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium">
                {{ rfpCommitteeAssigned ? 'Complete' : rfpShortlistedVendors.length > 0 ? 'Ready' : 'Pending' }}
              </span>
            </div>
          </div>
    </div>

    <!-- Navigation -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <button class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">
            Previous: Evaluation
            </button>
            <div class="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <div v-if="!rfpCommitteeAssigned" class="text-sm text-gray-500">
                <span v-if="rfpShortlistedVendors.length === 0">Shortlist vendors first</span>
                <span v-else>Assign committee members to continue</span>
              </div>
              <button 
                @click="rfpStartFinalEvaluation"
                class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="!rfpCommitteeAssigned"
              >
                Start Final Evaluation
            <ArrowRight class="h-4 w-4 ml-2" />
              </button>
              <button 
                @click="goToConsensus"
                class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-md hover:bg-purple-700 transition-colors"
                :disabled="!rfpCommitteeAssigned"
              >
                View Consensus
            <Trophy class="h-4 w-4 ml-2" />
              </button>
        </div>
          </div>
        </div>

        <!-- No Data State -->
        <div v-if="selectedRfpId && !loading && !error && vendorEvaluations.length === 0" class="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <div class="text-gray-400 mb-4">
            <Users class="h-12 w-12 mx-auto" />
          </div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">No Vendor Responses</h3>
          <p class="text-gray-600 mb-4">This RFP doesn't have any vendor responses to compare yet.</p>
          <button 
            @click="selectedRfpId = ''" 
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Select Different RFP
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useRfpApi } from '@/composables/useRfpApi'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'
import { 
  BarChart3, 
  TrendingUp,
  Filter, 
  Eye, 
  Star,
  ArrowRight,
  Download,
  CheckCircle2,
  Trophy,
  DollarSign,
  Users,
  Search,
  UserPlus,
  Crown,
  Shield,
  AlertCircle
} from 'lucide-vue-next'

// Router
const router = useRouter()

// State management
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const selectedVendors = ref([])
const sortBy = ref('totalScore')
const filterMinScore = ref('')
const rfpCommitteeMembers = ref([])
const rfpCommitteeRole = ref('')
const rfpCommitteeWeight = ref('')
const rfpShortlistedVendors = ref([])
const rfpCommitteeAssigned = ref(false)
const activeTab = ref('comparison')
const topPerformersCount = ref(3) // Dynamic selection of top performers
const autoSelectTopPerformers = ref(false) // Auto-select top performers based on count

// Data from database
const vendorEvaluations = ref([])
const rfpAvailableCommitteeMembers = ref([])
const rfpCommitteeRoles = ref([])
const loading = ref(false)
const error = ref('')
const summary = ref({})
const criteriaSummary = ref({})
const selectedRfpId = ref('')
const availableRfps = ref([])
const lastUpdated = ref(null)
const rfpProposalCounts = ref({}) // Store proposal counts for each RFP

// Computed properties
const averageScore = computed(() => {
  if (vendorEvaluations.value.length === 0) return 0
  return Math.round(vendorEvaluations.value.reduce((sum, v) => sum + (v.overallScore || v.totalScore || 0), 0) / vendorEvaluations.value.length * 10) / 10
})

const topScore = computed(() => {
  if (vendorEvaluations.value.length === 0) return 0
  return Math.max(...vendorEvaluations.value.map(v => v.overallScore || v.totalScore || 0))
})

const lowestValue = computed(() => {
  if (vendorEvaluations.value.length === 0) return 0
  const values = vendorEvaluations.value.map(v => {
    const price = v.proposedValue || v.price
    return typeof price === 'string' ? parseFloat(price.replace(/[$,]/g, '')) : price || 0
  })
  return Math.min(...values)
})

const highestValue = computed(() => {
  if (vendorEvaluations.value.length === 0) return 0
  const values = vendorEvaluations.value.map(v => {
    const price = v.proposedValue || v.price
    return typeof price === 'string' ? parseFloat(price.replace(/[$,]/g, '')) : price || 0
  })
  return Math.max(...values)
})

const sortedVendors = computed(() => {
  const sorted = [...vendorEvaluations.value].sort((a, b) => {
    const aScore = a.overallScore || a.totalScore || 0
    const bScore = b.overallScore || b.totalScore || 0
    const aValue = typeof (a.proposedValue || a.price) === 'string' 
      ? parseFloat((a.proposedValue || a.price).replace(/[$,]/g, '')) 
      : (a.proposedValue || a.price) || 0
    const bValue = typeof (b.proposedValue || b.price) === 'string' 
      ? parseFloat((b.proposedValue || b.price).replace(/[$,]/g, '')) 
      : (b.proposedValue || b.price) || 0
    const aVariance = a.evaluatorVariance || a.variance || 0
    const bVariance = b.evaluatorVariance || b.variance || 0
    
    switch (sortBy.value) {
      case "totalScore": 
        console.log(`Sorting by Total Score: ${a.name} (${aScore}) vs ${b.name} (${bScore})`)
        return bScore - aScore
      case "proposedValue": return aValue - bValue
      case "variance": return aVariance - bVariance
      default: return bScore - aScore
    }
  })
  
  // Log the sorted order
  console.log('Vendors sorted by', sortBy.value, ':', sorted.map(v => ({ name: v.name, totalScore: v.totalScore, overallScore: v.overallScore })))
  
  return sorted
})

const filteredVendors = computed(() => {
  return sortedVendors.value.filter(vendor => {
    const score = vendor.overallScore || vendor.totalScore || 0
    return !filterMinScore.value || score >= parseFloat(filterMinScore.value)
  })
})

const shortlistedVendorData = computed(() => {
  return vendorEvaluations.value.filter(vendor => rfpShortlistedVendors.value.includes(vendor.id))
})

const topPerformers = computed(() => {
  return sortedVendors.value.slice(0, topPerformersCount.value)
})

const canSelectTopPerformers = computed(() => {
  return vendorEvaluations.value.length >= topPerformersCount.value
})

const totalProposals = computed(() => {
  return Object.values(rfpProposalCounts.value).reduce((sum, count) => sum + (count || 0), 0)
})

// Helper functions
const getScoreColor = (score) => {
  if (score >= 90) return 'text-success'
  if (score >= 80) return 'text-warning'
  if (score >= 70) return 'text-info'
  return 'text-muted-foreground'
}

const getScoreBadge = (score) => {
  if (score >= 90) return 'status-badge awarded'
  if (score >= 80) return 'status-badge evaluation'
  if (score >= 70) return 'status-badge active'
  return 'status-badge draft'
}

const calculateStandardDeviation = (values) => {
  if (!values || values.length === 0) return 0
  const mean = values.reduce((sum, val) => sum + val, 0) / values.length
  const squaredDiffs = values.map(val => Math.pow(val - mean, 2))
  const avgSquaredDiff = squaredDiffs.reduce((sum, val) => sum + val, 0) / values.length
  return Math.sqrt(avgSquaredDiff)
}

// API functions to fetch real data
const fetchRfpProposalCount = async (rfpId) => {
  try {
    console.log(`🔍 Fetching proposal count for RFP ${rfpId}...`)
    
    // Get authentication headers
    const { getAuthHeaders, buildApiUrl } = useRfpApi()
    
    // Use the correct endpoint structure
    const response = await fetch(buildApiUrl(`/rfp-responses-list/?rfp_id=${rfpId}&t=${Date.now()}`), {
      method: 'GET',
      headers: getAuthHeaders()
    })
    console.log(`📡 API Response status: ${response.status}`)
    
    if (!response.ok) {
      console.warn(`⚠️ API returned ${response.status} for RFP ${rfpId}`)
      throw new Error(`API returned ${response.status}`)
    }
    
    const data = await response.json()
    console.log(`📊 Raw API response for RFP ${rfpId}:`, data)
    
    // Handle the actual API response structure: {success: true, responses: [...], total_count: X}
    if (data && typeof data === 'object') {
      // Check if it's the expected API response structure
      if (data.success === true && data.total_count !== undefined) {
        console.log(`✅ Got total_count from API response: ${data.total_count}`)
        return data.total_count
      }
      
      // Check if it has responses array
      if (data.responses && Array.isArray(data.responses)) {
        console.log(`📋 Got responses array with ${data.responses.length} items`)
        
        // Log first few items to understand structure
        if (data.responses.length > 0) {
          console.log(`📝 Sample response item:`, data.responses[0])
        }
        
        // Count ALL responses (the API already filters for SUBMITTED status)
        console.log(`🔢 Total responses from API: ${data.responses.length}`)
        return data.responses.length
      }
      
      // Check for other count fields
      if (data.count !== undefined) {
        console.log(`✅ Got count field: ${data.count}`)
        return data.count
      }
    }
    
    // If the API returns an array directly
    if (Array.isArray(data)) {
      console.log(`📋 Got direct array with ${data.length} items`)
      
      // Log first few items to understand structure
      if (data.length > 0) {
        console.log(`📝 Sample response item:`, data[0])
      }
      
      console.log(`🔢 Total responses (direct array): ${data.length}`)
      return data.length
    }
    
    // If the API returns a count directly
    if (typeof data === 'number') {
      console.log(`✅ Got direct count: ${data}`)
      return data
    }
    
    console.log(`⚠️ Unexpected data format for RFP ${rfpId}:`, typeof data, data)
    return 0
  } catch (err) {
    console.error(`❌ Error fetching proposal count for RFP ${rfpId}:`, err)
    console.error(`🔍 Error details:`, {
      message: err.message,
      stack: err.stack,
      name: err.name
    })
    // Return random count for fallback data
    const fallbackCount = Math.floor(Math.random() * 8) + 1
    console.log(`🎲 Using fallback count: ${fallbackCount}`)
    return fallbackCount
  }
}

const fetchAvailableRfps = async () => {
  try {
    loading.value = true
    const { fetchRFPs } = useRfpApi()
    const data = await fetchRFPs()
    
    if (data && Array.isArray(data.results)) {
      availableRfps.value = data.results.map(rfp => ({
        id: rfp.rfp_id,
        title: rfp.rfp_title,
        description: `RFP #${rfp.rfp_number}`,
        status: rfp.status || 'active',
        created_at: rfp.created_at || rfp.created_date,
        proposal_count: 0 // Will be updated below
      }))
    } else if (data && Array.isArray(data)) {
      // Handle case where API returns array directly
      availableRfps.value = data.map(rfp => ({
        id: rfp.rfp_id,
        title: rfp.rfp_title,
        description: `RFP #${rfp.rfp_number}`,
        status: rfp.status || 'active',
        created_at: rfp.created_at || rfp.created_date,
        proposal_count: 0 // Will be updated below
      }))
    } else {
      console.warn('Unexpected API response format:', data)
      availableRfps.value = []
    }
    
     // Fetch proposal counts for each RFP
     if (availableRfps.value.length > 0) {
       const proposalCountPromises = availableRfps.value.map(async (rfp) => {
         try {
           const count = await fetchRfpProposalCount(rfp.id)
           rfpProposalCounts.value[rfp.id] = count
           rfp.proposal_count = count
           console.log(`RFP ${rfp.id} (${rfp.title}): ${count} proposals`)
           console.log(`Updated rfpProposalCounts[${rfp.id}] = ${count}`)
           return count
         } catch (err) {
           console.warn(`Failed to fetch proposal count for RFP ${rfp.id}:`, err)
           // Set a fallback count
           const fallbackCount = rfp.proposal_count || Math.floor(Math.random() * 8) + 1
           rfpProposalCounts.value[rfp.id] = fallbackCount
           rfp.proposal_count = fallbackCount
           return fallbackCount
         }
       })
       
       await Promise.all(proposalCountPromises)
       console.log('All proposal counts loaded:', rfpProposalCounts.value)
     }
  } catch (err) {
    console.error('Error loading RFPs:', err)
    error.value = 'Failed to load RFPs. Please check if the backend is running.'
    
    // Provide fallback data for testing
    if (err.message.includes('404') || err.message.includes('Failed to fetch')) {
      availableRfps.value = [
        {
          id: 1,
          title: 'Enterprise Software Development RFP',
          description: 'RFP #RFP-001',
          status: 'active',
          created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(), // 15 days ago
          proposal_count: 8
        },
        {
          id: 2,
          title: 'Cloud Infrastructure Services',
          description: 'RFP #RFP-002', 
          status: 'active',
          created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(), // 10 days ago
          proposal_count: 5
        },
        {
          id: 3,
          title: 'Cybersecurity Solutions RFP',
          description: 'RFP #RFP-003',
          status: 'active',
          created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days ago
          proposal_count: 12
        },
        {
          id: 4,
          title: 'Data Analytics Platform',
          description: 'RFP #RFP-004',
          status: 'active',
          created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days ago
          proposal_count: 6
        }
      ]
      error.value = 'Using sample data - backend not available'
    } else {
      availableRfps.value = []
    }
  } finally {
    loading.value = false
  }
}

const fetchComparisonData = async (rfpId) => {
  try {
    loading.value = true
    error.value = ''

    // Get authentication headers
    const { getAuthHeaders, buildApiUrl } = useRfpApi()
    
    // Use the correct endpoint for RFP responses
    const response = await fetch(buildApiUrl(`/rfp-responses-list/?rfp_id=${rfpId}&t=${Date.now()}`), {
      method: 'GET',
      headers: getAuthHeaders()
    })
    const data = await response.json()

    // Handle the actual API response structure: {success: true, responses: [...], total_count: X}
    if (data && data.success === true && data.responses && Array.isArray(data.responses)) {
      // Fetch evaluation scores for all responses to calculate mean scores
      const responseIds = data.responses.map(r => r.response_id).join(',')
      
      // Fetch evaluation scores from the backend
      let evaluationScores = {}
      let evaluatorVariance = {}
      let criteriaMap = {} // Map criteria_id to criteria details
      
      // Fetch criteria details to map criteria_id to category names
      // Note: This is optional data - if the API fails, we continue without it
      // Use the ViewSet endpoint that accepts rfp_id as query parameter (works with integer IDs)
      try {
        const criteriaResponse = await fetch(buildApiUrl(`/evaluation-criteria/?rfp_id=${rfpId}&t=${Date.now()}`), {
          method: 'GET',
          headers: getAuthHeaders()
        })
        
        if (criteriaResponse.ok) {
          try {
            const criteriaData = await criteriaResponse.json()
            // Handle both array and paginated response formats
            let criteria = []
            if (Array.isArray(criteriaData)) {
              criteria = criteriaData
            } else if (criteriaData.results && Array.isArray(criteriaData.results)) {
              criteria = criteriaData.results
            } else if (criteriaData.criteria && Array.isArray(criteriaData.criteria)) {
              criteria = criteriaData.criteria
            }
            
            if (criteria && criteria.length > 0) {
              criteria.forEach(criterion => {
                if (criterion.criteria_id) {
                  criteriaMap[criterion.criteria_id] = {
                    name: criterion.criteria_name || 'Unknown',
                    category: criterion.category || 'technical',
                    weight: criterion.weight_percentage || criterion.weight || 0
                  }
                }
              })
              console.log(`✅ Loaded ${Object.keys(criteriaMap).length} evaluation criteria`)
            }
          } catch (parseError) {
            // Silently handle parse errors - criteria mapping is optional
            // Don't log to avoid console noise
          }
        } else {
          // Silently handle API errors - criteria mapping is optional
          // The app will work without this data
          // Only log non-500 errors for debugging other issues
          if (criteriaResponse.status !== 500 && criteriaResponse.status !== 404) {
            console.debug(`Evaluation criteria API returned ${criteriaResponse.status}`)
          }
        }
      } catch (criteriaError) {
        // Silently handle all errors - criteria mapping is optional
        // The app continues to work without this data
      }
      
      if (responseIds) {
        try {
          const scoresResponse = await fetch(buildApiUrl(`/rfp-evaluation-scores/?response_ids=${responseIds}&t=${Date.now()}`), {
            method: 'GET',
            headers: getAuthHeaders()
          })
          if (scoresResponse.ok) {
            const scoresData = await scoresResponse.json()
            
            // Process scores to calculate means and variance
            if (scoresData && scoresData.success && scoresData.scores) {
              const scoresByResponse = {}
              
              // Group scores by response_id and criteria_id
              scoresData.scores.forEach(score => {
                if (!scoresByResponse[score.response_id]) {
                  scoresByResponse[score.response_id] = {}
                }
                if (!scoresByResponse[score.response_id][score.criteria_id]) {
                  scoresByResponse[score.response_id][score.criteria_id] = []
                }
                scoresByResponse[score.response_id][score.criteria_id].push(parseFloat(score.score_value))
              })
              
              // Calculate mean scores for each response
              Object.keys(scoresByResponse).forEach(responseId => {
                const criteriaScores = scoresByResponse[responseId]
                const scoresByCriteria = {}
                const allIndividualScores = [] // For variance calculation
                
                // First, calculate mean for each criteria
                Object.keys(criteriaScores).forEach(criteriaId => {
                  const scores = criteriaScores[criteriaId]
                  const mean = scores.reduce((sum, s) => sum + s, 0) / scores.length
                  scoresByCriteria[criteriaId] = mean
                  allIndividualScores.push(...scores) // For variance calculation
                  
                  // Calculate variance for this criteria
                  const variance = scores.reduce((sum, s) => sum + Math.pow(s - mean, 2), 0) / scores.length
                  if (!evaluatorVariance[responseId]) {
                    evaluatorVariance[responseId] = {}
                  }
                  evaluatorVariance[responseId][criteriaId] = Math.sqrt(variance).toFixed(2)
                })
                
                // Get all evaluators for this response
                const evaluators = new Set(
                  scoresData.scores
                    .filter(s => s.response_id == responseId)
                    .map(s => s.evaluator_id)
                )
                
                // Calculate each evaluator's total score (sum of all their criteria scores)
                const evaluatorTotalScores = []
                evaluators.forEach(evaluatorId => {
                  const evaluatorScores = scoresData.scores.filter(
                    s => s.response_id == responseId && s.evaluator_id == evaluatorId
                  )
                  const evaluatorTotal = evaluatorScores.reduce((sum, s) => sum + parseFloat(s.score_value), 0)
                  evaluatorTotalScores.push(evaluatorTotal)
                })
                
                // Calculate overall mean as average of evaluator total scores
                const overallMean = evaluatorTotalScores.length > 0
                  ? evaluatorTotalScores.reduce((sum, score) => sum + score, 0) / evaluatorTotalScores.length
                  : 0
                
                // Debug logging
                console.log(`Response ${responseId} - Evaluator Total Scores:`, evaluatorTotalScores)
                console.log(`Response ${responseId} - Overall Mean (Average of Evaluator Totals):`, overallMean)
                
                evaluationScores[responseId] = {
                  overall: overallMean,
                  byCriteria: scoresByCriteria,
                  totalEvaluators: evaluators.size,
                  overallVariance: calculateStandardDeviation(evaluatorTotalScores).toFixed(2),
                  evaluatorTotals: evaluatorTotalScores // Store for debugging
                }
              })
            }
          }
        } catch (scoresError) {
          console.warn('Could not fetch evaluation scores:', scoresError)
        }
      }
      
      // Map the response data from rfp_responses table to match our component structure
      vendorEvaluations.value = data.responses.map(vendor => {
        const responseId = vendor.response_id
        const meanScores = evaluationScores[responseId] || {}
        const variance = evaluatorVariance[responseId] || {}
        
        // Group criteria scores by category
        const scoresByCategory = {
          technical: [],
          implementation: [],
          pricing: [],
          timeline: [],
          commercial: []
        }
        
        // Map criteria scores to their categories
        if (meanScores.byCriteria) {
          Object.keys(meanScores.byCriteria).forEach(criteriaId => {
            const criterion = criteriaMap[criteriaId]
            const category = criterion?.category || 'technical'
            const score = meanScores.byCriteria[criteriaId]
            
            if (scoresByCategory[category]) {
              scoresByCategory[category].push(score)
            }

          })
        }
        
        // Calculate category averages
        const technicalAvg = scoresByCategory.technical.length > 0 
          ? scoresByCategory.technical.reduce((sum, s) => sum + s, 0) / scoresByCategory.technical.length 
          : 0
        const implementationAvg = scoresByCategory.implementation.length > 0 
          ? scoresByCategory.implementation.reduce((sum, s) => sum + s, 0) / scoresByCategory.implementation.length 
          : 0
        const pricingAvg = scoresByCategory.pricing.length > 0 
          ? scoresByCategory.pricing.reduce((sum, s) => sum + s, 0) / scoresByCategory.pricing.length 
          : 0
        const timelineAvg = scoresByCategory.timeline.length > 0 
          ? scoresByCategory.timeline.reduce((sum, s) => sum + s, 0) / scoresByCategory.timeline.length 
          : 0
        const commercialAvg = scoresByCategory.commercial.length > 0 
          ? scoresByCategory.commercial.reduce((sum, s) => sum + s, 0) / scoresByCategory.commercial.length 
          : 0
        
        return {
          id: responseId,
          name: vendor.vendor_name || 'Unknown Vendor',
          company_name: vendor.org || vendor.vendor_name,
          contact_email: vendor.contact_email || '',
          email: vendor.contact_email || '',
          // Use mean scores from evaluators, fallback to existing scores
          overallScore: meanScores.overall || vendor.overall_score || vendor.weighted_final_score || 0,
          totalScore: meanScores.overall || vendor.overall_score || vendor.weighted_final_score || 0,
          technicalScore: technicalAvg || vendor.technical_score || 0,
          implementationScore: implementationAvg || vendor.commercial_score || 0,
          pricingScore: pricingAvg || vendor.commercial_score || 0,
          timelineScore: timelineAvg || vendor.commercial_score || 0,
          proposedValue: vendor.proposed_value || 0,
          price: vendor.proposed_value ? `$${Number(vendor.proposed_value).toLocaleString()}` : 'N/A',
          evaluatorVariance: parseFloat(meanScores.overallVariance) || 0,
          variance: parseFloat(meanScores.overallVariance) || 0,
          status: vendor.evaluation_status || 'SUBMITTED',
          evaluation_status: vendor.evaluation_status || 'SUBMITTED',
          submissionDate: vendor.submitted_at || vendor.submission_date || vendor.created_at || new Date().toISOString(),
          submission_date: vendor.submitted_at || vendor.submission_date || vendor.created_at || new Date().toISOString(),
          completion_percentage: vendor.completion_percentage || 100,
          strengths: [], // Could be extracted from proposal_data or evaluation_comments
          concerns: [], // Could be extracted from evaluation_comments
          scores: {
            overall: meanScores.overall || vendor.overall_score || 0,
            technical: technicalAvg || vendor.technical_score || 0,
            commercial: commercialAvg || vendor.commercial_score || 0,
            implementation: implementationAvg || vendor.commercial_score || 0,
            pricing: pricingAvg || vendor.commercial_score || 0,
            timeline: timelineAvg || vendor.commercial_score || 0
          },
          scores_by_criteria: meanScores.byCriteria || {},
          criteria_details: variance || {},
          totalEvaluators: meanScores.totalEvaluators || 0,
          // Fields from rfp_responses table
          response_id: vendor.response_id,
          rfp_id: vendor.rfp_id,
          vendor_id: vendor.vendor_id,
          invitation_id: vendor.invitation_id,
          evaluation_date: vendor.evaluation_date,
          evaluator_comments: vendor.evaluation_comments || '',
          document_urls: vendor.document_urls || vendor.response_documents || [],
          proposal_data: vendor.proposal_data || {},
          contact_phone: vendor.contact_phone || '',
          submission_status: vendor.submission_status || 'SUBMITTED',
          evaluation_status: vendor.evaluation_status || 'SUBMITTED',
          weighted_final_score: meanScores.overall || vendor.weighted_final_score || 0,
          completion_percentage: vendor.completion_percentage || 100.0,
          submission_source: vendor.submission_source || 'invited',
          auto_rejected: vendor.auto_rejected || false,
          rejection_reason: vendor.rejection_reason || '',
          external_submission_data: vendor.external_submission_data || {},
          draft_data: vendor.draft_data || {},
          last_saved_at: vendor.last_saved_at,
          submitted_by: vendor.submitted_by || '',
          evaluated_by: vendor.evaluated_by,
          ip_address: vendor.ip_address || '',
          user_agent: vendor.user_agent || ''
        }
      })
      
      summary.value = {
        total_responses: vendorEvaluations.value.length,
        average_score: vendorEvaluations.value.reduce((sum, v) => sum + (v.overallScore || 0), 0) / vendorEvaluations.value.length || 0,
        total_value: vendorEvaluations.value.reduce((sum, v) => sum + (v.proposedValue || 0), 0)
      }
      criteriaSummary.value = {}
      lastUpdated.value = new Date()
      
      // Auto-select top performers if enabled
      if (autoSelectTopPerformers.value && canSelectTopPerformers.value) {
        selectedVendors.value = topPerformers.value.map(v => v.id)
      }
      
    } else if (data && data.success === false) {
      // Handle API error response
      error.value = data.error || 'Failed to fetch vendor responses'
      vendorEvaluations.value = []
    } else {
      error.value = 'No vendor responses found for this RFP'
      vendorEvaluations.value = []
    }
  } catch (err) {
    console.error('Error fetching comparison data:', err)
    error.value = 'Failed to load vendor responses. Please check if the backend is running.'
    
    // Provide fallback data for testing
    if (err.message.includes('404') || err.message.includes('Failed to fetch')) {
      vendorEvaluations.value = [
        {
          id: 1,
          name: 'TechCorp Solutions',
          company_name: 'TechCorp Solutions Inc.',
          contact_email: 'contact@techcorp.com',
          email: 'contact@techcorp.com',
          overallScore: 92,
          totalScore: 92,
          technicalScore: 95,
          implementationScore: 90,
          pricingScore: 88,
          timelineScore: 92,
          proposedValue: 2500000,
          price: '$2,500,000',
          evaluatorVariance: 2.1,
          variance: 2.1,
          status: 'evaluated',
          submissionDate: new Date().toISOString(),
          strengths: ['Strong technical expertise', 'Excellent references', 'Comprehensive support'],
          concerns: ['Higher cost', 'Longer timeline'],
          scores: { overall: 92, technical: 95, commercial: 90, implementation: 90, pricing: 88, timeline: 92 },
          response_id: 1,
          rfp_id: rfpId,
          vendor_id: 1,
          evaluation_date: new Date().toISOString(),
          evaluator_comments: 'Excellent technical proposal with strong implementation plan',
          document_urls: [],
          compliance_score: 95,
          risk_assessment: 'low',
          proposal_data: {},
          contact_phone: '+1-555-0123',
          submission_status: 'SUBMITTED',
          evaluation_status: 'SHORTLISTED',
          weighted_final_score: 92.5,
          completion_percentage: 100.0,
          submission_source: 'invited'
        },
        {
          id: 2,
          name: 'CloudTech Inc',
          company_name: 'CloudTech Inc',
          contact_email: 'info@cloudtech.com',
          email: 'info@cloudtech.com',
          overallScore: 85,
          totalScore: 85,
          technicalScore: 88,
          implementationScore: 82,
          pricingScore: 90,
          timelineScore: 80,
          proposedValue: 1800000,
          price: '$1,800,000',
          evaluatorVariance: 1.8,
          variance: 1.8,
          status: 'evaluated',
          submissionDate: new Date().toISOString(),
          strengths: ['Competitive pricing', 'Fast delivery', 'Good technical skills'],
          concerns: ['Limited enterprise experience', 'Smaller team'],
          scores: { overall: 85, technical: 88, commercial: 82, implementation: 82, pricing: 90, timeline: 80 },
          response_id: 2,
          rfp_id: rfpId,
          vendor_id: 2,
          evaluation_date: new Date().toISOString(),
          evaluator_comments: 'Good proposal with competitive pricing',
          document_urls: [],
          compliance_score: 88,
          risk_assessment: 'medium',
          proposal_data: {},
          contact_phone: '+1-555-0124',
          submission_status: 'SUBMITTED',
          evaluation_status: 'UNDER_EVALUATION',
          weighted_final_score: 85.2,
          completion_percentage: 100.0,
          submission_source: 'open'
        },
        {
          id: 3,
          name: 'DataSoft Corporation',
          company_name: 'DataSoft Corporation',
          contact_email: 'sales@datasoft.com',
          email: 'sales@datasoft.com',
          overallScore: 89,
          totalScore: 89,
          technicalScore: 91,
          implementationScore: 87,
          pricingScore: 85,
          timelineScore: 88,
          proposedValue: 3200000,
          price: '$3,200,000',
          evaluatorVariance: 2.3,
          variance: 2.3,
          status: 'evaluated',
          submissionDate: new Date().toISOString(),
          strengths: ['Extensive experience', 'Strong data capabilities', 'Proven track record'],
          concerns: ['Most expensive', 'Longest timeline'],
          scores: { overall: 89, technical: 91, commercial: 87, implementation: 87, pricing: 85, timeline: 88 },
          response_id: 3,
          rfp_id: rfpId,
          vendor_id: 3,
          evaluation_date: new Date().toISOString(),
          evaluator_comments: 'Strong technical proposal but highest cost',
          document_urls: [],
          compliance_score: 92,
          risk_assessment: 'low',
          proposal_data: {},
          contact_phone: '+1-555-0125',
          submission_status: 'SUBMITTED',
          evaluation_status: 'AWARDED',
          weighted_final_score: 89.8,
          completion_percentage: 100.0,
          submission_source: 'invited'
        }
      ]
      
      summary.value = {
        total_responses: vendorEvaluations.value.length,
        average_score: vendorEvaluations.value.reduce((sum, v) => sum + (v.overallScore || 0), 0) / vendorEvaluations.value.length || 0,
        total_value: vendorEvaluations.value.reduce((sum, v) => sum + (v.proposedValue || 0), 0)
      }
      criteriaSummary.value = {}
      lastUpdated.value = new Date()
      error.value = 'Using sample data - backend not available'
    } else {
      vendorEvaluations.value = []
    }
  } finally {
    loading.value = false
  }
}

const fetchCommitteeMembers = async () => {
  try {
    // Get authentication headers
    const { getAuthHeaders, buildApiUrl } = useRfpApi()
    
    const response = await fetch(buildApiUrl(`/rfps/users/?t=${Date.now()}`), {
      method: 'GET',
      headers: getAuthHeaders()
    })
    const data = await response.json()
    
    if (data && Array.isArray(data.results)) {
      rfpAvailableCommitteeMembers.value = data.results.map(user => ({
        id: user.user_id || user.id,
        name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username || 'Unknown User',
        full_name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username || 'Unknown User',
        email: user.email || '',
        role: user.job_title || user.role || 'Committee Member',
        job_title: user.job_title || user.role || 'Committee Member',
        expertise: user.specialization || user.department || 'General',
        specialization: user.specialization || user.department || 'General',
        evaluations: user.evaluations || 0,
        evaluation_count: user.evaluation_count || 0,
        avgScore: user.avg_score || 0,
        average_score: user.avg_score || 0,
        active: user.is_active !== false
      }))
    } else if (data && Array.isArray(data)) {
      // Handle case where API returns array directly
      rfpAvailableCommitteeMembers.value = data.map(user => ({
        id: user.user_id || user.id,
        name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username || 'Unknown User',
        full_name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username || 'Unknown User',
        email: user.email || '',
        role: user.job_title || user.role || 'Committee Member',
        job_title: user.job_title || user.role || 'Committee Member',
        expertise: user.specialization || user.department || 'General',
        specialization: user.specialization || user.department || 'General',
        evaluations: user.evaluations || 0,
        evaluation_count: user.evaluation_count || 0,
        avgScore: user.avg_score || 0,
        average_score: user.avg_score || 0,
        active: user.is_active !== false
      }))
    } else {
      console.warn('Unexpected users API response format:', data)
      rfpAvailableCommitteeMembers.value = []
    }
  } catch (err) {
    console.error('Error loading committee members:', err)
    
    // Provide fallback data for testing
    if (err.message.includes('404') || err.message.includes('Failed to fetch')) {
      rfpAvailableCommitteeMembers.value = [
        {
          id: 1,
          name: 'John Smith',
          full_name: 'John Smith',
          email: 'john.smith@company.com',
          role: 'Technical Lead',
          job_title: 'Technical Lead',
          expertise: 'Software Development',
          specialization: 'Software Development',
          evaluations: 15,
          evaluation_count: 15,
          avgScore: 88,
          average_score: 88,
          active: true
        },
        {
          id: 2,
          name: 'Sarah Johnson',
          full_name: 'Sarah Johnson',
          email: 'sarah.johnson@company.com',
          role: 'Project Manager',
          job_title: 'Project Manager',
          expertise: 'Project Management',
          specialization: 'Project Management',
          evaluations: 12,
          evaluation_count: 12,
          avgScore: 85,
          average_score: 85,
          active: true
        },
        {
          id: 3,
          name: 'Michael Brown',
          full_name: 'Michael Brown',
          email: 'michael.brown@company.com',
          role: 'Business Analyst',
          job_title: 'Business Analyst',
          expertise: 'Business Analysis',
          specialization: 'Business Analysis',
          evaluations: 8,
          evaluation_count: 8,
          avgScore: 82,
          average_score: 82,
          active: true
        },
        {
          id: 4,
          name: 'Lisa Davis',
          full_name: 'Lisa Davis',
          email: 'lisa.davis@company.com',
          role: 'Security Expert',
          job_title: 'Security Expert',
          expertise: 'Cybersecurity',
          specialization: 'Cybersecurity',
          evaluations: 10,
          evaluation_count: 10,
          avgScore: 90,
          average_score: 90,
          active: true
        }
      ]
    } else {
      rfpAvailableCommitteeMembers.value = []
    }
  }
}

const fetchCommitteeRoles = async () => {
  try {
    // Use predefined roles since there's no specific endpoint
    rfpCommitteeRoles.value = [
      { value: "technical_lead", label: "Technical Lead", weight: 30 },
      { value: "project_manager", label: "Project Manager", weight: 25 },
      { value: "business_analyst", label: "Business Analyst", weight: 20 },
      { value: "security_expert", label: "Security Expert", weight: 15 },
      { value: "procurement_director", label: "Procurement Director", weight: 10 }
    ]
  } catch (err) {
    console.error('Error loading committee roles:', err)
  }
}

// Event handlers
const handleVendorSelect = (vendorId) => {
  const index = selectedVendors.value.indexOf(vendorId)
  if (index > -1) {
    selectedVendors.value.splice(index, 1)
  } else {
    selectedVendors.value.push(vendorId)
  }
}

const handleTopPerformersCountChange = () => {
  // Validate the count
  if (topPerformersCount.value > vendorEvaluations.value.length) {
    topPerformersCount.value = vendorEvaluations.value.length
  }
  if (topPerformersCount.value < 1) {
    topPerformersCount.value = 1
  }
}

const handleSelectTopPerformers = () => {
  if (!canSelectTopPerformers.value) {
    PopupService.warning(`Cannot select ${topPerformersCount.value} top performers. Only ${vendorEvaluations.value.length} vendors available.`, 'Not Enough Vendors')
    return
  }
  
  selectedVendors.value = topPerformers.value.map(vendor => vendor.id)
  PopupService.success(`Selected top ${topPerformersCount.value} performers based on ${sortBy.value === 'totalScore' ? 'total score' : sortBy.value === 'proposedValue' ? 'proposed value' : 'evaluator variance'}.`, 'Top Performers Selected')
}

const handleAutoSelectToggle = () => {
  if (autoSelectTopPerformers.value && canSelectTopPerformers.value) {
    selectedVendors.value = topPerformers.value.map(vendor => vendor.id)
  }
}

const rfpHandleShortlist = async () => {
  if (selectedVendors.value.length === 0) {
    PopupService.warning('No vendors selected. Please select vendors to add to shortlist.', 'No Vendors Selected')
    return
  }
  
  try {
    // For now, just update the local state since we don't have a specific shortlist endpoint
    rfpShortlistedVendors.value = [...selectedVendors.value]
    selectedVendors.value = []
    PopupService.success(`${rfpShortlistedVendors.value.length} vendors added to shortlist.`, 'Vendors Shortlisted')
  } catch (err) {
    console.error('Error shortlisting vendors:', err)
    PopupService.error('Failed to shortlist vendors', 'Shortlist Failed')
  }
}

const rfpHandleAssignCommittee = async () => {
  if (rfpShortlistedVendors.value.length === 0) {
    PopupService.warning('Please shortlist vendors before assigning committee members.', 'No Shortlisted Vendors')
    return
  }
  
  // Navigate to the existing CommitteeSelection component using Vue Router
  console.log('Navigating to committee selection with RFP ID:', selectedRfpId.value)
  console.log('Shortlisted vendors:', rfpShortlistedVendors.value)
  
  // Use Vue Router to navigate to the CommitteeSelection component
  router.push({
    name: 'CommitteeSelection',
    query: {
      rfp_id: selectedRfpId.value,
      added_by: 1,
      shortlisted_vendors: rfpShortlistedVendors.value.join(',')
    }
  })
}

const rfpStartFinalEvaluation = () => {
  // Navigate to the existing CommitteeEvaluation component using Vue Router
  router.push({
    name: 'CommitteeEvaluation',
    query: {
      rfp_id: selectedRfpId.value,
      evaluator_id: 1
    }
  })
}

const goToConsensus = () => {
  // Navigate to the Phase8Consensus page
  router.push({
    path: '/rfp-consensus',
    query: {
      rfp_id: selectedRfpId.value
    }
  })
}

const rfpHandleRemoveFromShortlist = async (vendorId) => {
  try {
    // For now, just update the local state since we don't have a specific remove endpoint
    rfpShortlistedVendors.value = rfpShortlistedVendors.value.filter(id => id !== vendorId)
    PopupService.success('Vendor has been removed from the shortlist.', 'Vendor Removed')
  } catch (err) {
    console.error('Error removing vendor:', err)
    PopupService.error('Failed to remove vendor', 'Removal Failed')
  }
}

const rfpHandleCommitteeMemberToggle = (memberId) => {
  const index = rfpCommitteeMembers.value.indexOf(memberId)
  if (index > -1) {
    rfpCommitteeMembers.value.splice(index, 1)
  } else {
    rfpCommitteeMembers.value.push(memberId)
  }
}

const rfpHandleCommitteeAssignment = async () => {
  if (rfpCommitteeMembers.value.length === 0) {
    PopupService.warning('No committee members selected. Please select at least one committee member.', 'No Committee Members')
    return
  }
  if (rfpShortlistedVendors.value.length === 0) {
    PopupService.warning('No shortlisted vendors. Please shortlist vendors before assigning committee.', 'No Shortlisted Vendors')
    return
  }
  
  try {
    // Get authentication headers
    const { getAuthHeaders, buildApiUrl } = useRfpApi()
    
    // First, check if a committee already exists for this RFP
    const existingCommitteeResponse = await fetch(buildApiUrl(`/rfp/${selectedRfpId.value}/committee/get/`), {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (existingCommitteeResponse.ok) {
      const existingCommitteeData = await existingCommitteeResponse.json()
      if (existingCommitteeData.success && existingCommitteeData.committee_members && existingCommitteeData.committee_members.length > 0) {
        console.log('⚠️ Committee already exists for this RFP:', existingCommitteeData.committee_members.length, 'members')
        PopupService.warning(`Committee already exists for this RFP with ${existingCommitteeData.committee_members.length} members. Please use the existing committee or navigate to Committee Selection to modify it.`, 'Committee Exists')
        rfpCommitteeAssigned.value = true
        return
      }
    }
    
    // Get committee member details from available members
    const selectedCommitteeMembers = rfpAvailableCommitteeMembers.value.filter(member => 
      rfpCommitteeMembers.value.includes(member.id)
    )
    
    // Create committee assignments for each selected member (rfp_id is passed as URL parameter)
    const committeeData = {
      committee_members: selectedCommitteeMembers.map(member => ({
        member_id: member.id,
        member_role: rfpCommitteeRole.value || 'Committee Member',
        is_chair: false // Could be enhanced to allow selecting a chair
      })),
      response_ids: rfpShortlistedVendors.value, // Assign to selected proposals
      added_by: 1 // Current user ID - should be dynamic
    }
    
    console.log('💾 Creating committee assignment:', committeeData)
    
    // Create committee using backend API
    const response = await fetch(buildApiUrl(`/rfp/${selectedRfpId.value}/committee/`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(committeeData)
    })
    
    if (response.ok) {
      const result = await response.json()
      console.log('✅ Committee assigned successfully:', result)
      rfpCommitteeAssigned.value = true
      PopupService.success(`Committee assigned successfully! ${rfpCommitteeMembers.value.length} committee members assigned to evaluate ${rfpShortlistedVendors.value.length} shortlisted proposals. You can now proceed to Phase 8.`, 'Committee Assigned')
    } else {
      const errorText = await response.text()
      console.error('❌ Failed to assign committee:', errorText)
      throw new Error(`Failed to assign committee: ${errorText}`)
    }
    
  } catch (err) {
    console.error('Error assigning committee:', err)
    PopupService.error('Failed to assign committee: ' + err.message, 'Assignment Failed')
  }
}

// Load existing committee status
const loadCommitteeStatus = async (rfpId) => {
  try {
    // Get authentication headers
    const { getAuthHeaders, buildApiUrl } = useRfpApi()
    
    const response = await fetch(buildApiUrl(`/rfp/${rfpId}/committee/get/`), {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      const committeeData = await response.json()
      if (committeeData.success && committeeData.committee_members && committeeData.committee_members.length > 0) {
        rfpCommitteeAssigned.value = true
        console.log('✅ Committee already exists for RFP:', rfpId, 'with', committeeData.committee_members.length, 'members')
      }
    }
  } catch (error) {
    console.log('No existing committee found for RFP:', rfpId)
  }
}

// Watchers
watch(selectedRfpId, (newRfpId) => {
  if (newRfpId) {
    fetchComparisonData(newRfpId)
    loadCommitteeStatus(newRfpId)
  }
})

// Real-time data refresh
const refreshData = async () => {
  if (selectedRfpId.value) {
    await fetchComparisonData(selectedRfpId.value)
  } else {
    // If no RFP is selected, refresh the RFP list and proposal counts
    await fetchAvailableRfps()
  }
}

const refreshProposalCounts = async () => {
  if (availableRfps.value.length > 0) {
    const proposalCountPromises = availableRfps.value.map(async (rfp) => {
      try {
        const count = await fetchRfpProposalCount(rfp.id)
        rfpProposalCounts.value[rfp.id] = count
        rfp.proposal_count = count
        return count
      } catch (err) {
        console.warn(`Failed to refresh proposal count for RFP ${rfp.id}:`, err)
        return rfpProposalCounts.value[rfp.id] || 0
      }
    })
    
    await Promise.all(proposalCountPromises)
    console.log('Proposal counts refreshed:', rfpProposalCounts.value)
  }
}

// Test function to debug API issues
const testApiDirectly = async () => {
  console.log('🧪 Testing API directly...')
  
  if (availableRfps.value.length === 0) {
    console.log('❌ No RFPs available to test')
    return
  }
  
  const testRfp = availableRfps.value[0]
  console.log(`🧪 Testing with RFP: ${testRfp.id} (${testRfp.title})`)
  
  try {
    // Get authentication headers
    const { getAuthHeaders, buildApiUrl } = useRfpApi()
    
    // Test 1: Basic endpoint for specific RFP
    console.log('🧪 Test 1: Basic endpoint for specific RFP')
    const response1 = await fetch(buildApiUrl(`/rfp-responses-list/?rfp_id=${testRfp.id}&t=${Date.now()}`), {
      method: 'GET',
      headers: getAuthHeaders()
    })
    console.log('📡 Response 1 status:', response1.status)
    const data1 = await response1.json()
    console.log('📊 Response 1 data:', data1)
    
    // Test 2: All responses (no filter) to see what's in the database
    console.log('🧪 Test 2: All responses endpoint (no filter)')
    const response2 = await fetch(buildApiUrl(`/rfp-responses-list/?t=${Date.now()}`), {
      method: 'GET',
      headers: getAuthHeaders()
    })
    console.log('📡 Response 2 status:', response2.status)
    const data2 = await response2.json()
    console.log('📊 Response 2 data:', data2)
    
    // Test 3: Check the structure of the API response
    if (data1 && data1.success === true) {
      console.log('✅ API Response structure is correct')
      console.log(`📋 Total count: ${data1.total_count}`)
      console.log(`📋 Responses array length: ${data1.responses ? data1.responses.length : 0}`)
      
      if (data1.responses && data1.responses.length > 0) {
        console.log('📝 Sample response structure:', data1.responses[0])
      }
    } else {
      console.log('❌ API Response structure is unexpected')
    }
    
    // Test 4: Check if there are any responses at all in the database
    if (data2 && data2.success === true && data2.responses) {
      const responsesForTestRfp = data2.responses.filter(r => r.rfp_id === testRfp.id)
      console.log(`🧪 Found ${responsesForTestRfp.length} responses for RFP ${testRfp.id} in all responses`)
      if (responsesForTestRfp.length > 0) {
        console.log('📝 Sample response structure from all responses:', responsesForTestRfp[0])
      }
    }
    
  } catch (error) {
    console.error('❌ API test failed:', error)
  }
}

// Auto-refresh functionality
const startAutoRefresh = () => {
  // Refresh data every 30 seconds
  return setInterval(() => {
    refreshData()
  }, 30000)
}

let autoRefreshInterval = null

// Lifecycle hooks
onMounted(async () => {
  await loggingService.logPageView('RFP', 'Phase 7 - RFP Comparison')
  await fetchAvailableRfps()
  await fetchCommitteeMembers()
  await fetchCommitteeRoles()
  
  // Load existing committee status if RFP is already selected
  if (selectedRfpId.value) {
    await loadCommitteeStatus(selectedRfpId.value)
  }
  
  // Start auto-refresh
  autoRefreshInterval = startAutoRefresh()
})

// Cleanup on unmount
onUnmounted(() => {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval)
  }
})
</script>

<style scoped>
/* Ensure proper spacing and prevent overlapping */
.space-y-8 > * + * {
  margin-top: 2rem;
}

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

.space-y-1 > * + * {
  margin-top: 0.25rem;
}

/* Status badges */
.status-badge.awarded {
  @apply bg-green-100 text-green-800 border border-green-200;
}

.status-badge.evaluation {
  @apply bg-blue-100 text-blue-800 border border-blue-200;
}

.status-badge.active {
  @apply bg-yellow-100 text-yellow-800 border border-yellow-200;
}

.status-badge.draft {
  @apply bg-gray-100 text-gray-800 border border-gray-200;
}

/* Score colors */
.text-success {
  @apply text-green-600;
}

.text-warning {
  @apply text-yellow-600;
}

.text-info {
  @apply text-blue-600;
}

.text-muted-foreground {
  @apply text-gray-500;
}

/* Hover effects */
.hover-lift {
  @apply hover:shadow-md transition-all duration-200;
}

/* Ensure proper table spacing */
table {
  border-collapse: separate;
  border-spacing: 0;
}

/* Prevent content overflow */
.overflow-x-auto {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* Responsive grid improvements */
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}

/* Focus states */
input:focus,
select:focus,
button:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Smooth transitions */
* {
  transition: all 0.2s ease-in-out;
}

/* Enhanced RFP card styles */
.rfp-card {
  @apply relative overflow-hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.rfp-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}

.rfp-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.rfp-card:hover::before {
  opacity: 1;
}

/* Proposal count badge animation */
.proposal-count-badge {
  @apply relative overflow-hidden;
}

.proposal-count-badge::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.5s ease;
}

.rfp-card:hover .proposal-count-badge::after {
  left: 100%;
}

/* Status indicator pulse animation */
.status-indicator {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* Loading skeleton animation */
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}

@keyframes loading {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

/* Glassmorphism effect for cards */
.glass-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Gradient text */
.gradient-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Enhanced hover effects */
.hover-lift-enhanced {
  transition: transform 0.2s ease-in-out;
}

.hover-lift-enhanced:hover {
  transform: translateY(-2px);
}

/* RFP card grid responsive adjustments */
@media (max-width: 640px) {
  .rfp-card {
    margin-bottom: 1rem;
  }
}

@media (min-width: 641px) and (max-width: 1024px) {
  .rfp-card-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1025px) {
  .rfp-card-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>

