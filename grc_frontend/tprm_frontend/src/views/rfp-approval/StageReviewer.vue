<template>
  <div class="stage-reviewer max-w-6xl mx-auto p-6">
    <!-- Header Card -->
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm mb-6">
      <div class="px-6 py-4 border-b border-gray-200">
        <div class="flex items-center justify-between">
           <div>
             <h1 class="text-2xl font-bold text-gray-900">Stage Review & Decision</h1>
             <p class="text-gray-600 mt-1">
               {{ getUrlParams().stageId 
                 ? 'Review and make decisions on the selected approval stage' 
                 : 'Review and make decisions on assigned approval stages' 
               }}
             </p>
           </div>
           <div class="flex items-center space-x-3">
             <button 
               @click="goBack"
               class="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors flex items-center space-x-2"
             >
               <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
               </svg>
               <span>Back to My Approvals</span>
             </button>
        </div>
        </div>

      <!-- User Selection -->
      <div class="px-6 py-4">
        <div class="flex items-center space-x-4">
          <label class="text-sm font-medium text-gray-700">Reviewer User ID:</label>
          <select 
            v-model="selectedUserId" 
            @change="fetchAssignedStages"
            class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            style="width: 300px"
          >
            <option value="">Select your user ID</option>
            <option
              v-for="user in users"
              :key="user.id"
              :value="user.id"
            >
              {{ user.first_name }} {{ user.last_name }} ({{ user.role }} - {{ user.department }})
            </option>
          </select>
        </div>
      </div>
      </div>

      <!-- Assigned Stages -->
    <div v-if="selectedUserId && assignedStages.length > 0" class="space-y-6">
      <div class="flex items-center space-x-2">
        <div class="h-px bg-gray-300 flex-1"></div>
        <h2 class="text-lg font-semibold text-gray-900 px-4">Assigned Stages</h2>
        <div class="h-px bg-gray-300 flex-1"></div>
      </div>
      
      <div class="space-y-4">
        <div 
            v-for="stage in assignedStages" 
            :key="stage.stage_id" 
          class="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
        >
          <!-- Stage Header -->
          <div class="px-6 py-4 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <h3 class="text-lg font-semibold text-gray-900">{{ stage.stage_name }}</h3>
                <span class="text-sm text-gray-500">(Stage {{ stage.stage_order }})</span>
              </div>
              <div class="flex items-center space-x-2">
                <span 
                  :class="getStatusBadgeClass(stage.stage_status)"
                  class="px-3 py-1 text-sm font-medium rounded-full"
                >
                  {{ getStageStatusLabel(stage.stage_status) }}
                </span>
                <!-- Workflow Type Indicator -->
                <span 
                  v-if="stage.workflow_type === 'MULTI_LEVEL' || stage.workflow_type === 'SEQUENTIAL'"
                  class="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full"
                >
                  Sequential
                </span>
              </div>
            </div>
            
            <!-- Workflow Progress Indicator for Multi-Level/Sequential -->
            <div v-if="stage.workflow_type === 'MULTI_LEVEL' || stage.workflow_type === 'SEQUENTIAL'" class="mt-4">
              <div class="flex items-center space-x-2 mb-2">
                <span class="text-sm font-medium text-gray-700">Workflow Progress:</span>
                <span class="text-xs text-gray-500">Sequential approval required</span>
              </div>
              <div class="flex items-center space-x-2">
                <div 
                  v-for="i in getWorkflowStageCount(stage)" 
                  :key="i"
                  :class="getStageProgressClass(i, stage.stage_order, stage.stage_status)"
                  class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium border-2"
                >
                  {{ i }}
                </div>
                <div class="text-xs text-gray-500 ml-2">
                  Stage {{ stage.stage_order }} of {{ getWorkflowStageCount(stage) }}
                </div>
              </div>
            </div>
              </div>

          <!-- Stage Content -->
          <div class="px-6 py-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-3">
                <p><strong class="text-gray-700">Request:</strong> {{ stage.request_title }}</p>
                <p><strong class="text-gray-700">Description:</strong> {{ stage.stage_description }}</p>
                <p><strong class="text-gray-700">Deadline:</strong> {{ formatDate(stage.deadline_date) }}</p>
                <p><strong class="text-gray-700">Workflow Type:</strong> {{ stage.workflow_type }}</p>
              </div>
              <div class="space-y-3">
                <p><strong class="text-gray-700">Stage Order:</strong> {{ stage.stage_order }}</p>
                <p><strong class="text-gray-700">Department:</strong> {{ stage.department }}</p>
                <p><strong class="text-gray-700">Priority:</strong> {{ stage.priority }}</p>
                <p><strong class="text-gray-700">Created:</strong> {{ formatDate(stage.created_at) }}</p>
              </div>
            </div>

              <!-- Request Data -->
             <div class="mt-6">
               <div class="flex items-center space-x-2 mb-6">
                 <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                   <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                   </svg>
                 </div>
                 <h4 class="text-xl font-semibold text-gray-900">Request Details</h4>
               </div>
               
               <div v-if="hasRequestData(stage)" class="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                 <div class="p-6">
                   <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                     <div 
                       v-for="(value, key) in getRequestData(stage)" 
                       :key="key"
                       class="group"
                     >
                       <div class="bg-gray-50 rounded-lg p-4 border border-gray-100 hover:border-gray-200 transition-all duration-200">
                         <div class="flex items-start space-x-3">
                           <div class="flex-shrink-0 mt-1">
                             <div class="w-6 h-6 bg-blue-100 rounded-md flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                               <svg class="w-3 h-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                               </svg>
                             </div>
                           </div>
                           <div class="flex-1 min-w-0">
                             <h5 class="text-sm font-semibold text-gray-900 mb-3">{{ formatKey(key) }}</h5>
                             <div class="text-gray-700">
                               <!-- Special handling for criteria data -->
                               <div v-if="key && String(key).toLowerCase() === 'criteria' && Array.isArray(value)" class="space-y-3">
                                 <div v-for="(criterion, index) in value" :key="index" class="bg-white rounded-lg p-4 border border-gray-100">
                                   <div class="flex items-start space-x-3">
                                     <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                                       <span class="text-xs font-semibold text-blue-600">{{ index + 1 }}</span>
                                     </div>
                                     <div class="flex-1">
                                       <h6 class="text-sm font-semibold text-gray-900 mb-2">{{ criterion.name || `Criterion ${index + 1}` }}</h6>
                                       <p class="text-sm text-gray-600 mb-3">{{ criterion.description || 'No description provided' }}</p>
                                       <div class="flex items-center space-x-4 text-xs">
                                         <div class="flex items-center space-x-1">
                                           <span class="text-gray-500">Weight:</span>
                                           <span class="font-medium text-gray-800">{{ criterion.weight || 0 }}%</span>
                                         </div>
                                         <div class="flex items-center space-x-1">
                                           <span class="text-gray-500">Veto:</span>
                                           <span class="font-medium" :class="criterion.isVeto ? 'text-red-600' : 'text-green-600'">
                                             {{ criterion.isVeto ? 'Yes' : 'No' }}
                                           </span>
                                         </div>
                                       </div>
                                     </div>
                                   </div>
                                 </div>
                               </div>
                               <!-- Regular object handling -->
                               <div v-else-if="typeof value === 'object' && value !== null && !Array.isArray(value)" class="space-y-3">
                                 <div v-for="(subValue, subKey) in value" :key="subKey" class="flex flex-col space-y-1">
                                   <span class="text-xs font-medium text-gray-500 uppercase tracking-wide">{{ formatKey(subKey) }}</span>
                                   <span class="text-sm text-gray-800 font-medium">{{ formatValue(subValue) }}</span>
                                 </div>
                               </div>
                               <!-- Regular array handling -->
                               <div v-else-if="Array.isArray(value)" class="space-y-2">
                                 <div v-for="(item, index) in value" :key="index" class="flex items-center space-x-2">
                                   <div class="w-1.5 h-1.5 bg-blue-500 rounded-full flex-shrink-0"></div>
                                   <span class="text-sm text-gray-800">{{ formatValue(item) }}</span>
                                 </div>
                               </div>
                               <!-- Simple value handling -->
                               <div v-else class="text-sm text-gray-800 font-medium">
                                 {{ formatValue(value) }}
                               </div>
                             </div>
                           </div>
                         </div>
                       </div>
                     </div>
                   </div>
                 </div>
               </div>
                 <div v-else class="p-12 text-center">
                   <div class="text-gray-400 mb-4">
                     <svg class="mx-auto h-16 w-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                       <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                     </svg>
                   </div>
                   <h3 class="text-lg font-medium text-gray-900 mb-2">No Additional Data</h3>
                   <p class="text-sm text-gray-500 max-w-sm mx-auto">This approval request doesn't contain additional data fields. All necessary information is available in the request details above.</p>
                 </div>
               </div>
               
              </div>

              <!-- Complete RFP Details Section -->
            <div class="mt-6">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                    <svg class="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                  </div>
                  <h4 class="text-xl font-semibold text-gray-900">Complete RFP Information</h4>
                </div>
                <button 
                  v-if="!hasRfpDetails(stage)"
                  @click="() => loadRfpDetailsForStage(stage)"
                  :disabled="loadingRfpDetails"
                  class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  <svg v-if="!loadingRfpDetails" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                  </svg>
                  <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>{{ loadingRfpDetails ? 'Loading...' : 'Load RFP Details' }}</span>
                </button>
              </div>

              <!-- RFP Details Content -->
              <div v-if="hasRfpDetails(stage)" class="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
                <div class="p-6">
                  <div v-if="getRfpDetailsForStage(stage)" class="space-y-6">
                    <!-- Basic Information -->
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div class="space-y-4">
                        <div class="bg-blue-50 rounded-lg p-4 border border-blue-100">
                          <h5 class="text-sm font-semibold text-blue-900 mb-3">Basic Information</h5>
                          <div class="space-y-2 text-sm">
                            <p><strong class="text-gray-700">RFP Number:</strong> <span class="text-gray-900">{{ getRfpDetailsForStage(stage).rfp_number }}</span></p>
                            <p><strong class="text-gray-700">Title:</strong> <span class="text-gray-900">{{ getRfpDetailsForStage(stage).rfp_title }}</span></p>
                            <p><strong class="text-gray-700">Type:</strong> <span class="text-gray-900">{{ getRfpDetailsForStage(stage).rfp_type }}</span></p>
                            <p><strong class="text-gray-700">Category:</strong> <span class="text-gray-900">{{ getRfpDetailsForStage(stage).category || 'N/A' }}</span></p>
                            <p><strong class="text-gray-700">Status:</strong> 
                              <span :class="getStatusBadgeClass(getRfpDetailsForStage(stage).status)" class="px-2 py-1 text-xs font-medium rounded-full">
                                {{ getRfpDetailsForStage(stage).status }}
                              </span>
                            </p>
                          </div>
                        </div>

                        <div class="bg-green-50 rounded-lg p-4 border border-green-100">
                          <h5 class="text-sm font-semibold text-green-900 mb-3">Budget Information</h5>
                          <div class="space-y-2 text-sm">
                            <p><strong class="text-gray-700">Estimated Value:</strong> 
                              <span class="text-gray-900">
                                {{ getRfpDetailsForStage(stage).currency }} {{ formatValue(getRfpDetailsForStage(stage).estimated_value) }}
                              </span>
                            </p>
                            <p v-if="getRfpDetailsForStage(stage).budget_range_min || getRfpDetailsForStage(stage).budget_range_max">
                              <strong class="text-gray-700">Budget Range:</strong> 
                              <span class="text-gray-900">
                                {{ getRfpDetailsForStage(stage).currency }} {{ formatValue(getRfpDetailsForStage(stage).budget_range_min) }} - {{ formatValue(getRfpDetailsForStage(stage).budget_range_max) }}
                              </span>
                            </p>
                          </div>
                        </div>
                      </div>

                      <div class="space-y-4">
                        <div class="bg-purple-50 rounded-lg p-4 border border-purple-100">
                          <h5 class="text-sm font-semibold text-purple-900 mb-3">Timeline</h5>
                          <div class="space-y-2 text-sm">
                            <p><strong class="text-gray-700">Issue Date:</strong> <span class="text-gray-900">{{ formatDate(getRfpDetailsForStage(stage).issue_date) }}</span></p>
                            <p><strong class="text-gray-700">Submission Deadline:</strong> <span class="text-gray-900">{{ formatDate(getRfpDetailsForStage(stage).submission_deadline) }}</span></p>
                            <p><strong class="text-gray-700">Evaluation End:</strong> <span class="text-gray-900">{{ formatDate(getRfpDetailsForStage(stage).evaluation_period_end) }}</span></p>
                            <p v-if="getRfpDetailsForStage(stage).award_date"><strong class="text-gray-700">Award Date:</strong> <span class="text-gray-900">{{ formatDate(getRfpDetailsForStage(stage).award_date) }}</span></p>
                          </div>
                        </div>

                        <div class="bg-amber-50 rounded-lg p-4 border border-amber-100">
                          <h5 class="text-sm font-semibold text-amber-900 mb-3">Evaluation Details</h5>
                          <div class="space-y-2 text-sm">
                            <p><strong class="text-gray-700">Method:</strong> <span class="text-gray-900">{{ formatKey(getRfpDetailsForStage(stage).evaluation_method) }}</span></p>
                            <p><strong class="text-gray-700">Criticality:</strong> 
                              <span :class="{
                                'text-red-600': getRfpDetailsForStage(stage).criticality_level === 'critical',
                                'text-orange-600': getRfpDetailsForStage(stage).criticality_level === 'high',
                                'text-yellow-600': getRfpDetailsForStage(stage).criticality_level === 'medium',
                                'text-green-600': getRfpDetailsForStage(stage).criticality_level === 'low'
                              }" class="font-medium">
                                {{ formatKey(getRfpDetailsForStage(stage).criticality_level) }}
                              </span>
                            </p>
                            <p v-if="getRfpDetailsForStage(stage).geographical_scope">
                              <strong class="text-gray-700">Geographical Scope:</strong> 
                              <span class="text-gray-900">{{ getRfpDetailsForStage(stage).geographical_scope }}</span>
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- Description -->
                    <div v-if="getRfpDetailsForStage(stage).description" class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                      <h5 class="text-sm font-semibold text-gray-900 mb-2">Description</h5>
                      <p class="text-sm text-gray-700 whitespace-pre-wrap">{{ getRfpDetailsForStage(stage).description }}</p>
                    </div>

                    <!-- Evaluation Criteria -->
                    <div v-if="getRfpDetailsForStage(stage).evaluation_criteria && getRfpDetailsForStage(stage).evaluation_criteria.length > 0" class="bg-indigo-50 rounded-lg p-4 border border-indigo-100">
                      <h5 class="text-sm font-semibold text-indigo-900 mb-3">Evaluation Criteria</h5>
                      <div class="space-y-3">
                        <div v-for="(criterion, index) in getRfpDetailsForStage(stage).evaluation_criteria" :key="index" class="bg-white rounded-lg p-3 border border-indigo-100">
                          <div class="flex items-start justify-between mb-2">
                            <h6 class="text-sm font-semibold text-gray-900">{{ criterion.criteria_name }}</h6>
                            <span class="text-xs font-medium text-indigo-600 bg-indigo-100 px-2 py-1 rounded">{{ criterion.weight_percentage }}%</span>
                          </div>
                          <p class="text-xs text-gray-600 mb-2">{{ criterion.criteria_description }}</p>
                          <div class="flex items-center space-x-4 text-xs">
                            <span class="text-gray-500">Type: <span class="font-medium text-gray-700">{{ formatKey(criterion.evaluation_type) }}</span></span>
                            <span v-if="criterion.is_mandatory" class="text-red-600 font-medium">Mandatory</span>
                            <span v-if="criterion.veto_enabled" class="text-orange-600 font-medium">Veto Enabled</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- Attached Documents -->
                    <div v-if="hasRfpDetails(stage)" class="bg-red-50 rounded-lg p-4 border border-red-100">
                      <h5 class="text-sm font-semibold text-red-900 mb-3 flex items-center space-x-2">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                        </svg>
                        <span>Attached Documents 
                          <span v-if="getRfpDetailsForStage(stage)?.documents && Array.isArray(getRfpDetailsForStage(stage).documents)">
                            ({{ getRfpDetailsForStage(stage).documents.length }})
                          </span>
                          <span v-else>(0)</span>
                        </span>
                      </h5>
                      
                      <!-- Documents List -->
                      <div v-if="getRfpDetailsForStage(stage)?.documents && Array.isArray(getRfpDetailsForStage(stage).documents) && getRfpDetailsForStage(stage).documents.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        <div
                          v-for="(doc, index) in getRfpDetailsForStage(stage).documents" 
                          :key="doc.id || doc.file_id || index"
                          @click="openDocument(doc)"
                          class="bg-white rounded-lg p-3 border border-red-200 hover:border-red-400 hover:shadow-md transition-all duration-200 group cursor-pointer"
                        >
                          <div class="flex items-center space-x-3">
                            <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center group-hover:bg-red-200 transition-colors">
                              <svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                              </svg>
                            </div>
                            <div class="flex-1 min-w-0">
                              <p class="text-sm font-medium text-gray-900 truncate">{{ getDocumentName(doc) }}</p>
                              <p class="text-xs text-gray-500">Click to open</p>
                              <p v-if="doc.file_type" class="text-xs text-gray-400 mt-1">{{ doc.file_type.toUpperCase() }}</p>
                            </div>
                            <svg class="w-4 h-4 text-gray-400 group-hover:text-red-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                            </svg>
                          </div>
                        </div>
                      </div>
                      
                      <!-- No Documents Message -->
                      <div v-else class="text-center py-6">
                        <div class="text-gray-400 mb-2">
                          <svg class="mx-auto h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path>
                          </svg>
                        </div>
                        <p class="text-sm text-gray-600">No documents attached to this RFP</p>
                      </div>
                    </div>

                    <!-- Compliance Requirements -->
                    <div v-if="getRfpDetailsForStage(stage).compliance_requirements && typeof getRfpDetailsForStage(stage).compliance_requirements === 'object' && !Array.isArray(getRfpDetailsForStage(stage).compliance_requirements) && Object.keys(getRfpDetailsForStage(stage).compliance_requirements).length > 0" class="bg-teal-50 rounded-lg p-4 border border-teal-100">
                      <h5 class="text-sm font-semibold text-teal-900 mb-3">Compliance Requirements</h5>
                      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div v-for="(value, key) in getRfpDetailsForStage(stage).compliance_requirements" :key="String(key)" class="bg-white rounded-lg p-3 border border-teal-100">
                          <p class="text-xs font-medium text-gray-500 uppercase">{{ formatKey(key) }}</p>
                          <p class="text-sm text-gray-900 mt-1">{{ formatValue(value) }}</p>
                        </div>
                      </div>
                    </div>

                    <!-- Custom Fields -->
                    <div v-if="getRfpDetailsForStage(stage).custom_fields && typeof getRfpDetailsForStage(stage).custom_fields === 'object' && !Array.isArray(getRfpDetailsForStage(stage).custom_fields) && Object.keys(getRfpDetailsForStage(stage).custom_fields).length > 0" class="bg-yellow-50 rounded-lg p-4 border border-yellow-100">
                      <h5 class="text-sm font-semibold text-yellow-900 mb-3">Additional Information</h5>
                      <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div v-for="(value, key) in getRfpDetailsForStage(stage).custom_fields" :key="String(key)" class="bg-white rounded-lg p-3 border border-yellow-100">
                          <p class="text-xs font-medium text-gray-500 uppercase">{{ formatKey(key) }}</p>
                          <p class="text-sm text-gray-900 mt-1">{{ formatValue(value) }}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- No RFP Details Message -->
              <div v-else class="bg-gray-50 rounded-lg p-8 text-center border border-gray-200">
                <div class="text-gray-400 mb-4">
                  <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                  </svg>
                </div>
                <h5 class="text-sm font-medium text-gray-900 mb-2">Complete RFP Information Not Loaded</h5>
                <p class="text-xs text-gray-500 mb-4">Click the button above to load the complete RFP details including all documents and evaluation criteria.</p>
              </div>
            </div>

              <!-- Proposal Evaluation Button -->
            <div v-if="isProposalEvaluation(stage)" class="mt-6 p-4 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-xl border border-purple-200 shadow-sm">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-3">
                  <div class="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                    <svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                  </div>
                  <div>
                    <h4 class="text-lg font-semibold text-gray-900">Proposal Evaluation Required</h4>
                    <p class="text-sm text-gray-600">This stage requires scoring and evaluation of the proposal</p>
                  </div>
                </div>
                <button 
                  @click="handleEvaluateProposal(stage)"
                  class="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all duration-200 font-medium shadow-sm hover:shadow-md"
                >
                  <span class="mr-2">📊</span>
                  Score Proposal
                </button>
              </div>
            </div>

              <!-- Stage Actions -->
            <div v-if="canMakeDecision(stage)" class="mt-6 p-6 bg-gradient-to-br from-gray-50 to-blue-50 rounded-xl border border-gray-200 shadow-sm">
              <div class="flex items-center space-x-3 mb-6">
                <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
                <h4 class="text-lg font-semibold text-gray-900">Stage Decision</h4>
              </div>
              
              <div class="space-y-6">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-4">Decision</label>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <!-- Approve Button -->
                    <button
                      @click="stageDecision.decision = 'APPROVE'"
                      :disabled="!canMakeDecision(stage)"
                      :class="[
                        'relative flex items-center justify-center px-4 py-3 rounded-lg border-2 transition-all duration-200 font-medium text-sm',
                        stageDecision.decision === 'APPROVE' 
                          ? 'border-green-500 bg-green-50 text-green-700 shadow-sm' 
                          : 'border-gray-200 bg-white text-gray-600 hover:border-green-300 hover:bg-green-25',
                        !canMakeDecision(stage) ? 'opacity-50 cursor-not-allowed' : ''
                      ]"
                    >
                      <div class="flex items-center space-x-2">
                        <div :class="[
                          'w-4 h-4 rounded-full border-2 flex items-center justify-center',
                          stageDecision.decision === 'APPROVE' 
                            ? 'border-green-500 bg-green-500' 
                            : 'border-gray-300'
                        ]">
                          <div v-if="stageDecision.decision === 'APPROVE'" class="w-2 h-2 bg-white rounded-full"></div>
                        </div>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                        <span>Approve</span>
                      </div>
                    </button>

                    <!-- Request Changes Button -->
                    <button
                      @click="stageDecision.decision = 'REQUEST_CHANGES'"
                      :disabled="!canMakeDecision(stage)"
                      :class="[
                        'relative flex items-center justify-center px-4 py-3 rounded-lg border-2 transition-all duration-200 font-medium text-sm',
                        stageDecision.decision === 'REQUEST_CHANGES' 
                          ? 'border-amber-500 bg-amber-50 text-amber-700 shadow-sm' 
                          : 'border-gray-200 bg-white text-gray-600 hover:border-amber-300 hover:bg-amber-25',
                        !canMakeDecision(stage) ? 'opacity-50 cursor-not-allowed' : ''
                      ]"
                    >
                      <div class="flex items-center space-x-2">
                        <div :class="[
                          'w-4 h-4 rounded-full border-2 flex items-center justify-center',
                          stageDecision.decision === 'REQUEST_CHANGES' 
                            ? 'border-amber-500 bg-amber-500' 
                            : 'border-gray-300'
                        ]">
                          <div v-if="stageDecision.decision === 'REQUEST_CHANGES'" class="w-2 h-2 bg-white rounded-full"></div>
                        </div>
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                        </svg>
                        <span>Request Changes</span>
                      </div>
                    </button>
                  </div>
                </div>

                <div v-if="stageDecision.decision === 'REQUEST_CHANGES'">
                  <label class="block text-sm font-medium text-gray-700 mb-2">Change Request</label>
                  <textarea
                      v-model="stageDecision.change_request"
                      :disabled="!canMakeDecision(stage)"
                      placeholder="Please describe what changes are needed..."
                    :class="[
                      'w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                      !canMakeDecision(stage) ? 'opacity-50 cursor-not-allowed bg-gray-100' : ''
                    ]"
                    rows="3"
                  ></textarea>
                  
                  <!-- Change request confirmation (no direct edit from reviewer) -->
                <div v-if="stageDecision.decision === 'REQUEST_CHANGES' && stageDecision.change_request" class="mt-4 p-4 bg-amber-50 rounded-lg border border-amber-200">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-3">
                      <div class="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center">
                        <svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                        </svg>
                      </div>
                      <div>
                        <h4 class="text-sm font-semibold text-amber-900">Change Request Created</h4>
                        <p class="text-xs text-amber-700">A change request has been sent to the RFP creator. They will be notified to make the requested changes.</p>
                      </div>
                    </div>
                    <div class="flex items-center space-x-2">
                      <button 
                        @click="viewChangeRequest(stage)"
                        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium flex items-center space-x-2"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                        </svg>
                        <span>View Request</span>
                      </button>
                    </div>
                  </div>
                </div>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Comments</label>
                  <textarea
                      v-model="stageDecision.comments"
                      :disabled="!canMakeDecision(stage)"
                      placeholder="Additional comments..."
                    :class="[
                      'w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                      !canMakeDecision(stage) ? 'opacity-50 cursor-not-allowed bg-gray-100' : ''
                    ]"
                    rows="2"
                  ></textarea>
                </div>

                <button 
                      @click="submitStageDecision(stage)"
                  :disabled="submitting || !canMakeDecision(stage)"
                  :class="[
                    'w-full sm:w-auto px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 font-medium shadow-sm hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2',
                    !canMakeDecision(stage) ? 'opacity-50 cursor-not-allowed' : ''
                  ]"
                >
                  <svg v-if="!submitting" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                  </svg>
                  <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>{{ submitting ? 'Submitting...' : 'Submit Decision' }}</span>
                </button>
              </div>
              </div>

              <!-- Waiting for Previous Stages - Sequential Workflow -->
            <div v-else-if="(stage.workflow_type === 'MULTI_LEVEL' || stage.workflow_type === 'SEQUENTIAL') && !arePreviousStagesApproved(stage) && (stage.stage_status === 'PENDING' || stage.stage_status === 'IN_PROGRESS')" class="mt-6 p-6 bg-yellow-50 rounded-xl border border-yellow-200 shadow-sm">
              <div class="flex items-center space-x-3 mb-4">
                <div class="w-8 h-8 bg-yellow-100 rounded-lg flex items-center justify-center">
                  <svg class="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
                <h4 class="text-lg font-semibold text-yellow-800">Waiting for Previous Stages</h4>
              </div>
              
              <div class="space-y-4">
                <div class="flex items-start space-x-3">
                  <svg class="w-5 h-5 text-yellow-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  <div>
                    <p class="text-sm text-yellow-700 font-medium">Sequential Approval Required</p>
                    <p class="text-sm text-yellow-600 mt-1">
                      This stage cannot be reviewed until all previous stages in the workflow have been approved. 
                      Please wait for the previous stage reviewers to complete their decisions.
                    </p>
                  </div>
                </div>
                
                <div class="bg-yellow-100 rounded-lg p-3">
                  <div class="flex items-center space-x-2">
                    <svg class="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span class="text-sm text-yellow-700 font-medium">Stage {{ stage.stage_order }} - {{ stage.stage_name }}</span>
                  </div>
                  <p class="text-xs text-yellow-600 mt-1">
                    You will be notified when this stage becomes available for review.
                  </p>
                </div>
              </div>
            </div>

              <!-- Decision Already Made - Frozen State -->
            <div v-else-if="hasUserMadeDecision(stage)" class="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div class="flex items-center space-x-2 mb-4">
                <div class="h-px bg-blue-300 flex-1"></div>
                <h4 class="text-sm font-medium text-blue-700 px-2">Decision Made</h4>
                <div class="h-px bg-blue-300 flex-1"></div>
              </div>
              
              <div class="bg-blue-100 border border-blue-300 rounded-md p-4 mb-4">
                <div class="flex items-start">
                  <svg class="w-5 h-5 text-blue-400 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                  </svg>
                  <div>
                    <h5 class="text-sm font-medium text-blue-800">Decision Submitted</h5>
                    <p class="text-sm text-blue-700 mt-1">
                      Your decision has been submitted and sent to the next level. The stage is now {{ getStageStatusLabel(stage.stage_status) }}.
                    </p>
                  </div>
                </div>
              </div>
              
              <div class="bg-white rounded-md p-4 border border-blue-200">
                <h4 class="text-sm font-medium text-gray-700 mb-3">Your Decision Summary:</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <p><strong class="text-gray-700">Decision:</strong> 
                      <span 
                        :class="getStatusBadgeClass(stage.stage_status)"
                        class="ml-2 px-2 py-1 text-xs font-medium rounded-full"
                      >
                      {{ getStageStatusLabel(stage.stage_status) }}
                      </span>
                    </p>
                    <p><strong class="text-gray-700">Completed:</strong> {{ formatDate(stage.completed_at) }}</p>
                  </div>
                  <div class="space-y-2">
                    <p v-if="stage.rejection_reason"><strong class="text-gray-700">Requested Changes:</strong> {{ stage.rejection_reason }}</p>
                    <p v-if="stage.response_data && stage.response_data.comments"><strong class="text-gray-700">Additional Comments:</strong> {{ stage.response_data.comments }}</p>
                  </div>
                </div>
                </div>
              </div>

              <!-- Stage History -->
            <div v-if="stage.stage_status !== 'PENDING'" class="mt-6 p-4 bg-gray-50 rounded-lg">
              <div class="flex items-center space-x-2 mb-3">
                <div class="h-px bg-gray-300 flex-1"></div>
                <h4 class="text-sm font-medium text-gray-700 px-2">Stage History</h4>
                <div class="h-px bg-gray-300 flex-1"></div>
              </div>
              <div class="space-y-2">
                <p><strong class="text-gray-700">Status:</strong> {{ getStageStatusLabel(stage.stage_status) }}</p>
                <p v-if="stage.completed_at"><strong class="text-gray-700">Completed:</strong> {{ formatDate(stage.completed_at) }}</p>
                <p v-if="stage.rejection_reason"><strong class="text-gray-700">Requested Changes:</strong> {{ stage.rejection_reason }}</p>
              </div>
              </div>

              <!-- Version Management -->
            <div class="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center space-x-2">
                  <div class="w-6 h-6 bg-blue-100 rounded-lg flex items-center justify-center">
                    <svg class="w-3 h-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                  </div>
                  <h4 class="text-lg font-semibold text-gray-900">Version Management</h4>
                </div>
                <div class="flex items-center space-x-2">
                  <button 
                    @click="loadVersionHistory(stage)"
                    :disabled="loadingVersions"
                    class="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    <svg v-if="!loadingVersions" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                    </svg>
                    <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>{{ loadingVersions ? 'Loading...' : 'Load History' }}</span>
                  </button>
                  <button 
                    @click="openVersionManager(stage)"
                    class="px-3 py-1 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm font-medium flex items-center space-x-2"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                    </svg>
                    <span>Manage Versions</span>
                  </button>
                </div>
              </div>

              <!-- Version History Content -->
              <div v-if="getVersionHistoryForStage(stage)" class="space-y-3">
                <div 
                  v-for="version in getVersionHistoryForStage(stage)" 
                  :key="version.version_id"
                  class="bg-white rounded-lg p-4 border border-blue-100 hover:border-blue-200 transition-colors"
                >
                  <div class="flex items-start justify-between mb-2">
                    <div class="flex items-center space-x-3">
                      <div class="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                        <span class="text-sm font-semibold text-blue-600">v{{ version.version_number }}</span>
                      </div>
                      <div>
                        <h5 class="text-sm font-semibold text-gray-900">{{ version.version_label }}</h5>
                        <p class="text-xs text-gray-500">{{ formatDate(version.created_at) }}</p>
                      </div>
                    </div>
                    <div class="flex items-center space-x-2">
                      <span 
                        :class="getVersionTypeBadgeClass(version.version_type)"
                        class="px-2 py-1 text-xs font-medium rounded-full"
                      >
                        {{ version.version_type }}
                      </span>
                      <span v-if="version.is_current" class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                        Current
                      </span>
                      <span v-if="version.is_approved" class="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                        Approved
                      </span>
                    </div>
                  </div>
                  
                  <div class="space-y-2">
                    <p class="text-sm text-gray-700">{{ version.changes_summary }}</p>
                    <div class="flex items-center space-x-4 text-xs text-gray-500">
                      <span>By: {{ version.created_by_name }} ({{ version.created_by_role }})</span>
                      <span v-if="version.change_reason">Reason: {{ version.change_reason }}</span>
                    </div>
                  </div>
                  
                  <!-- Version Actions -->
                  <div class="flex items-center space-x-2 mt-3">
                    <button 
                      @click="viewVersionDetails(version)"
                      class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs hover:bg-blue-200 transition-colors"
                    >
                      View Details
                    </button>
                    <button 
                      @click="compareVersion(version)"
                      class="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs hover:bg-purple-200 transition-colors"
                    >
                      Compare
                    </button>
                    <button 
                      v-if="!version.is_approved && canApproveVersion(version)"
                      @click="approveVersion(version)"
                      class="px-2 py-1 bg-green-100 text-green-700 rounded text-xs hover:bg-green-200 transition-colors"
                    >
                      Approve
                    </button>
                  </div>
                </div>
              </div>

              <!-- No Version History Message -->
              <div v-else class="text-center py-8">
                <div class="text-gray-400 mb-4">
                  <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
                <h5 class="text-sm font-medium text-gray-900 mb-2">No Version History</h5>
                <p class="text-xs text-gray-500 mb-4">Click the button above to load the version history for this approval request.</p>
              </div>
            </div>
            </div>
        </div>
      </div>

      <!-- No Stages Message -->
    <div v-else-if="selectedUserId && assignedStages.length === 0" class="text-center py-12">
      <div class="text-gray-400 mb-4">
        <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
      </div>
      <h3 class="text-lg font-medium text-gray-900 mb-2">
        {{ getUrlParams().stageId ? 'Stage not found' : 'No stages assigned' }}
      </h3>
      <p class="text-gray-600">
        {{ getUrlParams().stageId 
          ? 'The requested stage was not found or is not assigned to you.' 
          : 'You don\'t have any pending stages to review.' 
        }}
      </p>
      </div>

      <!-- Select User Message -->
    <div v-else class="text-center py-12">
      <div class="text-gray-400 mb-4">
        <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
        </svg>
      </div>
      <h3 class="text-lg font-medium text-gray-900 mb-2">Select your user ID</h3>
      <p class="text-gray-600">Choose your user ID from the dropdown above to see your assigned approval stages.</p>
    </div>
      </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { API_CONFIG, API_ENDPOINTS, apiCall } from '@/config/api.js'
