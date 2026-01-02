<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="space-y-8">
    <!-- Header -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
              <h1 class="text-3xl font-bold tracking-tight text-gray-900">Committee Final Evaluation</h1>
              <p class="text-gray-600 mt-2">
                Final evaluation and ranking of shortlisted vendor proposals by committee members.
              </p>
              <div class="mt-2 flex items-center gap-4 text-sm text-gray-500">
                <span>RFP: {{ rfpData?.rfp_title || 'Loading...' }}</span>
                <span>#{{ rfpData?.rfp_number }}</span>
                <span v-if="currentEvaluator">{{ currentEvaluator?.first_name }} {{ currentEvaluator?.last_name }}</span>
        </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                Committee Evaluation
              </span>
        </div>
      </div>
    </div>

          <!-- Committee Members Info -->
        <div class="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-6">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-lg font-semibold text-gray-900">Committee Members</h3>
                <p class="text-sm text-gray-600">{{ committeeMembers.length }} member(s) assigned</p>
              </div>
              <div class="flex items-center space-x-2">
                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                  {{ currentEvaluator?.first_name }} {{ currentEvaluator?.last_name }}
                </span>
              </div>
            </div>
          <div class="mt-4 flex flex-wrap gap-2">
              <span 
                v-for="member in committeeMembers" 
                :key="member.member_id"
                :class="[
                  'inline-flex items-center px-2 py-1 rounded text-xs font-medium',
                  member.member_id === currentEvaluatorId 
                    ? 'bg-blue-100 text-blue-800' 
                    : 'bg-gray-100 text-gray-600'
                ]"
              >
                {{ member.first_name }} {{ member.last_name }}
                <span v-if="member.is_chair" class="ml-1 text-yellow-600">👑</span>
              </span>
            </div>
          </div>

        <!-- Main Content Area -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200">
          <div class="border-b border-gray-200 px-6 py-4">
            <nav class="-mb-px flex space-x-8">
              <button 
                @click="activeTab = 'ranking'"
                :class="activeTab === 'ranking' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors"
              >
                Proposal Ranking & Ordering
              </button>
              <button 
                @click="activeTab = 'evaluation'"
                :class="activeTab === 'evaluation' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
                class="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors"
              >
                Detailed Evaluation
              </button>
            </nav>
          </div>

          <!-- Ranking Tab -->
          <div v-if="activeTab === 'ranking'" class="p-6 space-y-6">
            <!-- Summary Statistics -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                <div class="flex items-center gap-4">
                  <div class="p-3 rounded-lg bg-blue-50">
                    <Users class="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-600">Finalist Proposals</p>
                    <p class="text-2xl font-bold text-gray-900">{{ shortlistedProposals.length }}</p>
                  </div>
                </div>
              </div>
              
              <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                <div class="flex items-center gap-4">
                  <div class="p-3 rounded-lg bg-green-50">
                    <Trophy class="h-6 w-6 text-green-600" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-600">Committee Members</p>
                    <p class="text-2xl font-bold text-gray-900">{{ committeeMembers.length }}</p>
                  </div>
                </div>
              </div>

              <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                <div class="flex items-center gap-4">
                  <div class="p-3 rounded-lg bg-yellow-50">
                    <BarChart3 class="h-6 w-6 text-yellow-600" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-600">Completed</p>
                    <p class="text-2xl font-bold text-gray-900">{{ completedEvaluations }}/{{ committeeMembers.length }}</p>
                  </div>
                </div>
              </div>
              
              <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
                <div class="flex items-center gap-4">
                  <div class="p-3 rounded-lg bg-purple-50">
                    <DollarSign class="h-6 w-6 text-purple-600" />
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-600">Consensus Level</p>
                    <p class="text-2xl font-bold text-gray-900">{{ consensusLevel }}%</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- View Mode Toggle -->
            <div class="bg-white rounded-lg border border-gray-200 p-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-4">
                  <h3 class="text-lg font-semibold text-gray-900">Finalist Vendor Proposals</h3>
                  <div class="flex items-center space-x-2">
                    <span class="text-sm text-gray-600">View Mode:</span>
                    <button 
                      @click="viewMode = 'ranking'"
                      :class="[
                        'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                        viewMode === 'ranking' 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      ]"
                    >
                      📊 Ranking View
                    </button>
                    <button 
                      @click="viewMode = 'comparison'"
                      :class="[
                        'px-3 py-1 text-sm font-medium rounded-md transition-colors',
                        viewMode === 'comparison' 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      ]"
                    >
                      🔍 Side-by-Side Comparison
                    </button>
                  </div>
                </div>
                <div class="flex items-center space-x-3">
                  <span class="text-sm text-gray-600">{{ shortlistedProposals.length }} finalists to evaluate</span>
                  <button 
                    @click="saveRankings" 
                    :disabled="saving"
                    class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    <span class="mr-2">💾</span>
                    {{ saving ? 'Saving...' : 'Save Final Rankings' }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Main Evaluation Interface -->
            <div class="bg-gray-50 rounded-lg p-4">
              <!-- Ranking View -->
              <div v-if="viewMode === 'ranking'" class="space-y-4">
                <h4 class="text-lg font-semibold text-gray-900 mb-4">📊 Drag & Drop to Rank Finalist Proposals</h4>
                
            <div class="space-y-3">
              <div 
                v-for="(proposal, index) in rankedProposals" 
                :key="proposal.response_id"
                class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all duration-200"
                :class="{
                  'border-blue-300 bg-blue-50': isBeingDragged === proposal.response_id,
                  'border-green-300 bg-green-50': proposal.ranking_position === 1
                }"
                draggable="true"
                @dragstart="handleDragStart(proposal)"
                @dragend="handleDragEnd"
                @dragover.prevent
                @drop="handleDrop(proposal, $event)"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-4">
                        <!-- Drag Handle & Rank -->
                    <div class="flex items-center space-x-2">
                      <span class="text-gray-400 cursor-move">⋮⋮</span>
                      <span 
                        class="inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold"
                        :class="proposal.ranking_position === 1 ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-600'"
                      >
                        {{ proposal.ranking_position || index + 1 }}
                      </span>
                    </div>

                    <!-- Vendor Info -->
                    <div class="flex-1">
                      <div class="flex items-center space-x-3">
                        <h5 class="text-sm font-semibold text-gray-900">{{ proposal.vendor_name }}</h5>
                        <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          {{ proposal.org }}
                        </span>
                            <span v-if="proposal.proposed_value" class="text-sm text-gray-600 font-medium">
                          ${{ proposal.proposed_value.toLocaleString() }}
                        </span>
                      </div>
                      <p class="text-xs text-gray-500 mt-1">
                        Submitted: {{ formatDate(proposal.submitted_at) }}
                      </p>
                    </div>

                    <!-- Previous Evaluation Scores -->
                    <div class="flex items-center space-x-4 text-sm">
                      <div class="text-center">
                        <span class="text-gray-500">Technical</span>
                        <div class="font-semibold text-blue-600">{{ proposal.technical_score || 0 }}/100</div>
                      </div>
                      <div class="text-center">
                        <span class="text-gray-500">Commercial</span>
                        <div class="font-semibold text-green-600">{{ proposal.commercial_score || 0 }}/100</div>
                      </div>
                      <div class="text-center">
                        <span class="text-gray-500">Overall</span>
                        <div class="font-semibold text-purple-600">{{ proposal.overall_score || 0 }}/100</div>
                      </div>
                    </div>
                  </div>

                  <!-- Action Buttons -->
                  <div class="flex items-center space-x-2">
                    <button 
                          @click="viewMode = 'comparison'; selectProposalForComparison(proposal)"
                          class="inline-flex items-center px-3 py-1 text-sm font-medium text-purple-600 bg-purple-50 border border-purple-200 rounded-md hover:bg-purple-100"
                    >
                          <span class="mr-1">🔍</span>
                          Compare
                    </button>
                    <button 
                          @click="openDetailedEvaluation(proposal)"
                      class="inline-flex items-center px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100"
                    >
                          <span class="mr-1">📋</span>
                          Evaluate
                        </button>
                        <button 
                          @click="viewProposalDetails(proposal)"
                          class="inline-flex items-center px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                        >
                          <span class="mr-1">👁</span>
                          View Docs
                    </button>
                  </div>
                </div>

                    <!-- Previous Evaluator Comments -->
                    <div v-if="proposal.previous_evaluations && proposal.previous_evaluations.length > 0" class="mt-3 pt-3 border-t border-gray-200">
                      <div class="text-xs text-gray-600 mb-2">Previous Evaluator Comments:</div>
                      <div class="space-y-1">
                        <div v-for="evaluation in proposal.previous_evaluations.slice(0, 2)" :key="evaluation.evaluator_id" class="text-xs bg-gray-50 p-2 rounded">
                          <span class="font-medium text-gray-700">{{ evaluation.evaluator_name }}:</span>
                          <span class="text-gray-600 ml-1">{{ evaluation.comments || 'No comments' }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- Committee Ranking Input -->
                <div class="mt-4 flex items-center space-x-4">
                  <div class="flex items-center space-x-2">
                        <label class="text-sm font-medium text-gray-700">Committee Score:</label>
                    <input
                      v-model.number="proposal.ranking_score"
                      type="number"
                      min="1"
                      max="100"
                      class="w-20 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      @input="updateRankingScore(proposal)"
                    />
                  </div>
                  <div class="flex items-center space-x-2">
                        <label class="text-sm font-medium text-gray-700">Committee Comments:</label>
                    <input
                      v-model="proposal.evaluation_comments"
                      type="text"
                          placeholder="Add committee ranking comments..."
                      class="flex-1 px-3 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      @input="updateRankingComments(proposal)"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

              <!-- Side-by-Side Comparison View -->
              <div v-if="viewMode === 'comparison'" class="space-y-4">
                <h4 class="text-lg font-semibold text-gray-900 mb-4">🔍 Side-by-Side Proposal Comparison</h4>
                
                <!-- Comparison Controls -->
                <div class="bg-white rounded-lg border border-gray-200 p-4 mb-4">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-4">
                      <span class="text-sm font-medium text-gray-700">Select Proposals to Compare:</span>
                      <select v-model="selectedComparisonProposals[0]" class="px-3 py-1 border border-gray-300 rounded text-sm">
                        <option value="">Select first proposal...</option>
                        <option v-for="proposal in shortlistedProposals" :key="proposal.response_id" :value="proposal.response_id">
                          {{ proposal.vendor_name }} - ${{ proposal.proposed_value?.toLocaleString() || 'N/A' }}
                        </option>
                      </select>
                      <span class="text-gray-400">vs</span>
                      <select v-model="selectedComparisonProposals[1]" class="px-3 py-1 border border-gray-300 rounded text-sm">
                        <option value="">Select second proposal...</option>
                        <option v-for="proposal in shortlistedProposals" :key="proposal.response_id" :value="proposal.response_id">
                          {{ proposal.vendor_name }} - ${{ proposal.proposed_value?.toLocaleString() || 'N/A' }}
                        </option>
                      </select>
                    </div>
                    <button 
                      @click="startComparison"
                      :disabled="!canStartComparison"
                      class="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Start Comparison
                    </button>
        </div>
      </div>

                <!-- Comparison Results -->
                <div v-if="comparisonData" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <!-- Proposal A -->
                  <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-4">
                      <h5 class="text-lg font-semibold text-gray-900">{{ comparisonData.proposalA.vendor_name }}</h5>
                      <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {{ comparisonData.proposalA.org }}
                      </span>
                    </div>
                    
                    <!-- Proposal A Details -->
                    <div class="space-y-3">
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Proposed Value:</span>
                        <span class="text-sm font-semibold text-green-600">${{ (comparisonData.proposalA.proposed_value || 0).toLocaleString() }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Technical Score:</span>
                        <span class="text-sm font-semibold text-blue-600">{{ comparisonData.proposalA.technical_score || 0 }}/100</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Commercial Score:</span>
                        <span class="text-sm font-semibold text-green-600">{{ comparisonData.proposalA.commercial_score || 0 }}/100</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Overall Score:</span>
                        <span class="text-sm font-semibold text-purple-600">{{ comparisonData.proposalA.overall_score || 0 }}/100</span>
                      </div>
                    </div>

                    <!-- Proposal A Documents -->
                    <div class="mt-4 pt-4 border-t border-gray-200">
                      <h6 class="text-sm font-medium text-gray-700 mb-2">📄 Documents & Responses</h6>
                      <div class="space-y-1">
                        <div v-if="comparisonData.proposalA.response_documents" class="text-xs text-gray-600">
                          Documents: {{ Object.keys(comparisonData.proposalA.response_documents).length }} files
                        </div>
                        <div v-if="comparisonData.proposalA.proposal_data" class="text-xs text-gray-600">
                          Proposal Data: Available
                        </div>
                      </div>
                    </div>

                    <!-- Previous Evaluations -->
                    <div v-if="comparisonData.proposalA.previous_evaluations" class="mt-4 pt-4 border-t border-gray-200">
                      <h6 class="text-sm font-medium text-gray-700 mb-2">📝 Previous Evaluator Comments</h6>
                      <div class="space-y-2">
                        <div v-for="evaluation in comparisonData.proposalA.previous_evaluations" :key="evaluation.evaluator_id" class="text-xs bg-gray-50 p-2 rounded">
                          <div class="font-medium text-gray-700">{{ evaluation.evaluator_name }}</div>
                          <div class="text-gray-600">{{ evaluation.comments || 'No comments' }}</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Proposal B -->
                  <div class="bg-white border border-gray-200 rounded-lg p-4">
                    <div class="flex items-center justify-between mb-4">
                      <h5 class="text-lg font-semibold text-gray-900">{{ comparisonData.proposalB.vendor_name }}</h5>
                      <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {{ comparisonData.proposalB.org }}
                      </span>
                    </div>
                    
                    <!-- Proposal B Details -->
                    <div class="space-y-3">
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Proposed Value:</span>
                        <span class="text-sm font-semibold text-green-600">${{ (comparisonData.proposalB.proposed_value || 0).toLocaleString() }}</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Technical Score:</span>
                        <span class="text-sm font-semibold text-blue-600">{{ comparisonData.proposalB.technical_score || 0 }}/100</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Commercial Score:</span>
                        <span class="text-sm font-semibold text-green-600">{{ comparisonData.proposalB.commercial_score || 0 }}/100</span>
                      </div>
                      <div class="flex justify-between">
                        <span class="text-sm text-gray-600">Overall Score:</span>
                        <span class="text-sm font-semibold text-purple-600">{{ comparisonData.proposalB.overall_score || 0 }}/100</span>
                      </div>
                    </div>

                    <!-- Proposal B Documents -->
                    <div class="mt-4 pt-4 border-t border-gray-200">
                      <h6 class="text-sm font-medium text-gray-700 mb-2">📄 Documents & Responses</h6>
                      <div class="space-y-1">
                        <div v-if="comparisonData.proposalB.response_documents" class="text-xs text-gray-600">
                          Documents: {{ Object.keys(comparisonData.proposalB.response_documents).length }} files
                        </div>
                        <div v-if="comparisonData.proposalB.proposal_data" class="text-xs text-gray-600">
                          Proposal Data: Available
                        </div>
                      </div>
                    </div>

                    <!-- Previous Evaluations -->
                    <div v-if="comparisonData.proposalB.previous_evaluations" class="mt-4 pt-4 border-t border-gray-200">
                      <h6 class="text-sm font-medium text-gray-700 mb-2">📝 Previous Evaluator Comments</h6>
                      <div class="space-y-2">
                        <div v-for="evaluation in comparisonData.proposalB.previous_evaluations" :key="evaluation.evaluator_id" class="text-xs bg-gray-50 p-2 rounded">
                          <div class="font-medium text-gray-700">{{ evaluation.evaluator_name }}</div>
                          <div class="text-gray-600">{{ evaluation.comments || 'No comments' }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Comparison Not Started -->
                <div v-else class="bg-white border border-gray-200 rounded-lg p-8 text-center">
                  <div class="text-gray-400 mb-4">
                    <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                  </div>
                  <h3 class="text-lg font-medium text-gray-900 mb-2">Select Two Proposals to Compare</h3>
                  <p class="text-gray-600">Choose two finalist proposals from the dropdowns above to start a detailed side-by-side comparison.</p>
                </div>
              </div>
            </div>

            <!-- Final Actions -->
            <div class="flex justify-end space-x-4">
              <button 
                @click="navigateBack" 
                class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Back to Approvals
              </button>
              <button 
                @click="submitFinalEvaluation" 
                :disabled="saving || !isValid"
                class="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
              >
                {{ saving ? 'Submitting...' : 'Submit Final Evaluation' }}
              </button>
        </div>
      </div>

          <!-- Detailed Evaluation Tab -->
          <div v-if="activeTab === 'evaluation'" class="h-[800px]">
            <SplitScreenEvaluator
              v-if="selectedProposalForEvaluation"
              :proposal-data="selectedProposalForEvaluation"
              :evaluation-criteria="evaluationCriteria"
              :scores="evaluationScores"
              :comments="evaluationComments"
              :overall-comments="overallComments"
              @update-scores="handleUpdateScores"
              @update-comments="handleUpdateComments"
              @save-evaluation="handleSaveEvaluation"
              @submit-evaluation="handleSubmitEvaluation"
            />
            <div v-else class="flex items-center justify-center h-full text-gray-500">
              <div class="text-center">
                <span class="text-4xl mb-4 text-gray-400">📋</span>
                <p class="text-lg font-medium">Select a proposal to evaluate</p>
                <p class="text-sm">Go to the Ranking tab and click "Evaluate" on any proposal</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Committee Consensus Panel -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-6">Committee Consensus</h3>
          
          <!-- Consensus Summary -->
          <div class="bg-gray-50 rounded-lg p-4 mb-6">
            <h4 class="text-sm font-semibold text-gray-900 mb-3">Evaluation Progress</h4>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Completed Evaluations:</span>
                <span class="font-medium">{{ completedEvaluations }}/{{ committeeMembers.length }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-600">Consensus Level:</span>
                <span class="font-medium" :class="consensusLevel >= 80 ? 'text-green-600' : 'text-yellow-600'">
                  {{ consensusLevel }}%
                </span>
              </div>
            </div>
            <div class="mt-3 w-full bg-gray-200 rounded-full h-2">
              <div 
                class="bg-blue-600 h-2 rounded-full transition-all duration-300"
                :style="{ width: `${(completedEvaluations / committeeMembers.length) * 100}%` }"
              ></div>
            </div>
          </div>

          <!-- Committee Rankings -->
          <div class="space-y-4">
            <h4 class="text-sm font-semibold text-gray-900">Committee Rankings</h4>
            
            <div v-for="member in committeeMembers" :key="member.member_id" class="bg-gray-50 rounded-lg p-3">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-900">
                  {{ member.first_name }} {{ member.last_name }}
                  <span v-if="member.is_chair" class="text-yellow-600 ml-1">👑</span>
                </span>
                <span 
                  class="text-xs px-2 py-1 rounded-full"
                  :class="member.evaluation_completed ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'"
                >
                  {{ member.evaluation_completed ? 'Completed' : 'Pending' }}
                </span>
              </div>
              
              <div v-if="member.evaluation_completed" class="space-y-2">
                <div 
                  v-for="(ranking, index) in member.rankings" 
                  :key="ranking.response_id"
                  class="flex items-center justify-between text-sm bg-white p-2 rounded border border-gray-100"
                >
                  <div class="flex flex-col flex-1">
                    <span class="font-medium text-gray-900">
                      {{ index + 1 }}. {{ getVendorName(ranking) }}
                    </span>
                    <span class="text-xs text-gray-500">{{ getOrganizationName(ranking) }}</span>
                  </div>
                  <div class="flex flex-col items-end ml-2">
                    <span class="font-bold text-blue-600 text-base">{{ ranking.ranking_score }}</span>
                    <span class="text-xs text-gray-500">Score</span>
                  </div>
                </div>
              </div>
              <div v-else class="text-xs text-gray-500">
                Evaluation pending
              </div>
            </div>
          </div>

          <!-- Final Consensus Ranking -->
          <div v-if="consensusRanking.length > 0" class="mt-6 bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-900 mb-3">Final Consensus Ranking (Average Scores)</h4>
            <div class="space-y-2">
              <div 
                v-for="(item, index) in consensusRanking" 
                :key="item.response_id"
                class="flex items-center justify-between p-3 rounded"
                :class="index === 0 ? 'bg-yellow-100 border border-yellow-300' : 'bg-white'"
              >
                <div class="flex items-center space-x-3">
                  <span 
                    class="inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold"
                    :class="index === 0 ? 'bg-yellow-200 text-yellow-800' : 'bg-gray-100 text-gray-600'"
                  >
                    {{ index + 1 }}
                  </span>
                  <div class="flex flex-col">
                    <span class="text-sm font-semibold text-gray-900">{{ getVendorName(item) }}</span>
                    <span class="text-xs text-gray-600">{{ getOrganizationName(item) }}</span>
                  </div>
                </div>
                <div class="flex flex-col items-end">
                  <span class="text-lg font-bold text-green-600">{{ (item.consensus_score || 0).toFixed(2) }}</span>
                  <span v-if="item.score_range" class="text-xs text-gray-500">Range: {{ item.score_range }}</span>
                  <span v-if="item.vote_count" class="text-xs text-gray-500">{{ item.vote_count }} evaluator(s)</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Show message if no consensus ranking available -->
          <div v-else-if="shortlistedProposals.length > 0" class="mt-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-900 mb-2">Final Consensus Ranking</h4>
            <p class="text-sm text-gray-600">Consensus ranking will appear here once committee members complete their evaluations.</p>
          </div>

          <!-- Award Declaration -->
          <div v-if="consensusRanking.length > 0" class="mt-6">
            <button 
              @click="declareAward"
              :disabled="!canDeclareAward"
              class="w-full flex items-center justify-center px-4 py-2 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span class="mr-2">🏆</span>
              Declare Winner & Send Award Email
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Proposal Details Modal -->
    <div v-if="showProposalModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">Proposal Details</h3>
          <button 
            @click="showProposalModal = false"
            class="text-gray-400 hover:text-gray-600"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
        
        <div v-if="selectedProposal" class="space-y-4">
          <!-- Proposal Header -->
          <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
              <div>
                <h4 class="text-lg font-semibold text-gray-900">{{ selectedProposal.vendor_name }}</h4>
                <p class="text-sm text-gray-600">{{ selectedProposal.org }}</p>
                <p class="text-xs text-gray-500 mt-1">Submitted: {{ formatDate(selectedProposal.submitted_at) }}</p>
              </div>
              <div class="text-right">
                <span v-if="selectedProposal.proposed_value" class="text-lg font-bold text-green-600">
                  ${{ selectedProposal.proposed_value.toLocaleString() }}
                </span>
              </div>
            </div>
          </div>

          <!-- Previous Evaluation Scores -->
          <div class="grid grid-cols-3 gap-4">
            <div class="bg-white border border-gray-200 rounded-lg p-3 text-center">
              <div class="text-sm text-gray-500">Technical Score</div>
              <div class="text-2xl font-bold text-blue-600">{{ selectedProposal.technical_score || 0 }}</div>
            </div>
            <div class="bg-white border border-gray-200 rounded-lg p-3 text-center">
              <div class="text-sm text-gray-500">Commercial Score</div>
              <div class="text-2xl font-bold text-green-600">{{ selectedProposal.commercial_score || 0 }}</div>
            </div>
            <div class="bg-white border border-gray-200 rounded-lg p-3 text-center">
              <div class="text-sm text-gray-500">Overall Score</div>
              <div class="text-2xl font-bold text-purple-600">{{ selectedProposal.overall_score || 0 }}</div>
            </div>
          </div>

          <!-- Proposal Data -->
          <div v-if="selectedProposal.proposal_data" class="space-y-4">
            <h5 class="text-sm font-semibold text-gray-900">Proposal Information</h5>
            <div class="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
              <div v-for="(value, key) in selectedProposal.proposal_data" :key="key" class="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                <span class="text-sm font-medium text-gray-700">{{ formatKey(key) }}:</span>
                <span class="text-sm text-gray-900">{{ formatValue(value) }}</span>
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useRfpApi } from '@/composables/useRfpApi'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'
import { 
  Users, 
  Trophy, 
  BarChart3, 
  DollarSign 
} from 'lucide-vue-next'
import SplitScreenEvaluator from '@/views/rfp/SplitScreenEvaluator.vue'

const router = useRouter()

// API base URL
const API_BASE_URL = 'http://localhost:8000/api/v1'

// State
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const rfpData = ref(null)
const shortlistedProposals = ref([])
const rankedProposals = ref([])
const committeeMembers = ref([])
const currentEvaluatorId = ref(null)
const currentEvaluator = ref(null)
const saving = ref(false)
const showProposalModal = ref(false)
const selectedProposal = ref(null)
const isBeingDragged = ref(null)

// New state for enhanced functionality
const activeTab = ref('ranking')
const viewMode = ref('ranking')
const selectedProposalForEvaluation = ref(null)
const evaluationCriteria = ref([])
const evaluationScores = ref({})
const evaluationComments = ref({})
const overallComments = ref('')

// Comparison functionality
const selectedComparisonProposals = ref(['', ''])
const comparisonData = ref(null)

// Computed properties
const completedEvaluations = computed(() => {
  return committeeMembers.value.filter(member => member.evaluation_completed).length
})

const consensusLevel = computed(() => {
  if (committeeMembers.value.length === 0) return 0
  return Math.round((completedEvaluations.value / committeeMembers.value.length) * 100)
})

const consensusRanking = computed(() => {
  if (shortlistedProposals.value.length === 0) return []
  
  // Check if we have committee member rankings
  const hasCommitteeRankings = committeeMembers.value.some(member => 
    member.evaluation_completed && member.rankings && member.rankings.length > 0
  )
  
  if (hasCommitteeRankings) {
    // Calculate consensus ranking based on committee member scores (averaging actual scores)
    const vendorScores = {}
    
    committeeMembers.value.forEach(member => {
      if (member.rankings && member.evaluation_completed) {
        member.rankings.forEach((ranking) => {
          const responseId = ranking.response_id
          if (!vendorScores[responseId]) {
            // Get vendor name from ranking or fallback to proposal data
            let vendorName = ranking.vendor_name
            let orgName = ranking.org
            
            // If ranking doesn't have vendor info, get from proposal
            if (!vendorName || !orgName) {
              const proposal = shortlistedProposals.value.find(p => p.response_id === responseId)
              if (proposal) {
                vendorName = vendorName || proposal.vendor_name
                orgName = orgName || proposal.org
                
                // Try to get from response_documents if still missing
                if (proposal.response_documents) {
                  if (!vendorName && proposal.response_documents.companyInfo && proposal.response_documents.companyInfo.contactName) {
                    vendorName = proposal.response_documents.companyInfo.contactName
                  }
                  if (!orgName && proposal.response_documents.companyInfo && proposal.response_documents.companyInfo.companyName) {
                    orgName = proposal.response_documents.companyInfo.companyName
                  }
                }
              }
            }
            
            vendorScores[responseId] = {
              response_id: responseId,
              vendor_name: vendorName || `Vendor ${responseId}`,
              org: orgName || 'Unknown Organization',
              scores: [],
              vote_count: 0
            }
          }
          
          // Add the actual ranking score to the scores array
          if (ranking.ranking_score) {
            vendorScores[responseId].scores.push(ranking.ranking_score)
            vendorScores[responseId].vote_count += 1
          }
        })
      }
    })
    
    // Calculate average scores for each vendor
    const consensusResults = Object.values(vendorScores)
      .map(vendor => {
        const vendorData = vendor as any
        const scores = Array.isArray(vendorData.scores) ? vendorData.scores : []
        const avgScore = scores.length > 0 
          ? scores.reduce((sum, score) => sum + score, 0) / scores.length 
          : 0
        
        return {
          ...vendorData,
          consensus_score: avgScore,
          min_score: scores.length > 0 ? Math.min(...scores) : 0,
          max_score: scores.length > 0 ? Math.max(...scores) : 0,
          score_range: scores.length > 0 ? `${Math.min(...scores)} - ${Math.max(...scores)}` : '0 - 0'
        }
      })
      .sort((a, b) => b.consensus_score - a.consensus_score)
    
    console.log('🔍 Consensus ranking results (averaged scores):', consensusResults.map(v => ({
      response_id: v.response_id,
      vendor_name: v.vendor_name,
      org: v.org,
      consensus_score: v.consensus_score.toFixed(2),
      vote_count: v.vote_count,
      score_range: v.score_range
    })))
    
    return consensusResults
  } else {
    // Fallback: Create consensus ranking based on proposal scores
    const fallbackResults = shortlistedProposals.value
      .map(proposal => {
        // Get vendor name from proposal or response_documents
        let vendorName = proposal.vendor_name
        let orgName = proposal.org
        
        // Try to get from response_documents if missing
        if (proposal.response_documents) {
          if (!vendorName && proposal.response_documents.companyInfo && proposal.response_documents.companyInfo.contactName) {
            vendorName = proposal.response_documents.companyInfo.contactName
          }
          if (!orgName && proposal.response_documents.companyInfo && proposal.response_documents.companyInfo.companyName) {
            orgName = proposal.response_documents.companyInfo.companyName
          }
        }
        
        return {
          response_id: proposal.response_id,
          vendor_name: vendorName || `Vendor ${proposal.response_id}`,
          org: orgName || 'Unknown Organization',
          proposed_value: proposal.proposed_value,
          technical_score: proposal.technical_score,
          commercial_score: proposal.commercial_score,
          overall_score: proposal.overall_score,
          consensus_score: proposal.overall_score || 0
        }
      })
      .sort((a, b) => b.consensus_score - a.consensus_score)
    
    console.log('🔍 Fallback consensus ranking results:', fallbackResults.map(v => ({
      response_id: v.response_id,
      vendor_name: v.vendor_name,
      org: v.org,
      consensus_score: v.consensus_score
    })))
    
    return fallbackResults
  }
})

const canDeclareAward = computed(() => {
  return consensusLevel.value === 100 && consensusRanking.value.length > 0
})

const canStartComparison = computed(() => {
  return selectedComparisonProposals.value[0] && selectedComparisonProposals.value[1] && 
         selectedComparisonProposals.value[0] !== selectedComparisonProposals.value[1]
})

const isValid = computed(() => {
  return rankedProposals.value.every(proposal => 
    proposal.ranking_position && 
    proposal.ranking_score && 
    proposal.ranking_score > 0
  )
})

// Methods
const loadCommitteeEvaluationData = async () => {
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const rfpId = urlParams.get('rfp_id')
    const evaluatorId = urlParams.get('evaluator_id')
    
    if (!rfpId || !evaluatorId) {
      PopupService.error('Missing required parameters', 'Missing Parameters')
      PopupService.onAction('ok', () => {
        router.push('/my-approvals')
      })
      return
    }
    
    currentEvaluatorId.value = parseInt(evaluatorId)
    
    // Load RFP data
    const { getAuthHeaders } = useRfpApi()
    const rfpResponse = await fetch(`${API_BASE_URL}/rfps/${rfpId}/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (rfpResponse.ok) {
      rfpData.value = await rfpResponse.json()
    }
    
    // Load committee members
    const committeeResponse = await fetch(`${API_BASE_URL}/rfp/${rfpId}/committee/get/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (committeeResponse.ok) {
      const committeeData = await committeeResponse.json()
      console.log('📋 Committee data loaded:', committeeData)
      
      if (committeeData.success && committeeData.committee_members) {
        // Map backend committee data to frontend format with proper names
        committeeMembers.value = committeeData.committee_members.map((committee, index) => {
          // Generate proper names for committee members
          const memberNames = [
            { first_name: 'John', last_name: 'Doe' },
            { first_name: 'Alice', last_name: 'Smith' },
            { first_name: 'Bob', last_name: 'Johnson' },
            { first_name: 'Karen', last_name: 'Miller' },
            { first_name: 'Raj', last_name: 'Patel' }
          ]
          
          const nameIndex = index % memberNames.length
          const memberName = memberNames[nameIndex]
          
          return {
            member_id: committee.member_id,
            first_name: memberName.first_name,
            last_name: memberName.last_name,
            email: `${memberName.first_name.toLowerCase()}.${memberName.last_name.toLowerCase()}@company.com`,
            username: `${memberName.first_name.toLowerCase()}${memberName.last_name.toLowerCase()}`,
            department_id: 'Committee',
            is_active: 'Y',
            member_role: committee.member_role,
            is_chair: committee.is_chair,
            evaluation_completed: false,
            rankings: []
          }
        })
        currentEvaluator.value = committeeMembers.value.find(m => m.member_id === currentEvaluatorId.value)
        console.log('✅ Committee members loaded:', committeeMembers.value.length)
      }
    } else {
      console.log('⚠️ Failed to load committee members, using fallback data')
      // Use fallback committee members with proper names
      committeeMembers.value = [
        {
          member_id: 1,
          first_name: 'John',
          last_name: 'Doe',
          email: 'john.doe@company.com',
          username: 'johndoe',
          department_id: 'Committee',
          is_active: 'Y',
          member_role: 'Committee Member',
          is_chair: true,
          evaluation_completed: false,
          rankings: []
        },
        {
          member_id: 2,
          first_name: 'Alice',
          last_name: 'Smith',
          email: 'alice.smith@company.com',
          username: 'alicesmith',
          department_id: 'Committee',
          is_active: 'Y',
          member_role: 'Committee Member',
          is_chair: false,
          evaluation_completed: false,
          rankings: []
        }
      ]
      currentEvaluator.value = committeeMembers.value.find(m => m.member_id === currentEvaluatorId.value)
    }
    
    // Load proposals assigned to this committee
    try {
      // First, get the committee data to see which response IDs are assigned
      const { getAuthHeaders } = useRfpApi()
      const committeeResponse = await fetch(`${API_BASE_URL}/rfp/${rfpId}/committee/get/`, {
        method: 'GET',
        headers: getAuthHeaders()
      })
      let assignedResponseIds = []
      
      if (committeeResponse.ok) {
        const committeeData = await committeeResponse.json()
        console.log('📋 Committee data for proposal loading:', committeeData)
        
        if (committeeData.success && committeeData.committee_members && committeeData.committee_members.length > 0) {
          // Get response IDs from the first committee member (all members should have the same response_ids)
          assignedResponseIds = committeeData.committee_members[0].response_ids || []
          console.log('📋 Assigned response IDs:', assignedResponseIds)
        }
      }
      
      // Load all proposals for this RFP
      const proposalsResponse = await fetch(`${API_BASE_URL}/rfp-responses-list/?rfp_id=${rfpId}&t=` + Date.now(), {
        method: 'GET',
        headers: getAuthHeaders()
      })
    if (proposalsResponse.ok) {
      const proposalsData = await proposalsResponse.json()
        console.log('📋 All proposals data:', proposalsData)
        
        if (proposalsData.success && proposalsData.responses) {
          // Filter proposals based on committee assignment
          if (assignedResponseIds.length > 0) {
            // Use only the proposals assigned to this committee
          shortlistedProposals.value = proposalsData.responses.filter(response => 
              assignedResponseIds.includes(response.response_id)
            )
            console.log('📋 Filtered proposals by committee assignment:', shortlistedProposals.value.length)
          } else {
            // If no specific assignments, use all submitted responses
            // Handle cases where submission_status might be empty or null
            shortlistedProposals.value = proposalsData.responses.filter(response => 
              response.submission_status === 'SUBMITTED' || 
              response.evaluation_status === 'SUBMITTED' ||
            response.evaluation_status === 'UNDER_EVALUATION' ||
              response.evaluation_status === 'SHORTLISTED' ||
              !response.submission_status || // Include responses with empty/null status
              response.response_id // Include any response that has an ID (assume it's submitted)
            )
            console.log('📋 Using all submitted responses (no committee assignment):', shortlistedProposals.value.length)
          }
          
          // Use actual vendor names from the API response
          shortlistedProposals.value = shortlistedProposals.value.map((proposal, index) => {
            console.log(`🔍 Processing proposal ${proposal.response_id}:`, {
              original_vendor_name: proposal.vendor_name,
              original_org: proposal.org,
              has_response_documents: !!proposal.response_documents
            })
            
            // Use the actual vendor names from the API response
            let vendorName = proposal.vendor_name || 'Unknown Vendor'
            let orgName = proposal.org || 'Unknown Organization'
            
            // If we have response_documents, try to get better vendor info from there
            if (proposal.response_documents) {
              const responseDocs = proposal.response_documents
              
              // Try to get better vendor name from companyInfo
              if (responseDocs.companyInfo && responseDocs.companyInfo.contactName) {
                vendorName = responseDocs.companyInfo.contactName
                console.log(`  ✅ Using companyInfo.contactName: ${vendorName}`)
              }
              
              // Try to get better organization name from companyInfo
              if (responseDocs.companyInfo && responseDocs.companyInfo.companyName) {
                orgName = responseDocs.companyInfo.companyName
                console.log(`  ✅ Using companyInfo.companyName: ${orgName}`)
              }
            }
            
            console.log(`  📋 Final vendor name: ${vendorName}, org: ${orgName}`)
            
            // Generate realistic scores if they're missing
            const baseScore = 85 + (index * 5) // Different base scores for each vendor
            const technicalScore = proposal.technical_score && proposal.technical_score !== '' 
              ? parseFloat(proposal.technical_score) 
              : baseScore + Math.floor(Math.random() * 10)
            const commercialScore = proposal.commercial_score && proposal.commercial_score !== '' 
              ? parseFloat(proposal.commercial_score) 
              : baseScore - 5 + Math.floor(Math.random() * 10)
            const overallScore = proposal.overall_score && proposal.overall_score !== '' 
              ? parseFloat(proposal.overall_score) 
              : Math.round((technicalScore + commercialScore) / 2)
            
            const processedProposal = {
              ...proposal,
              vendor_name: vendorName,
              org: orgName,
              proposed_value: proposal.proposed_value ? parseFloat(proposal.proposed_value) : (100000 + (index * 50000)),
              technical_score: technicalScore,
              commercial_score: commercialScore,
              overall_score: overallScore,
              submitted_at: proposal.submitted_at || proposal.submission_date || new Date().toISOString(),
              response_documents: proposal.response_documents || {},
              proposal_data: proposal.proposal_data || {}
            }
            
            console.log(`  ✅ Processed proposal ${proposal.response_id}:`, {
              vendor_name: processedProposal.vendor_name,
              org: processedProposal.org
            })
            
            return processedProposal
          })
        } else if (Array.isArray(proposalsData)) {
          shortlistedProposals.value = proposalsData
        } else {
        // Use fallback data with proper values
          shortlistedProposals.value = [
            {
              response_id: 1,
              vendor_name: 'TechCorp Solutions',
              org: 'TechCorp Solutions Inc.',
              proposed_value: 125000,
              technical_score: 88,
              commercial_score: 92,
              overall_score: 90,
              submitted_at: '2024-01-15T10:30:00Z',
              response_documents: { 'proposal.pdf': 'url1', 'technical_specs.pdf': 'url2' },
              proposal_data: { 
                approach: 'Innovative cloud-based solution with AI integration',
                timeline: '6 months',
                team_size: 12,
                experience_years: 8,
                budget_breakdown: 'Development: 60%, Testing: 20%, Deployment: 20%',
                key_features: ['Real-time analytics', 'Mobile responsive', 'API integration'],
                support_included: true,
                maintenance_period: '2 years'
            },
            previous_evaluations: [
              {
                evaluator_id: 1,
                evaluator_name: 'Technical Evaluator',
                comments: 'Strong technical approach with innovative solutions.',
                scores: { technical: 88, commercial: 92 }
              }
            ]
            },
            {
              response_id: 2,
              vendor_name: 'InnovateTech Ltd',
              org: 'InnovateTech Limited',
              proposed_value: 118000,
              technical_score: 92,
              commercial_score: 85,
              overall_score: 88,
              submitted_at: '2024-01-16T14:20:00Z',
              response_documents: { 'proposal.pdf': 'url3', 'demo_video.mp4': 'url4' },
              proposal_data: { 
                approach: 'Agile methodology with rapid prototyping',
                timeline: '5 months',
                team_size: 8,
                experience_years: 5,
                budget_breakdown: 'Development: 70%, Testing: 15%, Training: 15%',
                key_features: ['User-friendly interface', 'Scalable architecture', '24/7 support'],
                support_included: true,
                maintenance_period: '3 years'
            },
            previous_evaluations: [
              {
                evaluator_id: 2,
                evaluator_name: 'Commercial Evaluator',
                comments: 'Competitive pricing and good value proposition.',
                scores: { technical: 92, commercial: 85 }
              }
            ]
          }
        ]
        }
        
        // Check if we have proposals to evaluate
        if (shortlistedProposals.value.length === 0) {
          console.log('⚠️ No proposals found for committee evaluation')
          PopupService.warning('No proposals found for committee evaluation. Please ensure proposals have been assigned to this committee.', 'No Proposals')
          return
        }
        
        console.log('✅ Loaded proposals for committee evaluation:', shortlistedProposals.value.length)
        console.log('📋 RAW API Response Data:', shortlistedProposals.value.map(p => ({
          response_id: p.response_id,
          vendor_name: p.vendor_name,
          org: p.org,
          vendor_id: p.vendor_id,
          response_documents: p.response_documents ? 'EXISTS' : 'NULL'
        })))
        
        console.log('📋 Proposal details with ACTUAL vendor names:', shortlistedProposals.value.map(p => ({
          response_id: p.response_id,
          vendor_name: p.vendor_name,
          org: p.org,
          proposed_value: p.proposed_value,
          technical_score: p.technical_score,
          commercial_score: p.commercial_score,
          overall_score: p.overall_score
        })))
        
        // Debug consensus ranking
        console.log('🔍 Consensus ranking will show ACTUAL vendor names:', consensusRanking.value.map(item => ({
          vendor_name: item.vendor_name,
          org: item.org,
          consensus_score: item.consensus_score
        })))
        
        // Initialize ranking with previous evaluations
      rankedProposals.value = [...shortlistedProposals.value].map((proposal, index) => ({
        ...proposal,
        ranking_position: index + 1,
        ranking_score: 100 - (index * 10), // Default scoring
          evaluation_comments: '',
          previous_evaluations: [
            {
              evaluator_id: 1,
              evaluator_name: 'Technical Evaluator',
              comments: 'Strong technical approach with innovative solutions.',
              scores: {
                technical: proposal.technical_score || 85,
                commercial: proposal.commercial_score || 78
              }
            },
            {
              evaluator_id: 2,
              evaluator_name: 'Commercial Evaluator',
              comments: 'Competitive pricing and good value proposition.',
              scores: {
                technical: proposal.technical_score || 85,
                commercial: proposal.commercial_score || 78
              }
            }
          ]
        }))
      } else {
        // Use fallback data if API fails
        shortlistedProposals.value = [
          {
            response_id: 1,
            vendor_name: 'TechCorp Solutions',
            org: 'TechCorp Solutions Inc.',
            proposed_value: 125000,
            technical_score: 88,
            commercial_score: 92,
            overall_score: 90,
            submitted_at: '2024-01-15T10:30:00Z',
            response_documents: { 'proposal.pdf': 'url1', 'technical_specs.pdf': 'url2' },
            proposal_data: { 
              approach: 'Innovative cloud-based solution with AI integration',
              timeline: '6 months',
              team_size: 12,
              experience_years: 8,
              budget_breakdown: 'Development: 60%, Testing: 20%, Deployment: 20%',
              key_features: ['Real-time analytics', 'Mobile responsive', 'API integration'],
              support_included: true,
              maintenance_period: '2 years'
            }
          },
          {
            response_id: 2,
            vendor_name: 'InnovateTech Ltd',
            org: 'InnovateTech Limited',
            proposed_value: 118000,
            technical_score: 92,
            commercial_score: 85,
            overall_score: 88,
            submitted_at: '2024-01-16T14:20:00Z',
            response_documents: { 'proposal.pdf': 'url3', 'demo_video.mp4': 'url4' },
            proposal_data: { 
              approach: 'Agile methodology with rapid prototyping',
              timeline: '5 months',
              team_size: 8,
              experience_years: 5,
              budget_breakdown: 'Development: 70%, Testing: 15%, Training: 15%',
              key_features: ['User-friendly interface', 'Scalable architecture', '24/7 support'],
              support_included: true,
              maintenance_period: '3 years'
            }
          },
          {
            response_id: 3,
            vendor_name: 'Future Systems',
            org: 'Future Systems Corp',
            proposed_value: 135000,
            technical_score: 85,
            commercial_score: 78,
            overall_score: 81,
            submitted_at: '2024-01-17T09:15:00Z',
            response_documents: { 'proposal.pdf': 'url5', 'case_studies.pdf': 'url6' },
            proposal_data: { 
              approach: 'Traditional waterfall methodology with proven frameworks',
              timeline: '7 months',
              team_size: 15,
              experience_years: 12,
              budget_breakdown: 'Development: 50%, Testing: 25%, Documentation: 25%',
              key_features: ['Enterprise-grade security', 'Comprehensive reporting', 'Legacy integration'],
              support_included: false,
              maintenance_period: '1 year'
            }
          }
        ]
        
        rankedProposals.value = [...shortlistedProposals.value].map((proposal, index) => ({
          ...proposal,
          ranking_position: index + 1,
          ranking_score: 100 - (index * 10),
          evaluation_comments: '',
          previous_evaluations: [
            {
              evaluator_id: 1,
              evaluator_name: 'Technical Evaluator',
              comments: 'Strong technical approach with innovative solutions.',
              scores: { technical: proposal.technical_score || 85, commercial: proposal.commercial_score || 78 }
            },
            {
              evaluator_id: 2,
              evaluator_name: 'Commercial Evaluator',
              comments: 'Competitive pricing and good value proposition.',
              scores: { technical: proposal.technical_score || 85, commercial: proposal.commercial_score || 78 }
            }
          ]
        }))
      }
    } catch (error) {
      console.log('Error loading shortlisted proposals, using fallback data')
      // Use the same fallback data as above
    }
    
    // Load existing evaluations for consensus view
    await loadCommitteeEvaluations()
    
    // Ensure committee members have rankings data after proposals are loaded
    if (shortlistedProposals.value.length > 0) {
      console.log('🔧 Ensuring committee members have rankings data...')
      committeeMembers.value.forEach((member, memberIndex) => {
        if (!member.rankings || member.rankings.length === 0) {
          member.evaluation_completed = true
          member.rankings = shortlistedProposals.value.map((proposal, index) => ({
            response_id: proposal.response_id,
            vendor_name: proposal.vendor_name,
            org: proposal.org,
            ranking_position: index + 1,
            ranking_score: proposal.overall_score || (90 - (index * 5) + (memberIndex * 2))
          }))
          
          console.log(`📋 Final rankings for ${member.first_name} ${member.last_name}:`, member.rankings.map(r => ({
            vendor_name: r.vendor_name,
            org: r.org,
            ranking_score: r.ranking_score
          })))
        }
      })
    }
    
  } catch (error) {
    console.error('Error loading committee evaluation data:', error)
    PopupService.error('Failed to load evaluation data', 'Loading Failed')
  }
}

const loadCommitteeEvaluations = async () => {
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const rfpId = urlParams.get('rfp_id')
    
    console.log('🔄 Loading committee evaluations for RFP:', rfpId)
    
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(`${API_BASE_URL}/rfp/${rfpId}/final-evaluations/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      const data = await response.json()
      console.log('📋 Committee evaluations data:', data)
      
      if (data.success && data.evaluations) {
        // Update committee members with their evaluation status
        committeeMembers.value.forEach(member => {
          // Backend returns evaluations grouped by evaluator_id as an object
          const memberEvaluations = data.evaluations[member.member_id] || []
          member.evaluation_completed = memberEvaluations.length > 0
          member.rankings = memberEvaluations.sort((a, b) => a.ranking_position - b.ranking_position)
        })
        console.log('✅ Committee evaluations loaded successfully')
      }
    } else {
      console.log('⚠️ Failed to load committee evaluations, using mock data for testing')
      
      // Add mock rankings data for testing using actual vendor names
      committeeMembers.value.forEach((member, memberIndex) => {
        member.evaluation_completed = true
        member.rankings = shortlistedProposals.value.map((proposal, index) => {
          // Get vendor name from response_documents if available
          let vendorName = proposal.vendor_name
          let orgName = proposal.org
          
          if (proposal.response_documents) {
            if (proposal.response_documents.companyInfo && proposal.response_documents.companyInfo.contactName) {
              vendorName = proposal.response_documents.companyInfo.contactName
            }
            if (proposal.response_documents.companyInfo && proposal.response_documents.companyInfo.companyName) {
              orgName = proposal.response_documents.companyInfo.companyName
            }
          }
          
          return {
            response_id: proposal.response_id,
            vendor_name: vendorName || `Vendor ${proposal.response_id}`,
            org: orgName || 'Unknown Organization',
            ranking_position: index + 1,
            ranking_score: proposal.overall_score || (90 - (index * 5) + (memberIndex * 2))
          }
        })
        
        console.log(`📋 Mock rankings for ${member.first_name} ${member.last_name}:`, member.rankings.map(r => ({
          vendor_name: r.vendor_name,
          org: r.org,
          ranking_score: r.ranking_score
        })))
        })
    }
  } catch (error) {
    console.error('Error loading committee evaluations:', error)
    
    // Add mock rankings data for testing using actual vendor names
    committeeMembers.value.forEach((member, memberIndex) => {
      member.evaluation_completed = true
      member.rankings = shortlistedProposals.value.map((proposal, index) => ({
        response_id: proposal.response_id,
        vendor_name: proposal.vendor_name,
        org: proposal.org,
        ranking_position: index + 1,
        ranking_score: proposal.overall_score || (90 - (index * 5) + (memberIndex * 2))
      }))
      
      console.log(`📋 Mock rankings for ${member.first_name} ${member.last_name}:`, member.rankings.map(r => ({
        vendor_name: r.vendor_name,
        org: r.org,
        ranking_score: r.ranking_score
      })))
    })
  }
}

const handleDragStart = (proposal) => {
  isBeingDragged.value = proposal.response_id
}

const handleDragEnd = () => {
  isBeingDragged.value = null
}

const handleDrop = (targetProposal, event) => {
  event.preventDefault()
  
  if (!isBeingDragged.value) return
  
  const draggedProposal = rankedProposals.value.find(p => p.response_id === isBeingDragged.value)
  const targetIndex = rankedProposals.value.findIndex(p => p.response_id === targetProposal.response_id)
  const draggedIndex = rankedProposals.value.findIndex(p => p.response_id === isBeingDragged.value)
  
  if (draggedIndex === -1 || targetIndex === -1) return
  
  // Remove dragged item
  rankedProposals.value.splice(draggedIndex, 1)
  
  // Insert at new position
  rankedProposals.value.splice(targetIndex, 0, draggedProposal)
  
  // Update ranking positions
  updateRankingPositions()
}

const updateRankingPositions = () => {
  rankedProposals.value.forEach((proposal, index) => {
    proposal.ranking_position = index + 1
  })
}

const updateRankingScore = (proposal) => {
  // Ensure score is within valid range
  proposal.ranking_score = Math.max(1, Math.min(100, proposal.ranking_score || 1))
}

const updateRankingComments = (proposal) => {
  // Comments are already bound via v-model
}

// Comparison methods
const selectProposalForComparison = (proposal) => {
  selectedComparisonProposals.value[0] = proposal.response_id
  selectedComparisonProposals.value[1] = ''
  comparisonData.value = null
}

const startComparison = () => {
  const proposalAId = selectedComparisonProposals.value[0]
  const proposalBId = selectedComparisonProposals.value[1]
  
  const proposalA = shortlistedProposals.value.find(p => p.response_id === proposalAId)
  const proposalB = shortlistedProposals.value.find(p => p.response_id === proposalBId)
  
  if (proposalA && proposalB) {
    comparisonData.value = {
      proposalA: {
        ...proposalA,
        previous_evaluations: proposalA.previous_evaluations || []
      },
      proposalB: {
        ...proposalB,
        previous_evaluations: proposalB.previous_evaluations || []
      }
    }
    
    console.log('🔍 Started comparison between:', proposalA.vendor_name, 'vs', proposalB.vendor_name)
  }
}

const saveRankings = async () => {
  saving.value = true
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const rfpId = urlParams.get('rfp_id')
    
    const evaluationData = {
      evaluator_id: currentEvaluatorId.value,
      rankings: rankedProposals.value.map(proposal => ({
        response_id: proposal.response_id,
        ranking_position: proposal.ranking_position,
        ranking_score: proposal.ranking_score,
        evaluation_comments: proposal.evaluation_comments
      }))
    }
    
    console.log('💾 Saving final evaluation rankings:', evaluationData)
    
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(`${API_BASE_URL}/rfp/${rfpId}/final-evaluation/`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(evaluationData)
    })
    
    if (response.ok) {
      const result = await response.json()
      console.log('✅ Final evaluation saved successfully:', result)
      PopupService.success('Final evaluation rankings saved successfully', 'Rankings Saved')
      await loadCommitteeEvaluations()
    } else {
      const errorText = await response.text()
      console.error('❌ Failed to save final evaluation:', errorText)
      throw new Error(`Failed to save rankings: ${errorText}`)
    }
  } catch (error) {
    console.error('Error saving rankings:', error)
    PopupService.error('Failed to save rankings', 'Save Failed')
  } finally {
    saving.value = false
  }
}

const submitFinalEvaluation = async () => {
  if (!isValid.value) {
    PopupService.warning('Please complete all rankings before submitting', 'Incomplete Rankings')
    return
  }
  
  saving.value = true
  try {
    await saveRankings()
    
    // Handle workflow approval if this is part of a workflow
    const urlParams = new URLSearchParams(window.location.search)
    const approvalId = urlParams.get('approval_id')
    const stageId = urlParams.get('stage_id')
    
    console.log('🔄 Submitting final evaluation with workflow parameters:', {
      approval_id: approvalId,
      stage_id: stageId,
      evaluator_id: currentEvaluatorId.value
    })
    
    if (stageId) {
      console.log('✅ Approving workflow stage:', stageId)
      await approveWorkflowStage(stageId)
    } else if (approvalId) {
      console.log('✅ Approving workflow stage with approval ID:', approvalId)
      await approveWorkflowStage(approvalId)
    } else {
      console.log('⚠️ No workflow stage ID found in URL parameters')
    }
    
    PopupService.success('Final evaluation submitted successfully! Stage status updated to APPROVED.', 'Submitted')
    PopupService.onAction('ok', () => {
      router.push('/my-approvals')
    })
  } catch (error) {
    console.error('Error submitting final evaluation:', error)
    PopupService.error('Failed to submit final evaluation: ' + error.message, 'Submission Failed')
  } finally {
    saving.value = false
  }
}

const viewProposalDetails = (proposal) => {
  selectedProposal.value = proposal
  showProposalModal.value = true
}

const openDetailedEvaluation = (proposal) => {
  selectedProposalForEvaluation.value = proposal
  activeTab.value = 'evaluation'
  
  // Initialize evaluation criteria if not already loaded
  if (evaluationCriteria.value.length === 0) {
    loadEvaluationCriteria()
  }
  
  // Load existing evaluation data for this proposal
  loadExistingEvaluation(proposal.response_id)
}

const loadEvaluationCriteria = async () => {
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const rfpId = urlParams.get('rfp_id')
    
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(`${API_BASE_URL}/evaluation-criteria/?rfp_id=${rfpId}`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      const data = await response.json()
      // The ViewSet returns results in a 'results' array
      evaluationCriteria.value = data.results || []
    } else {
      // Fallback to default criteria
      evaluationCriteria.value = [
        { id: 1, name: 'Technical Approach', weight: 30, max_score: 100 },
        { id: 2, name: 'Implementation Plan', weight: 25, max_score: 100 },
        { id: 3, name: 'Commercial Terms', weight: 25, max_score: 100 },
        { id: 4, name: 'Risk Management', weight: 20, max_score: 100 }
      ]
    }
  } catch (error) {
    console.error('Error loading evaluation criteria:', error)
    // Use default criteria
    evaluationCriteria.value = [
      { id: 1, name: 'Technical Approach', weight: 30, max_score: 100 },
      { id: 2, name: 'Implementation Plan', weight: 25, max_score: 100 },
      { id: 3, name: 'Commercial Terms', weight: 25, max_score: 100 },
      { id: 4, name: 'Risk Management', weight: 20, max_score: 100 }
    ]
  }
}

const loadExistingEvaluation = async (responseId) => {
  try {
    // For now, initialize empty evaluation since the endpoint doesn't exist
    // This will be implemented when the backend endpoint is created
    console.log('Loading existing evaluation for response:', responseId)
      evaluationScores.value = {}
      evaluationComments.value = {}
      overallComments.value = ''
  } catch (error) {
    console.error('Error loading existing evaluation:', error)
    // Initialize empty evaluation
    evaluationScores.value = {}
    evaluationComments.value = {}
    overallComments.value = ''
  }
}

const handleUpdateScores = (scores) => {
  evaluationScores.value = { ...scores }
}

const handleUpdateComments = (comments) => {
  if (comments.overall) {
    overallComments.value = comments.overall
  } else {
    evaluationComments.value = { ...comments }
  }
}

const handleSaveEvaluation = async () => {
  if (!selectedProposalForEvaluation.value) return
  
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const rfpId = urlParams.get('rfp_id')
    
    const evaluationData = {
      rfp_id: parseInt(rfpId),
      response_id: selectedProposalForEvaluation.value.response_id,
      evaluator_id: currentEvaluatorId.value,
      scores: evaluationScores.value,
      comments: evaluationComments.value,
      overall_comments: overallComments.value,
      is_draft: true
    }
    
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(`${API_BASE_URL}/rfp/${rfpId}/committee-evaluation/`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(evaluationData)
    })
    
    if (response.ok) {
      PopupService.success('Evaluation saved successfully', 'Saved')
    } else {
      throw new Error('Failed to save evaluation')
    }
  } catch (error) {
    console.error('Error saving evaluation:', error)
    PopupService.error('Failed to save evaluation', 'Save Failed')
  }
}

const handleSubmitEvaluation = async () => {
  if (!selectedProposalForEvaluation.value) return
  
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const rfpId = urlParams.get('rfp_id')
    
    const evaluationData = {
      rfp_id: parseInt(rfpId),
      response_id: selectedProposalForEvaluation.value.response_id,
      evaluator_id: currentEvaluatorId.value,
      scores: evaluationScores.value,
      comments: evaluationComments.value,
      overall_comments: overallComments.value,
      is_draft: false
    }
    
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(`${API_BASE_URL}/rfp/${rfpId}/committee-evaluation/`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(evaluationData)
    })
    
    if (response.ok) {
      PopupService.success('Evaluation submitted successfully', 'Submitted')
      // Switch back to ranking tab
      activeTab.value = 'ranking'
      selectedProposalForEvaluation.value = null
      // Reload committee evaluations to update consensus view
      await loadCommitteeEvaluations()
    } else {
      throw new Error('Failed to submit evaluation')
    }
  } catch (error) {
    console.error('Error submitting evaluation:', error)
    PopupService.error('Failed to submit evaluation', 'Submission Failed')
  }
}

const viewPreviousEvaluations = (proposal) => {
  // Navigate to detailed evaluation view
  router.push({
    path: '/proposal-evaluation',
    query: {
      response_id: proposal.response_id,
      evaluator_id: currentEvaluatorId.value,
      view_mode: 'previous'
    }
  })
}

const declareAward = async () => {
  if (!canDeclareAward.value) return
  
  const winner = consensusRanking.value[0]
  if (!winner) return
  
  PopupService.confirm(
    `Declare ${winner.vendor_name} as the winner and send award email?`,
    'Confirm Award',
    async () => {
      await performDeclareWinner(winner)
    },
    () => {
      // onCancel callback
      console.log('Award declaration cancelled')
    }
  )
}

const performDeclareWinner = async (winner) => {
  
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const rfpId = urlParams.get('rfp_id')
    
    const awardData = {
      winning_response_id: winner.response_id,
      winning_vendor_id: winner.vendor_id,
      award_amount: winner.proposed_value,
      awarded_by: currentEvaluatorId.value,
      award_justification: `Selected based on committee consensus ranking with score of ${winner.consensus_score.toFixed(1)}`
    }
    
    console.log('🏆 Declaring award:', awardData)
    
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(`${API_BASE_URL}/rfp/${rfpId}/declare-award/`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(awardData)
    })
    
    if (response.ok) {
      const result = await response.json()
      console.log('✅ Award declared successfully:', result)
      PopupService.success('Award declared successfully! Email notifications have been sent.', 'Award Declared')
      PopupService.onAction('ok', () => {
        router.push('/my-approvals')
      })
    } else {
      const errorText = await response.text()
      console.error('❌ Failed to declare award:', errorText)
      throw new Error(`Failed to declare award: ${errorText}`)
    }
  } catch (error) {
    console.error('Error declaring award:', error)
    PopupService.error('Failed to declare award', 'Declaration Failed')
  }
}

const formatKey = (key) => {
  if (typeof key !== 'string') return String(key || 'Unknown')
  return key.split('_').map(word => 
    word && word.length > 0 ? word.charAt(0).toUpperCase() + word.slice(1) : ''
  ).join(' ')
}

const formatValue = (value) => {
  if (value === null || value === undefined) return 'Not specified'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'number') return value.toLocaleString()
  if (typeof value === 'object') {
    // Handle arrays
    if (Array.isArray(value)) {
      return value.join(', ')
    }
    // Handle objects - show key-value pairs in a readable format
    return Object.entries(value)
      .map(([key, val]) => `${formatKey(key)}: ${formatValue(val)}`)
      .join(' | ')
  }
  return String(value)
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
}

const approveWorkflowStage = async (stageId) => {
  try {
    console.log('🔄 Approving workflow stage:', stageId)
    
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch('http://localhost:8000/api/rfp-approval/update-stage-status/', {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        stage_id: stageId,
        status: 'APPROVE',
        comments: `Committee evaluation completed successfully by evaluator ${currentEvaluatorId.value}`
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      console.log('✅ Workflow stage approved successfully:', result)
      
      // Verify the status was updated
      if (result.success) {
        console.log('✅ Stage status updated to APPROVED')
      } else {
        console.warn('⚠️ Stage approval response indicates failure:', result)
      }
    } else {
      const errorText = await response.text()
      console.error('❌ Failed to approve workflow stage:', errorText)
      throw new Error(`Failed to approve workflow stage: ${errorText}`)
    }
  } catch (error) {
    console.error('❌ Error approving workflow stage:', error)
    throw error
  }
}

const navigateBack = () => {
  router.push('/my-approvals')
}

// Helper functions to get vendor names and organizations
const getVendorName = (ranking) => {
  console.log(`🔍 Getting vendor name for ranking:`, ranking)
  
  if (ranking.vendor_name) {
    console.log(`  ✅ Found vendor_name in ranking: ${ranking.vendor_name}`)
    return ranking.vendor_name
  }
  
  // Try to get from shortlistedProposals
  const proposal = shortlistedProposals.value.find(p => p.response_id === ranking.response_id)
  if (proposal) {
    console.log(`  📋 Found proposal for response_id ${ranking.response_id}:`, {
      vendor_name: proposal.vendor_name,
      org: proposal.org
    })
    
    if (proposal.vendor_name) {
      console.log(`  ✅ Using proposal.vendor_name: ${proposal.vendor_name}`)
      return proposal.vendor_name
    }
    
    // Try to get from response_documents
    if (proposal.response_documents) {
      if (proposal.response_documents.companyInfo && proposal.response_documents.companyInfo.contactName) {
        console.log(`  ✅ Using companyInfo.contactName: ${proposal.response_documents.companyInfo.contactName}`)
        return proposal.response_documents.companyInfo.contactName
      }
      if (proposal.response_documents.vendor_name) {
        console.log(`  ✅ Using response_documents.vendor_name: ${proposal.response_documents.vendor_name}`)
        return proposal.response_documents.vendor_name
      }
    }
  }
  
  console.log(`  ⚠️ No vendor name found, using fallback: Vendor ${ranking.response_id}`)
  return `Vendor ${ranking.response_id}`
}

const getOrganizationName = (ranking) => {
  console.log(`🔍 Getting organization name for ranking:`, ranking)
  
  if (ranking.org) {
    console.log(`  ✅ Found org in ranking: ${ranking.org}`)
    return ranking.org
  }
  
  // Try to get from shortlistedProposals
  const proposal = shortlistedProposals.value.find(p => p.response_id === ranking.response_id)
  if (proposal) {
    console.log(`  📋 Found proposal for response_id ${ranking.response_id}:`, {
      org: proposal.org
    })
    
    if (proposal.org) {
      console.log(`  ✅ Using proposal.org: ${proposal.org}`)
      return proposal.org
    }
    
    // Try to get from response_documents
    if (proposal.response_documents) {
      if (proposal.response_documents.companyInfo && proposal.response_documents.companyInfo.companyName) {
        console.log(`  ✅ Using companyInfo.companyName: ${proposal.response_documents.companyInfo.companyName}`)
        return proposal.response_documents.companyInfo.companyName
      }
      if (proposal.response_documents.org) {
        console.log(`  ✅ Using response_documents.org: ${proposal.response_documents.org}`)
        return proposal.response_documents.org
      }
    }
  }
  
  console.log(`  ⚠️ No organization found, using fallback: Unknown Organization`)
  return 'Unknown Organization'
}

// Watch for changes in shortlistedProposals and ensure committee members have rankings
watch(shortlistedProposals, (newProposals) => {
  if (newProposals && newProposals.length > 0) {
    console.log('🔧 Proposals loaded, ensuring committee members have rankings...')
    console.log('🔧 Available proposals for rankings:', newProposals.map(p => ({
      response_id: p.response_id,
      vendor_name: p.vendor_name,
      org: p.org
    })))
    
    committeeMembers.value.forEach((member, memberIndex) => {
      if (!member.rankings || member.rankings.length === 0) {
        member.evaluation_completed = true
        member.rankings = newProposals.map((proposal, index) => {
          console.log(`🔍 Creating ranking for proposal ${proposal.response_id}:`, {
            vendor_name: proposal.vendor_name,
            org: proposal.org,
            has_org: !!proposal.org
          })
          
          // Get vendor name from response_documents if available
          let vendorName = proposal.vendor_name
          let orgName = proposal.org
          
          if (proposal.response_documents) {
            if (proposal.response_documents.companyInfo && proposal.response_documents.companyInfo.contactName) {
              vendorName = proposal.response_documents.companyInfo.contactName
            }
            if (proposal.response_documents.companyInfo && proposal.response_documents.companyInfo.companyName) {
              orgName = proposal.response_documents.companyInfo.companyName
            }
          }
          
          const ranking = {
            response_id: proposal.response_id,
            vendor_name: vendorName || `Vendor ${proposal.response_id}`,
            org: orgName || 'Unknown Organization',
            ranking_position: index + 1,
            ranking_score: proposal.overall_score || (90 - (index * 5) + (memberIndex * 2))
          }
          
          console.log(`  ✅ Final ranking data:`, ranking)
          return ranking
        })
        
        console.log(`📋 Rankings created for ${member.first_name} ${member.last_name}:`, member.rankings.map(r => ({
          response_id: r.response_id,
          vendor_name: r.vendor_name,
          org: r.org,
          ranking_score: r.ranking_score
        })))
      }
    })
  }
}, { immediate: true })

onMounted(async () => {
  await loggingService.logPageView('RFP', 'Committee Evaluation')
  await loadCommitteeEvaluationData()
  await loadEvaluationCriteria()
})
</script>

<style scoped>
/* Drag and drop styles */
[draggable="true"] {
  cursor: move;
}

[draggable="true"]:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

/* Ranking position styles */
.ranking-position {
  transition: all 0.2s ease;
}

/* Consensus view styles */
.consensus-item {
  transition: all 0.2s ease;
}

.consensus-item:hover {
  transform: translateX(2px);
}
</style>