import { useRfpApi } from '@/composables/useRfpApi'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'
import { getTprmApiUrl, getApiOrigin } from '@/utils/backendEnv'

// Router
const router = useRouter()

// Props
const props = defineProps({
  userId: {
    type: String,
    required: false
  }
})

// Get URL query parameters for MPA
const getUrlParams = () => {
  const urlParams = new URLSearchParams(window.location.search)
  return {
    userId: urlParams.get('userId'),
    stageId: urlParams.get('stageId'),
    approvalId: urlParams.get('approvalId'),
    workflowId: urlParams.get('workflowId')
  }
}
    const { showSuccess, showError, showWarning, showInfo } = useNotifications()
    
    // Get authenticated headers for axios requests
    const { getAuthHeaders } = useRfpApi()
    
    const selectedUserId = ref('')
    const users = ref([])
    const assignedStages = ref([])
    const allStagesForWorkflow = ref([]) // Store ALL stages including approved ones for checking dependencies
    const submitting = ref(false)
const stageDecision = reactive({
  decision: '',
  change_request: '',
  comments: ''
})
    const rfpDetails = ref({}) // Store complete RFP details
    const loadingRfpDetails = ref(false)
    const versionHistory = ref({}) // Store version history for each stage
    const loadingVersions = ref(false)

    onMounted(async () => {
      await loggingService.logPageView('RFP', 'Stage Reviewer')
      await fetchUsers()
      // Use userId from props, URL params, or default to user 1
      const urlParams = getUrlParams()
      selectedUserId.value = props.userId || urlParams.userId || '1'
      if (selectedUserId.value) {
        await fetchAssignedStages()
      }
    })

    const fetchUsers = async () => {
      try {
        const url = getTprmApiUrl('rfp-approval/users/')
        const data = await apiCall(url)
        users.value = data
      } catch (error) {
        console.error('Error fetching users:', error)
        // Fallback to mock data if API fails
        users.value = [
          {
            id: '1',
            username: 'admin',
            first_name: 'Admin',
            last_name: 'User',
            email: 'admin@company.com',
            role: 'Administrator',
            department: 'IT',
            is_active: true,
            full_name: 'Admin User',
            designation: 'Administrator'
          },
          {
            id: '2',
            username: 'manager',
            first_name: 'Manager',
            last_name: 'User',
            email: 'manager@company.com',
            role: 'Manager',
            department: 'Operations',
            is_active: true,
            full_name: 'Manager User',
            designation: 'Manager'
          }
        ]
        showMessage('Failed to fetch users, using fallback data', 'warning')
      }
    }

    const fetchRfpDetails = async (rfpId) => {
      // Ensure rfpId is not a Promise - if it is, await it
      let resolvedRfpId = rfpId
      if (rfpId && typeof rfpId.then === 'function') {
        console.log('⚠️ RFP ID is a Promise, awaiting resolution...')
        resolvedRfpId = await rfpId
      }
      
      if (!resolvedRfpId) {
        console.log('⚠️ No RFP ID provided to fetchRfpDetails')
        return null
      }
      
      // Convert to string to ensure it's not an object
      const rfpIdString = String(resolvedRfpId)
      
      try {
        loadingRfpDetails.value = true
        console.log('📡 Fetching RFP details for RFP ID:', rfpIdString)
        const url = getTprmApiUrl(`rfp-approval/rfp-details/${rfpIdString}/`)
        console.log('📡 API URL:', url)
        const data = await apiCall(url)
        console.log('✅ RFP Details fetched successfully:', data)
        console.log('📄 RFP Documents:', data.documents)
        console.log('📄 RFP Documents type:', typeof data.documents)
        console.log('📄 RFP Documents is array:', Array.isArray(data.documents))
        console.log('📄 RFP Documents length:', data.documents ? (Array.isArray(data.documents) ? data.documents.length : 'Not an array') : 'null/undefined')
        console.log('📋 RFP Evaluation Criteria:', data.evaluation_criteria)
        
        // Ensure documents is always an array
        if (data && !Array.isArray(data.documents)) {
          if (data.documents === null || data.documents === undefined) {
            data.documents = []
          } else if (typeof data.documents === 'string') {
            try {
              const parsed = JSON.parse(data.documents)
              data.documents = Array.isArray(parsed) ? parsed : []
            } catch (e) {
              console.warn('⚠️ Could not parse documents string:', e)
              data.documents = []
            }
          } else {
            data.documents = []
          }
        }
        
        console.log('📄 Final RFP Documents after processing:', data.documents)
        return data
      } catch (error) {
        console.error('❌ Error fetching RFP details:', error)
        console.error('❌ Error details:', error.message)
        return null
      } finally {
        loadingRfpDetails.value = false
      }
    }

    const extractRfpIdFromStage = async (stage) => {
      console.log('🔍 Extracting RFP ID from stage:', stage.stage_id)
      console.log('🔍 Full stage object:', JSON.stringify(stage, null, 2))
      
      // Try to extract RFP ID from different possible locations
      if (stage.rfp_id) {
        console.log('✅ Found RFP ID in stage.rfp_id:', stage.rfp_id)
        return stage.rfp_id
      }
      
      if (stage.request_data) {
        try {
          const requestData = typeof stage.request_data === 'string' 
            ? JSON.parse(stage.request_data) 
            : stage.request_data
          
          console.log('🔍 Parsed request_data:', requestData)
          console.log('🔍 request_data type:', typeof requestData)
          console.log('🔍 request_data keys:', requestData ? Object.keys(requestData) : 'null')
          
          // Check for RFP ID in various formats
          if (requestData.rfp_id) {
            console.log('✅ Found RFP ID in request_data.rfp_id:', requestData.rfp_id)
            return requestData.rfp_id
          }
          if (requestData.id) {
            console.log('✅ Found ID in request_data.id:', requestData.id)
            return requestData.id
          }
          if (requestData.rfpId) {
            console.log('✅ Found RFP ID in request_data.rfpId:', requestData.rfpId)
            return requestData.rfpId
          }
          
          // For array format (proposal evaluation)
          if (Array.isArray(requestData) && requestData.length > 0) {
            const firstItem = requestData[0]
            console.log('🔍 First item in array:', firstItem)
            if (firstItem.rfp_id) {
              console.log('✅ Found RFP ID in array first item:', firstItem.rfp_id)
              return firstItem.rfp_id
            }
            if (firstItem.id) {
              console.log('✅ Found ID in array first item:', firstItem.id)
              return firstItem.id
            }
          }
          
          // Deep search for RFP ID in nested objects
          console.log('🔍 Deep searching for RFP ID in request_data...')
          const deepSearch = (obj, path = '') => {
            if (!obj || typeof obj !== 'object') return null
            for (const [key, value] of Object.entries(obj)) {
              const currentPath = path ? `${path}.${key}` : key
              if (key === 'rfp_id' || key === 'id' || key === 'rfpId') {
                console.log(`✅ Found RFP ID at ${currentPath}:`, value)
                return value
              }
              if (typeof value === 'object' && value !== null) {
                const result = deepSearch(value, currentPath)
                if (result) return result
              }
            }
            return null
          }
          const deepResult = deepSearch(requestData)
          if (deepResult) {
            return deepResult
          }
        } catch (e) {
          console.error('❌ Error parsing request_data:', e)
        }
      }
      
      // Fallback: Try to get RFP ID from backend using approval_id
      if (stage.approval_id) {
        try {
          console.log('🔍 Attempting backend lookup for RFP ID using approval_id:', stage.approval_id)
          const response = await fetch(getTprmApiUrl(`rfp-approval/get-rfp-id-from-approval/${stage.approval_id}/`), {
            method: 'GET',
            headers: {
              ...getAuthHeaders(),
              'Content-Type': 'application/json',
            },
          })
          
          if (response.ok) {
            const data = await response.json()
            if (data.rfp_id) {
              console.log('✅ Found RFP ID from backend:', data.rfp_id)
              return data.rfp_id
            }
          } else {
            console.log('⚠️ Backend lookup failed with status:', response.status)
          }
        } catch (error) {
          console.log('⚠️ Backend lookup error:', error)
        }
      }
      
      console.log('⚠️ No RFP ID found in stage data')
      return null
    }

    const fetchAssignedStages = async () => {
      if (!selectedUserId.value) return
      
      try {
         const url = getTprmApiUrl(`rfp-approval/user-approvals/?user_id=${selectedUserId.value}`)
         const data = await apiCall(url)
         console.log('📡 API Response (user stages):', data.length, 'stages') // Debug log
         
         // Filter stages based on query parameters if provided
         let filteredData = data
         const urlParams = getUrlParams()
         const stageId = urlParams.stageId
         const workflowId = urlParams.workflowId
         
         let targetApprovalId = workflowId
         
         if (stageId) {
           // If specific stage ID is provided, find the approval ID
           const targetStage = data.find(stage => stage.stage_id === stageId)
           if (targetStage) {
             targetApprovalId = targetStage.approval_id
             filteredData = data.filter(stage => stage.approval_id === targetApprovalId)
             console.log('🔍 Filtered by stageId:', stageId, 'Approval ID:', targetApprovalId)
           } else {
             filteredData = data.filter(stage => stage.stage_id === stageId)
             console.log('🔍 Filtered by stageId:', stageId, 'Found stages:', filteredData.length)
           }
         } else if (workflowId) {
           // If workflow ID is provided, show stages from that workflow
           filteredData = data.filter(stage => stage.approval_id === workflowId)
           console.log('🔍 Filtered by workflowId:', workflowId, 'Found stages:', filteredData.length)
         }
         
         // CRITICAL: Fetch ALL stages for the workflow (not just user's stages) for dependency checking
         if (targetApprovalId) {
           console.log('🔍 Fetching ALL stages for approval:', targetApprovalId)
           try {
             const allStagesUrl = getTprmApiUrl(`rfp-approval/stages/?approval_id=${targetApprovalId}`)
             console.log('📡 All stages URL:', allStagesUrl)
             const allStagesData = await apiCall(allStagesUrl)
             console.log('✅ Fetched ALL stages for workflow:', allStagesData.length, 'stages')
             
             // Store ALL stages for dependency checking
             allStagesForWorkflow.value = allStagesData.map(stage => {
               let requestData = stage.request_data
               let requestDataDisplay = 'No data'
               
               if (requestData) {
                 if (typeof requestData === 'string') {
                   try {
                     const parsed = JSON.parse(requestData)
                     requestDataDisplay = JSON.stringify(parsed, null, 2)
                     requestData = parsed
                   } catch (e) {
                     requestDataDisplay = requestData
                   }
                 } else if (typeof requestData === 'object') {
                   requestDataDisplay = JSON.stringify(requestData, null, 2)
                 }
               }
               
               return {
                 ...stage,
                 request_data: requestData,
                 request_data_display: requestDataDisplay
               }
             })
             
             console.log('📊 All workflow stages stored:', allStagesForWorkflow.value.map(s => ({
               stage_id: s.stage_id,
               stage_order: s.stage_order,
               stage_name: s.stage_name,
               status: s.stage_status
             })))
           } catch (error) {
             console.error('⚠️ Failed to fetch all workflow stages, falling back to user stages:', error)
             // Fallback to user's stages if API call fails
             allStagesForWorkflow.value = filteredData.map(stage => {
               let requestData = stage.request_data
               let requestDataDisplay = 'No data'
               
               if (requestData) {
                 if (typeof requestData === 'string') {
                   try {
                     const parsed = JSON.parse(requestData)
                     requestDataDisplay = JSON.stringify(parsed, null, 2)
                     requestData = parsed
                   } catch (e) {
                     requestDataDisplay = requestData
                   }
                 } else if (typeof requestData === 'object') {
                   requestDataDisplay = JSON.stringify(requestData, null, 2)
                 }
               }
               
               return {
                 ...stage,
                 request_data: requestData,
                 request_data_display: requestDataDisplay
               }
             })
           }
         } else {
           // No specific approval ID, use filtered data
           allStagesForWorkflow.value = filteredData.map(stage => {
             let requestData = stage.request_data
             let requestDataDisplay = 'No data'
             
             if (requestData) {
               if (typeof requestData === 'string') {
                 try {
                   const parsed = JSON.parse(requestData)
                   requestDataDisplay = JSON.stringify(parsed, null, 2)
                   requestData = parsed
                 } catch (e) {
                   requestDataDisplay = requestData
                 }
               } else if (typeof requestData === 'object') {
                 requestDataDisplay = JSON.stringify(requestData, null, 2)
               }
             }
             
             return {
               ...stage,
               request_data: requestData,
               request_data_display: requestDataDisplay
             }
           })
         }
         
         // Show user's assigned stages for this workflow
         assignedStages.value = filteredData.map(stage => {
           let requestData = stage.request_data
           let requestDataDisplay = 'No data'
           
           if (requestData) {
             if (typeof requestData === 'string') {
               try {
                 const parsed = JSON.parse(requestData)
                 requestDataDisplay = JSON.stringify(parsed, null, 2)
                 requestData = parsed
               } catch (e) {
                 requestDataDisplay = requestData
               }
             } else if (typeof requestData === 'object') {
               requestDataDisplay = JSON.stringify(requestData, null, 2)
             }
           }
           
           return {
             ...stage,
             request_data: requestData,
             request_data_display: requestDataDisplay
           }
         })
         
         console.log('📊 Assigned stages to display:', assignedStages.value.length)
         
         // Automatically start review for PENDING stages that can be reviewed
         for (const stage of assignedStages.value) {
           if (stage.stage_status === 'PENDING' && canMakeDecision(stage)) {
             await startStageReview(stage)
           }
         }
         
         // Automatically load RFP details for each stage
         for (const stage of assignedStages.value) {
           const rfpId = await extractRfpIdFromStage(stage)
           if (rfpId) {
             console.log('🔍 Auto-loading RFP details for RFP ID:', rfpId)
             await loadRfpDetailsForStage(stage)
           } else {
             console.log('⚠️ No RFP ID found for stage:', stage.stage_id)
           }
         }
      } catch (error) {
        console.error('Error fetching assigned stages:', error)
         showMessage('Failed to fetch assigned stages', 'error')
      }
    }

const filterSequentialStages = async (stages) => {
  try {
    // Group stages by approval_id to check sequential dependencies
    const stageGroups = {}
    
    for (const stage of stages) {
      if (!stageGroups[stage.approval_id]) {
        stageGroups[stage.approval_id] = []
      }
      stageGroups[stage.approval_id].push(stage)
    }
    
    const filteredStages = []
    
    for (const [approvalId, groupStages] of Object.entries(stageGroups)) {
      // Sort by stage_order
      const sortedStages = groupStages.sort((a, b) => a.stage_order - b.stage_order)
      
      // Check if this is a multi-level workflow
      const isMultiLevel = sortedStages.some(stage => 
        stage.workflow_type === 'MULTI_LEVEL' || 
        stage.workflow_name?.toLowerCase().includes('multi level')
      )
      
      if (isMultiLevel) {
        console.log(`🔍 Multi-level workflow detected for approval ${approvalId}`)
        
        // Find the first stage that is not approved
        let firstUnapprovedIndex = -1
        for (let i = 0; i < sortedStages.length; i++) {
          if (sortedStages[i].stage_status !== 'APPROVED') {
            firstUnapprovedIndex = i
            break
          }
        }
        
        // Only show the first unapproved stage (or all if all are approved)
        if (firstUnapprovedIndex >= 0) {
          // Show only the first unapproved stage
          const availableStage = sortedStages[firstUnapprovedIndex]
          filteredStages.push(availableStage)
          console.log(`✅ Showing stage ${availableStage.stage_name} (order: ${availableStage.stage_order}) for approval ${approvalId}`)
        } else {
          // All stages are approved, show the last one
          const lastStage = sortedStages[sortedStages.length - 1]
          filteredStages.push(lastStage)
          console.log(`✅ All stages approved, showing last stage ${lastStage.stage_name} for approval ${approvalId}`)
        }
      } else {
        // Non-multi-level workflow, show all stages
        filteredStages.push(...sortedStages)
        console.log(`✅ Non-multi-level workflow, showing all stages for approval ${approvalId}`)
      }
    }
    
    return filteredStages
    
  } catch (error) {
    console.error('❌ Error filtering sequential stages:', error)
    // Return original data if filtering fails
    return stages
  }
}

    const submitStageDecision = async (stage) => {
      if (!stageDecision.decision) {
        showMessage('Please select a decision', 'warning')
        return
      }

      if (stageDecision.decision === 'REQUEST_CHANGES' && !stageDecision.change_request) {
        showMessage('Please describe the changes needed', 'warning')
        return
      }

      try {
        submitting.value = true

        const isRequestChanges = stageDecision.decision === 'REQUEST_CHANGES'
        const commentForApi = isRequestChanges ? stageDecision.change_request : stageDecision.comments
        
        const decisionData = {
          action: stageDecision.decision,
          user_id: selectedUserId.value,
          user_name: users.value.find(u => u.id === selectedUserId.value)?.first_name + ' ' + users.value.find(u => u.id === selectedUserId.value)?.last_name || 'Unknown',
          response_data: {
            decision: stageDecision.decision,
            comments: stageDecision.comments,
            change_request: stageDecision.change_request
          }
        }

        // Submit stage decision
        const url = getTprmApiUrl('rfp-approval/update-stage-status/')
        await apiCall(url, {
          method: 'POST',
          body: JSON.stringify({
            stage_id: stage.stage_id,
            status: stageDecision.decision,
            comments: commentForApi,
            response_data: decisionData.response_data
          })
        })
        
        // If requesting changes, create a change request
        if (stageDecision.decision === 'REQUEST_CHANGES') {
          await createChangeRequest(stage)
        }
        
        showMessage('Stage decision submitted successfully', 'success')
        
        // Reset form and refresh stages
        Object.assign(stageDecision, {
          decision: '',
          change_request: '',
          comments: ''
        })
        
        await fetchAssignedStages()
        
      } catch (error) {
        console.error('Error submitting stage decision:', error)
        showMessage(error.message || 'Failed to submit stage decision', 'error')
      } finally {
        submitting.value = false
      }
    }

const getStatusBadgeClass = (status) => {
      const statusMap = {
        'PENDING': 'bg-yellow-100 text-yellow-800',
        'IN_PROGRESS': 'bg-blue-100 text-blue-800',
        'APPROVED': 'bg-green-100 text-green-800',
    'REJECTED': 'bg-amber-100 text-amber-800',
        'SKIPPED': 'bg-gray-100 text-gray-800',
        'EXPIRED': 'bg-red-100 text-red-800',
        'CANCELLED': 'bg-gray-100 text-gray-800'
      }
      return statusMap[status] || 'bg-gray-100 text-gray-800'
    }

const getStageStatusLabel = (status) => {
  if (!status) {
    return 'Unknown'
  }
  if (status === 'REJECTED') {
    return 'Request Changes'
  }
  return formatKey(status.toLowerCase())
}

    const formatDate = (dateString) => {
      if (!dateString) return 'Not set'
      try {
        return new Date(dateString).toLocaleString()
      } catch {
        return dateString
      }
    }

    const canMakeDecision = (stage) => {
      // User can make decision if:
      // 1. Stage is PENDING or IN_PROGRESS
      // 2. Stage is assigned to the current user
      // 3. For MULTI_LEVEL/SEQUENTIAL workflows, if stage is rejected but overall status is not PENDING_DECISION
      if (stage.stage_status === 'PENDING' || stage.stage_status === 'IN_PROGRESS') {
        // For multi-level/sequential workflows, check if previous stages are approved
        if (stage.workflow_type === 'MULTI_LEVEL' || stage.workflow_type === 'SEQUENTIAL' || 
            stage.workflow_name?.toLowerCase().includes('multi level') ||
            stage.workflow_name?.toLowerCase().includes('sequential')) {
          return arePreviousStagesApproved(stage)
        }
        return true
      }
      
      // For MULTI_LEVEL/SEQUENTIAL workflows, if user rejected and it's sent to admin, they can't make another decision
      if ((stage.workflow_type === 'MULTI_LEVEL' || stage.workflow_type === 'SEQUENTIAL') && 
          stage.stage_status === 'REJECTED' && 
          stage.overall_status === 'PENDING') {
        return false
      }
      
      return false
    }

    const arePreviousStagesApproved = (stage) => {
      // For multi-level/sequential workflows, check if all previous stages are approved
      const isSequentialWorkflow = stage.workflow_type === 'MULTI_LEVEL' || 
                                   stage.workflow_type === 'SEQUENTIAL' ||
                                   stage.workflow_name?.toLowerCase().includes('multi level') ||
                                   stage.workflow_name?.toLowerCase().includes('sequential')
      
      console.log(`\n🔍 === Checking Previous Stages Approval ===`)
      console.log(`Stage: ${stage.stage_name} (Order: ${stage.stage_order}, Status: ${stage.stage_status})`)
      console.log(`Workflow Type: ${stage.workflow_type}`)
      console.log(`Is Sequential: ${isSequentialWorkflow}`)
      
      if (!isSequentialWorkflow) {
        console.log(`✅ Non-sequential workflow, no dependency check needed`)
        return true // Non-sequential workflows don't have sequential requirements
      }
      
      // If this is the first stage (stage_order = 1), it can always be processed
      if (stage.stage_order <= 1) {
        console.log(`✅ First stage (order ${stage.stage_order}), can always proceed`)
        return true
      }
      
      // For stages after the first, check if all previous stages are approved
      console.log(`📋 Checking dependencies for stage order ${stage.stage_order}...`)
      
      // Use allStagesForWorkflow instead of assignedStages to include ALL stages (even approved ones)
      const allStagesForApproval = allStagesForWorkflow.value.filter(s => s.approval_id === stage.approval_id)
      console.log(`📊 Total stages in workflow: ${allStagesForApproval.length}`)
      console.log(`📊 Stages:`, allStagesForApproval.map(s => ({
        order: s.stage_order,
        name: s.stage_name,
        status: s.stage_status,
        id: s.stage_id
      })))
      
      if (allStagesForApproval.length === 0) {
        console.error(`❌ ERROR: No stages found for approval ${stage.approval_id}!`)
        console.log(`⚠️ This means allStagesForWorkflow is empty or doesn't contain stages for this approval`)
        console.log(`⚠️ Fallback: Returning false to prevent premature approval`)
        return false
      }
      
      const sortedStages = allStagesForApproval.sort((a, b) => a.stage_order - b.stage_order)
      
      // Check all stages before the current one
      console.log(`🔍 Checking ${stage.stage_order - 1} previous stage(s)...`)
      for (let i = 0; i < stage.stage_order - 1; i++) {
        const previousStage = sortedStages[i]
        if (!previousStage) {
          console.error(`❌ ERROR: Previous stage at position ${i} (order ${i + 1}) not found!`)
          return false
        }
        
        console.log(`  Stage ${i + 1}: ${previousStage.stage_name} (Order: ${previousStage.stage_order}, Status: ${previousStage.stage_status})`)
        
        if (previousStage.stage_status !== 'APPROVED') {
          console.log(`❌ BLOCKED: Stage "${previousStage.stage_name}" (order ${previousStage.stage_order}) is ${previousStage.stage_status}, not APPROVED`)
          console.log(`❌ Current stage "${stage.stage_name}" cannot proceed until previous stage is approved`)
          return false
        } else {
          console.log(`  ✅ Stage ${previousStage.stage_order} is APPROVED`)
        }
      }
      
      console.log(`✅ SUCCESS: All ${stage.stage_order - 1} previous stage(s) are APPROVED!`)
      console.log(`✅ Stage "${stage.stage_name}" (order ${stage.stage_order}) can now be reviewed`)
      console.log(`=== End Previous Stages Check ===\n`)
      return true
    }

    const hasUserMadeDecision = (stage) => {
      // User has made a decision if:
      // 1. Stage is APPROVED, REJECTED, or has completed_at timestamp
      // 2. For MULTI_LEVEL workflows, if stage is REJECTED and overall status is PENDING_DECISION
      if (stage.stage_status === 'APPROVED' || stage.stage_status === 'REJECTED') {
        return true
      }
      
      if (stage.completed_at) {
        return true
      }
      
      return false
    }

    const showMessage = (message, type) => {
      // Use PopupService for consistent notifications
      if (type === 'error') {
        PopupService.error(message, 'Error')
      } else if (type === 'success') {
        PopupService.success(message, 'Success')
      } else if (type === 'warning') {
        PopupService.warning(message, 'Warning')
      } else {
        PopupService.success(message, 'Info')
      }
    }

     const goBack = () => {
       try {
         // Vue Router Navigation: Use router.push for proper SPA navigation
         router.push({ name: 'MyApprovals' })
       } catch (error) {
         console.error('Navigation error:', error)
         // Final fallback: go back in browser history
         window.history.back()
       }
     }

     const startStageReview = async (stage) => {
       try {
         // Only start review if stage is PENDING
         if (stage.stage_status === 'PENDING') {
           const url = getTprmApiUrl('rfp-approval/start-stage-review/')
           await apiCall(url, {
             method: 'POST',
             body: JSON.stringify({
               stage_id: stage.stage_id
             })
           })
           console.log(`Stage ${stage.stage_id} marked as IN_PROGRESS`)
           // Refresh the stages to show updated status
           await fetchAssignedStages()
         }
       } catch (error) {
         console.error('Error starting stage review:', error)
         // Don't show error message as this is automatic
       }
     }


     const formatKey = (key) => {
       // Handle non-string values
       if (typeof key !== 'string') {
         return String(key)
       }
       
       // Convert snake_case to Title Case
       return key
         .split('_')
         .map(word => word && word.length > 0 ? word.charAt(0).toUpperCase() + word.slice(1) : '')
         .join(' ')
     }

     const formatValue = (value) => {
       if (value === null || value === undefined) {
         return 'Not specified'
       }
       
       if (typeof value === 'boolean') {
         return value ? 'Yes' : 'No'
       }
       
       if (typeof value === 'number') {
         return value.toLocaleString()
       }
       
       if (typeof value === 'string') {
         // Check if it's a date string
         if (value.match(/^\d{4}-\d{2}-\d{2}/) || value.match(/^\d{4}-\d{2}-\d{2}T/)) {
           try {
             return new Date(value).toLocaleString()
           } catch (e) {
             return value
           }
         }
         return value
       }
       
       if (typeof value === 'object') {
         return JSON.stringify(value, null, 2)
       }
       
       return String(value)
     }

     const formatCriteriaValue = (value) => {
       if (value === null || value === undefined) {
         return 'Not specified'
       }
       
       if (typeof value === 'boolean') {
         return value ? 'Yes' : 'No'
       }
       
       if (typeof value === 'number') {
         return value.toLocaleString()
       }
       
       if (typeof value === 'string') {
         // Check if it's a date string
         if (value.match(/^\d{4}-\d{2}-\d{2}/) || value.match(/^\d{4}-\d{2}-\d{2}T/)) {
           try {
             return new Date(value).toLocaleString()
           } catch (e) {
             return value
           }
         }
         return value
       }
       
       if (typeof value === 'object') {
         return JSON.stringify(value, null, 2)
       }
       
       return String(value)
     }


     const hasRequestData = (stage) => {
       if (!stage.request_data) {
         return false
       }
       
       // Handle string data
       if (typeof stage.request_data === 'string') {
         try {
           const parsed = JSON.parse(stage.request_data)
           return parsed && typeof parsed === 'object' && Object.keys(parsed).length > 0
         } catch (e) {
           return stage.request_data.length > 0
         }
       }
       
       // Handle object data
       if (typeof stage.request_data === 'object') {
         return Object.keys(stage.request_data).length > 0
       }
       
       return false
     }

     const getRequestData = (stage) => {
       if (!stage.request_data) {
         return {}
       }
       
       // If request_data is a string, try to parse it as JSON
       if (typeof stage.request_data === 'string') {
         try {
           const parsed = JSON.parse(stage.request_data)
           return parsed
         } catch (e) {
           // Return as single field if not valid JSON
           return { 'Raw Data': stage.request_data }
         }
       }
       
       // Return object data as is
       return stage.request_data
     }

const handleEvaluateProposal = async (stage) => {
  try {
    console.log('🔍 DEBUG: Starting proposal evaluation process from StageReviewer')
    console.log('🔍 DEBUG: Full stage object:', JSON.stringify(stage, null, 2))
    console.log('🔍 DEBUG: Stage request_data type:', typeof stage.request_data)
    console.log('🔍 DEBUG: Stage request_data content:', stage.request_data)
    
    // Extract response_id from stage data or request_data
    let responseId = null
    
     // Try to get response_id from different possible locations
     if (stage.response_id) {
       responseId = stage.response_id
     } else if (stage.request_data) {
       try {
         const requestData = typeof stage.request_data === 'string' 
           ? JSON.parse(stage.request_data) 
           : stage.request_data
         console.log('Parsed request_data:', requestData)
         
         // Handle case where request_data is an array (proposal evaluation)
         if (Array.isArray(requestData) && requestData.length > 0) {
           const firstProposal = requestData[0]
           if (firstProposal && firstProposal.response_id) {
             responseId = firstProposal.response_id
             console.log('Found response_id in array:', responseId)
           }
         } else if (typeof requestData === 'object' && requestData !== null) {
           // Try multiple possible field names for the proposal/response ID
           responseId = requestData.response_id || 
                       requestData.proposal_id || 
                       requestData.rfp_response_id ||
                       requestData.id ||
                       requestData.proposalId ||
                       requestData.responseId
         }
       } catch (e) {
         console.log('Could not parse request_data:', e)
       }
     }
    
    // If still no response_id found, try to look it up from the backend
    if (!responseId) {
      console.log('No response_id found in stage data. Trying backend lookup...')
      console.log('Approval ID:', stage.approval_id)
      
       try {
         // Try to get proposal ID from backend
         const response = await fetch(getTprmApiUrl(`rfp-approval/get-proposal-id/${stage.approval_id}/`), {
           method: 'GET',
           headers: getAuthHeaders()
         })
         if (response.ok) {
           const data = await response.json()
           responseId = data.proposal_id
           console.log('Found proposal ID from backend:', responseId)
           console.log('All available response IDs:', data.all_response_ids)
         } else {
           console.log('Backend lookup failed, using approval_id as fallback')
           responseId = stage.approval_id
         }
       } catch (error) {
         console.log('Backend lookup error, using approval_id as fallback:', error)
         responseId = stage.approval_id
       }
    }
    
    if (!responseId) {
      PopupService.error('No proposal ID found for evaluation. Please check the stage data.', 'No Proposal ID')
      return
    }
    
    console.log('Using response_id:', responseId)
    
    // Navigate to ProposalEvaluation with response_id
    router.push({
      name: 'ProposalEvaluation',
      query: {
        response_id: responseId,
        userId: selectedUserId.value,
        stageId: stage.stage_id,
        approvalId: stage.approval_id
      }
    })
    
  } catch (error) {
    console.error('Error navigating to proposal evaluation:', error)
    PopupService.error('Failed to navigate to proposal evaluation. Please try again.', 'Navigation Failed')
  }
}

const isProposalEvaluation = (stage) => {
  // Check if this stage is for proposal evaluation
  const businessType = stage.business_object_type?.toLowerCase()
  const stageName = stage.stage_name?.toLowerCase()
  const requestTitle = stage.request_title?.toLowerCase()
  const workflowName = stage.workflow_name?.toLowerCase()
  
  // More specific checks to avoid false positives
  const hasProposalInTitle = requestTitle?.includes('proposal evaluation') || 
                            requestTitle?.includes('proposal -')
  const hasEvaluationWorkflow = workflowName?.includes('proposal evaluation') ||
                               workflowName?.includes('evaluation workflow')
  const hasContractBusinessType = businessType === 'contract' || businessType === 'evaluation'
  
  // Check if request_data contains actual proposal data (array format)
  let hasProposalData = false
  if (stage.request_data) {
    try {
      const requestData = typeof stage.request_data === 'string' 
        ? JSON.parse(stage.request_data) 
        : stage.request_data
      
      // Check if it's an array with proposal data
      if (Array.isArray(requestData) && requestData.length > 0) {
        const firstItem = requestData[0]
        hasProposalData = firstItem && firstItem.response_id && firstItem.vendor_name
      }
    } catch (e) {
      // Ignore parsing errors
    }
  }
  
  console.log('🔍 DEBUG: isProposalEvaluation check for stage:', {
    stage_id: stage.stage_id,
    businessType,
    stageName,
    requestTitle,
    workflowName,
    hasProposalInTitle,
    hasEvaluationWorkflow,
    hasContractBusinessType,
    hasProposalData,
    result: (hasProposalInTitle || hasEvaluationWorkflow) && hasProposalData
  })
  
  // Only show if there's actual proposal data
  // The workflow name or title might indicate proposal evaluation, but we need actual data
  return (hasProposalInTitle || hasEvaluationWorkflow || hasContractBusinessType) && hasProposalData
}

const loadRfpDetailsForStage = async (stage) => {
  console.log('🔄 Loading RFP details for stage:', stage.stage_id)
  const rfpId = await extractRfpIdFromStage(stage)
  if (rfpId) {
    console.log('✅ RFP ID extracted:', rfpId)
    const details = await fetchRfpDetails(rfpId)
    if (details) {
      console.log('✅ RFP details loaded and stored for stage:', stage.stage_id)
      rfpDetails.value[stage.stage_id] = details
    } else {
      console.log('⚠️ No RFP details returned for RFP ID:', rfpId)
    }
  } else {
    console.log('⚠️ Could not extract RFP ID for stage:', stage.stage_id)
  }
}

const getRfpDetailsForStage = (stage) => {
  const details = rfpDetails.value[stage.stage_id] || null
  if (details && !Array.isArray(details.documents)) {
    // Ensure documents is always an array
    if (details.documents === null || details.documents === undefined) {
      details.documents = []
    } else if (typeof details.documents === 'string') {
      try {
        const parsed = JSON.parse(details.documents)
        details.documents = Array.isArray(parsed) ? parsed : []
      } catch (e) {
        console.warn('⚠️ Could not parse documents string in getRfpDetailsForStage:', e)
        details.documents = []
      }
    } else {
      details.documents = []
    }
  }
  return details
}

const hasRfpDetails = (stage) => {
  return !!rfpDetails.value[stage.stage_id]
}

const getDocumentUrl = (document) => {
  console.log('📄 Getting document URL for:', document)
  console.log('📄 Document type:', typeof document)
  console.log('📄 Document keys:', document && typeof document === 'object' ? Object.keys(document) : 'N/A')
  
  let url = null
  
  // Handle different document formats
  if (typeof document === 'string') {
    url = document
    console.log('📄 Found URL as string:', url)
  } else if (document && typeof document === 'object') {
    // Try all possible URL field names
    const urlFields = ['url', 's3_url', 's3Url', 'download_url', 'downloadUrl', 'file_url', 'fileUrl', 'document_url', 'documentUrl']
    
    for (const field of urlFields) {
      if (document[field]) {
        url = document[field]
        console.log(`📄 Found URL in field "${field}":`, url)
        break
      }
    }
    
    // If still no URL found, check if document itself has a URL-like structure
    if (!url && document.path) {
      url = document.path
      console.log('📄 Found URL in path field:', url)
    }
  }
  
  console.log('📄 Extracted URL:', url)
  
  // If URL is relative, prepend backend URL
  if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
    // Check if it starts with /media/ or /static/
    const apiOrigin = getApiOrigin() || 'https://grc-tprm.vardaands.com'
    if (url.startsWith('/media/') || url.startsWith('/static/')) {
      url = `${apiOrigin}${url}`
    } else {
      // Assume it's a relative path, prepend backend URL
      url = `${apiOrigin}/${url}`
    }
  }
  
  console.log('📄 Final URL:', url)
  return url
}

const getDocumentName = (document) => {
  if (!document) {
    return 'Unknown Document'
  }
  
  if (typeof document === 'string') {
    const name = document.split('/').pop() || 'Document'
    return name.split('?')[0] // Remove query parameters
  }
  
  if (typeof document === 'object') {
    // Try various field names for document name
    const nameFields = [
      'document_name',
      'file_name', 
      'fileName',
      'name',
      'original_name',
      'originalName',
      'title',
      'filename'
    ]
    
    for (const field of nameFields) {
      if (document[field]) {
        return String(document[field])
      }
    }
    
    // If document has a URL, extract filename from it
    if (document.url) {
      const urlParts = document.url.split('/')
      const fileName = urlParts[urlParts.length - 1]
      if (fileName && fileName !== '') {
        return fileName.split('?')[0] // Remove query parameters
      }
    }
  }
  
  return 'Document'
}

const openDocument = async (document) => {
  const name = getDocumentName(document)
  
  console.log('📄 Opening document:', name)
  console.log('📄 Document object:', document)
  
  let url = getDocumentUrl(document)
  
  // If no URL found, try to fetch from s3_files table
  if (!url) {
    // Extract file ID from document object
    const fileId = document.id || document.file_id || document.s3_file_id || document.fileId
    
    if (fileId) {
      console.log('📄 No direct URL found, fetching from s3_files table with ID:', fileId)
      try {
        const fileUrl = getTprmApiUrl(`rfp-approval/document-url/${fileId}/`)
        const response = await apiCall(fileUrl)
        
        if (response.url) {
          url = response.url
          console.log('✅ Fetched URL from s3_files table:', url)
        } else {
          console.error('❌ No URL found in s3_files table response')
        }
      } catch (error) {
        console.error('❌ Error fetching document URL from s3_files:', error)
        showMessage('Unable to fetch document URL from database', 'error')
        return
      }
    } else {
      console.error('❌ No file ID found in document object')
      showMessage('Unable to open document: No file ID or URL found', 'error')
      return
    }
  }
  
  console.log('📄 Final Document URL:', url)
  
  if (!url) {
    showMessage('Unable to open document: No URL found', 'error')
    return
  }
  
  try {
    // Open document in new tab
    window.open(url, '_blank', 'noopener,noreferrer')
    console.log('✅ Document opened successfully')
  } catch (error) {
    console.error('❌ Error opening document:', error)
    showMessage(`Unable to open document: ${error.message}`, 'error')
  }
}

const loadVersionHistory = async (stage) => {
  try {
    loadingVersions.value = true
    console.log('🔄 Loading version history for approval:', stage.approval_id)
    
    const url = getTprmApiUrl(`rfp-approval/approval-version-history/${stage.approval_id}/`)
    const response = await apiCall(url)
    
    if (response.success && response.versions) {
      versionHistory.value[stage.approval_id] = response.versions
      console.log('✅ Version history loaded:', response.versions.length, 'versions')
    } else {
      console.log('⚠️ No version history found or API error')
      versionHistory.value[stage.approval_id] = []
    }
  } catch (error) {
    console.error('❌ Error loading version history:', error)
    showMessage('Failed to load version history', 'error')
    versionHistory.value[stage.approval_id] = []
  } finally {
    loadingVersions.value = false
  }
}

const getVersionHistoryForStage = (stage) => {
  return versionHistory.value[stage.approval_id] || null
}

const getVersionTypeBadgeClass = (versionType) => {
  const typeMap = {
    'INITIAL': 'bg-blue-100 text-blue-800',
    'REVISION': 'bg-yellow-100 text-yellow-800',
    'CONSOLIDATION': 'bg-purple-100 text-purple-800',
    'FINAL': 'bg-green-100 text-green-800'
  }
  return typeMap[versionType] || 'bg-gray-100 text-gray-800'
}

const getWorkflowStageCount = (stage) => {
  // For now, return a default count. In a real implementation, 
  // this would fetch the total stage count for the workflow
  return Math.max(stage.stage_order || 1, 2) // Default to 2 stages minimum
}

const getStageProgressClass = (stageNumber, currentStageOrder, currentStageStatus) => {
  if (stageNumber < currentStageOrder) {
    // Previous stages - should be approved
    return 'bg-green-500 text-white border-green-500'
  } else if (stageNumber === currentStageOrder) {
    // Current stage
    if (currentStageStatus === 'APPROVED') {
      return 'bg-green-500 text-white border-green-500'
    } else if (currentStageStatus === 'REJECTED') {
    return 'bg-amber-500 text-white border-amber-500'
    } else if (currentStageStatus === 'IN_PROGRESS') {
      return 'bg-blue-500 text-white border-blue-500'
    } else {
      return 'bg-yellow-500 text-white border-yellow-500'
    }
  } else {
    // Future stages - not yet available
    return 'bg-gray-200 text-gray-500 border-gray-300'
  }
}

const editRFPForChanges = async (stage) => {
  try {
    console.log('🔍 Starting RFP edit process from StageReviewer')
    console.log('🔍 Stage object:', JSON.stringify(stage, null, 2))
    
    // Extract RFP ID from stage data
    const rfpId = await extractRfpIdFromStage(stage)
    
    if (!rfpId) {
      showMessage('No RFP ID found for this stage. Cannot edit RFP.', 'error')
      return
    }
    
    console.log('✅ RFP ID extracted:', rfpId)
    
    // Create change request object
    const changeRequest = {
      id: `CR_${Date.now()}`,
      requestedBy: users.value.find(u => u.id === selectedUserId.value)?.first_name + ' ' + users.value.find(u => u.id === selectedUserId.value)?.last_name || 'Unknown User',
      requestDate: new Date().toISOString(),
      description: stageDecision.change_request || 'Changes requested by reviewer',
      stageId: stage.stage_id,
      approvalId: stage.approval_id,
      specificFields: [] // Could be populated based on the change request
    }
    
    console.log('📝 Change request created:', changeRequest)
    
    // Navigate to RFP edit page with change request context
    const editUrl = `/rfp-creation?mode=change_request&rfpId=${rfpId}&changeRequest=${encodeURIComponent(JSON.stringify(changeRequest))}`
    window.open(editUrl, '_blank')
    
    showMessage('Opening RFP editor with change request context', 'info')
    
  } catch (error) {
    console.error('Error opening RFP editor:', error)
    showMessage('Failed to open RFP editor. Please try again.', 'error')
  }
}

// Version Management Methods
const openVersionManager = (stage) => {
  try {
    console.log('🔍 Opening version manager for stage:', stage.stage_id)
    console.log('🔍 Approval ID:', stage.approval_id)
    
    // Navigate to version manager with approval ID
    router.push({
      name: 'VersionManager',
      query: {
        approvalId: stage.approval_id,
        userId: selectedUserId.value,
        stageId: stage.stage_id
      }
    })
  } catch (error) {
    console.error('Error opening version manager:', error)
    showMessage('Failed to open version manager. Please try again.', 'error')
  }
}

const viewVersionDetails = (version) => {
  try {
    console.log('🔍 Viewing version details:', version.version_id)
    
    // Create a modal or navigate to version details
    // For now, we'll show an alert with version details
    const details = `
Version: v${version.version_number}
Type: ${version.version_type}
Label: ${version.version_label || 'N/A'}
Created: ${formatDate(version.created_at)}
Created By: ${version.created_by_name} (${version.created_by_role})
Changes: ${version.changes_summary || 'No changes summary'}
Reason: ${version.change_reason || 'No reason provided'}
    `.trim()
    
    showMessage(details, 'info')
  } catch (error) {
    console.error('Error viewing version details:', error)
    showMessage('Failed to view version details.', 'error')
  }
}

const compareVersion = (version) => {
  try {
    console.log('🔍 Comparing version:', version.version_id)
    
    // Get current version for comparison
    const currentVersion = getVersionHistoryForStage(version)?.find(v => v.is_current)
    
    if (!currentVersion) {
      showMessage('No current version found for comparison.', 'warning')
      return
    }
    
    if (currentVersion.version_id === version.version_id) {
      showMessage('Cannot compare version with itself.', 'warning')
      return
    }
    
    // Show comparison details
    const comparison = `
Comparing:
- Version A: v${currentVersion.version_number} (${currentVersion.version_label || 'Current'})
- Version B: v${version.version_number} (${version.version_label || 'N/A'})

Changes in Version B:
${version.changes_summary || 'No changes summary'}

Reason for changes:
${version.change_reason || 'No reason provided'}
    `.trim()
    
    showMessage(comparison, 'info')
  } catch (error) {
    console.error('Error comparing versions:', error)
    showMessage('Failed to compare versions.', 'error')
  }
}

const canApproveVersion = (version) => {
  // User can approve version if:
  // 1. Version is not already approved
  // 2. User has appropriate permissions
  // 3. Version is current or latest
  return !version.is_approved && version.is_current
}

const approveVersion = async (version) => {
  try {
    console.log('🔍 Approving version:', version.version_id)
    
    const url = getTprmApiUrl(`rfp-approval/approval-request-versions/${version.version_id}/approve/`)
    const response = await apiCall(url, {
      method: 'POST',
      body: JSON.stringify({
        approved_by: selectedUserId.value,
        approved_by_name: users.value.find(u => u.id === selectedUserId.value)?.first_name + ' ' + users.value.find(u => u.id === selectedUserId.value)?.last_name || 'Unknown User',
        approved_at: new Date().toISOString()
      })
    })
    
    if (response.success) {
      showMessage('Version approved successfully', 'success')
      // Reload version history
      await loadVersionHistory({ approval_id: version.approval_id })
    } else {
      showMessage(response.message || 'Failed to approve version', 'error')
    }
  } catch (error) {
    console.error('Error approving version:', error)
    showMessage('Failed to approve version. Please try again.', 'error')
  }
}

// Change Request Methods
const createChangeRequest = async (stage) => {
  try {
    console.log('🔍 Creating change request for stage:', stage.stage_id)
    
    // Extract RFP ID from stage data
    const rfpId = await extractRfpIdFromStage(stage)
    
    if (!rfpId) {
      console.error('No RFP ID found for stage')
      return
    }
    
    const changeRequestData = {
      rfp_id: rfpId,
      approval_id: stage.approval_id,
      stage_id: stage.stage_id,
      requested_by: selectedUserId.value,
      requested_by_name: users.value.find(u => u.id === selectedUserId.value)?.first_name + ' ' + users.value.find(u => u.id === selectedUserId.value)?.last_name || 'Unknown User',
      requested_by_role: users.value.find(u => u.id === selectedUserId.value)?.role || 'Reviewer',
      change_request_description: stageDecision.change_request,
      specific_fields: [], // Could be populated based on the change request
      status: 'pending',
      priority: 'medium'
    }
    
    const url = getTprmApiUrl('rfp-approval/change-requests/')
    const response = await apiCall(url, {
      method: 'POST',
      body: JSON.stringify(changeRequestData)
    })
    
    if (response.success) {
      console.log('✅ Change request created successfully:', response.change_request_id)
      showMessage('Change request created and sent to RFP creator', 'success')
    } else {
      console.error('❌ Failed to create change request:', response.error)
      showMessage('Failed to create change request', 'error')
    }
  } catch (error) {
    console.error('❌ Error creating change request:', error)
    showMessage('Failed to create change request', 'error')
  }
}

const viewChangeRequest = (stage) => {
  try {
    console.log('🔍 Viewing change request for stage:', stage.stage_id)
    
    // Navigate to change request manager
    router.push({
      name: 'ChangeRequestManager',
      query: {
        stageId: stage.stage_id,
        approvalId: stage.approval_id,
        userId: selectedUserId.value
      }
    })
  } catch (error) {
    console.error('Error navigating to change request manager:', error)
    showMessage('Failed to open change request manager', 'error')
  }
}


</script>

<style scoped>
.stage-reviewer {
  min-height: 100vh;
  background-color: #f9fafb;
}
</style>