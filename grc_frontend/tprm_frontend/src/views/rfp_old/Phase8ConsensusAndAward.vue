<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="space-y-8">
        <!-- Header -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <h1 class="text-3xl font-bold tracking-tight text-gray-900">Consensus & Award Management</h1>
              <p class="text-gray-600 mt-2">
                Committee consensus ranking and contract award decision management.
              </p>
              <div class="mt-2 flex items-center gap-4 text-sm text-gray-500">
                <span>RFP: {{ rfpData?.rfp_title || 'Loading...' }}</span>
                <span>#{{ rfpData?.rfp_number }}</span>
                <span v-if="consensusRanking.length > 0">{{ consensusRanking.length }} finalists</span>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button
                v-if="currentRfpId"
                @click="changeRfp"
                class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                title="Select a different RFP"
              >
                <Search class="h-4 w-4 mr-2" />
                Change RFP
              </button>
              <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                Consensus & Award
              </span>
              <div class="flex items-center gap-2">
                <div class="flex items-center gap-1">
                  <div 
                    class="w-2 h-2 rounded-full"
                    :class="isPolling ? 'bg-green-500 animate-pulse' : 'bg-gray-400'"
                  ></div>
                  <span class="text-xs text-gray-500">
                    {{ isPolling ? 'Live' : 'Offline' }}
                  </span>
                </div>
                <span class="text-xs text-gray-400">•</span>
                <span class="text-xs text-gray-500">Updated {{ timeSinceUpdate }}</span>
                <button 
                  @click="refreshData"
                  class="ml-2 p-1 text-gray-400 hover:text-gray-600 transition-colors"
                  title="Refresh data"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- RFP Selection (shown when no RFP ID in URL) -->
        <div v-if="!currentRfpId" class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-2xl font-bold text-gray-900">Select RFP</h3>
              <p class="text-gray-600 mt-1">Choose an RFP to view consensus and award information</p>
            </div>
            <div>
              <button
                @click="router.push('/rfp-list')"
                class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                <Search class="h-4 w-4 mr-2" />
                Browse All RFPs
              </button>
            </div>
          </div>
          
          <div v-if="loadingRfps" class="text-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p class="text-gray-600 mt-2">Loading RFPs...</p>
          </div>
          
          <div v-else-if="availableRfps.length === 0" class="text-center py-8">
            <p class="text-gray-600">No RFPs available</p>
          </div>
          
          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div 
              v-for="rfp in availableRfps" 
              :key="rfp.rfp_id"
              @click="selectRfp(rfp.rfp_id)"
              class="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md cursor-pointer transition-all"
            >
              <div class="flex items-center justify-between mb-2">
                <h4 class="font-semibold text-gray-900">{{ rfp.rfp_title }}</h4>
                <span class="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">{{ rfp.rfp_number }}</span>
              </div>
              <p class="text-sm text-gray-600 mb-2">{{ rfp.description ? (rfp.description.substring(0, 100) + '...') : 'No description available' }}</p>
              <div class="flex items-center justify-between text-xs text-gray-500">
                <span>{{ rfp.status }}</span>
                <span>{{ new Date(rfp.created_at).toLocaleDateString() }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Main Content (shown when RFP is selected) -->
        <div v-if="currentRfpId" class="space-y-8">
          <!-- Overview Cards -->
          <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div class="flex items-center gap-4">
                <div class="p-3 rounded-lg bg-blue-50">
                  <Users class="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-600">Committee Members</p>
                  <p class="text-2xl font-bold text-gray-900">{{ committeeMembers.length }}</p>
                </div>
              </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div class="flex items-center gap-4">
                <div class="p-3 rounded-lg bg-green-50">
                  <CheckCircle2 class="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-600">Evaluations Complete</p>
                  <p class="text-2xl font-bold text-gray-900">{{ completedEvaluations }}/{{ committeeMembers.length }}</p>
                </div>
              </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div class="flex items-center gap-4">
                <div class="p-3 rounded-lg bg-purple-50">
                  <Trophy class="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p class="text-sm font-medium text-gray-600">Finalists</p>
                  <p class="text-2xl font-bold text-gray-900">{{ consensusRanking.length }}</p>
                </div>
              </div>
            </div>
            
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div class="flex items-center gap-4">
                <div class="p-3 rounded-lg bg-yellow-50">
                  <Award class="h-6 w-6 text-yellow-600" />
                </div>
                <div class="flex-1">
                  <p class="text-sm font-medium text-gray-600">Award Status</p>
                  <p class="text-2xl font-bold text-gray-900">{{ awardStatus }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Rejected Awards Alert -->
          <div v-if="rejectedAwards.length > 0" class="bg-red-50 border-2 border-red-300 rounded-lg p-6">
            <div class="flex items-start gap-4">
              <div class="flex-shrink-0 p-3 bg-red-100 rounded-full">
                <XCircle class="h-6 w-6 text-red-600" />
              </div>
              <div class="flex-1">
                <h3 class="text-lg font-bold text-red-900 mb-2">
                  {{ rejectedAwards.length }} Award(s) Rejected
                </h3>
                <p class="text-sm text-red-700 mb-3">
                  The following vendors have declined the award. Please select and notify the next available vendor.
                </p>
                <div class="space-y-2">
                  <div 
                    v-for="rejection in rejectedAwards" 
                    :key="rejection.notification_id"
                    class="flex items-center justify-between p-3 bg-white border border-red-200 rounded-md"
                  >
                    <div class="flex items-center gap-3">
                      <div class="font-medium text-gray-900">{{ rejection.vendor_name }}</div>
                      <div class="text-sm text-gray-500">{{ rejection.vendor_email }}</div>
                      <div class="text-xs text-gray-400">Rejected: {{ formatDate(rejection.response_date) }}</div>
                    </div>
                    <button
                      @click="selectAndSendToNextVendor(rejection.response_id)"
                      class="inline-flex items-center px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
                    >
                      <Mail class="h-3 w-3 mr-1" />
                      Send to Next Vendor
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Final Consensus Ranking -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h2 class="text-2xl font-bold text-gray-900">Final Consensus Ranking</h2>
                <p class="text-sm text-gray-600 mt-1">
                  {{ isConsensusComplete 
                    ? 'Consensus reached. Select a vendor to receive the contract award.' 
                    : 'Committee evaluations in progress. Rankings will update as evaluations are completed.' }}
                </p>
              </div>
              <div class="flex items-center gap-2">
                <span 
                  class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
                  :class="isConsensusComplete ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'"
                >
                  {{ isConsensusComplete ? 'Consensus Reached' : 'In Progress' }}
                </span>
                <div v-if="!isConsensusComplete" class="flex items-center gap-1">
                  <div class="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
                  <span class="text-xs text-gray-500">Waiting for evaluations...</span>
                </div>
              </div>
            </div>

            <div v-if="loading" class="text-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p class="text-gray-600 mt-2">Loading consensus data...</p>
            </div>

            <div v-else-if="consensusRanking.length > 0" class="space-y-4">
              <div 
                v-for="(item, index) in consensusRanking" 
                :key="item.response_id"
                class="flex items-center justify-between p-6 rounded-lg border-2 transition-all duration-200 cursor-pointer hover:shadow-md"
                :class="[
                  selectedWinner === item.response_id 
                    ? 'border-blue-500 bg-blue-50 shadow-md' 
                    : index === 0 
                      ? 'border-yellow-300 bg-gradient-to-r from-yellow-50 to-orange-50' 
                      : 'border-gray-200 bg-white hover:border-gray-300'
                ]"
                @click="isConsensusComplete && (selectedWinner = item.response_id)"
              >
                <div class="flex items-center space-x-4 flex-1">
                  <div 
                    class="flex items-center justify-center w-12 h-12 rounded-full text-lg font-bold"
                    :class="index === 0 ? 'bg-yellow-200 text-yellow-800' : 'bg-gray-100 text-gray-600'"
                  >
                    {{ index + 1 }}
                  </div>
                  <div class="flex-1">
                    <div class="flex items-center gap-2">
                      <h3 class="text-xl font-bold text-gray-900">{{ getVendorName(item) }}</h3>
                      <span v-if="index === 0" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        🏆 Top Ranked
                      </span>
                      <span v-if="selectedWinner === item.response_id" class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        ✓ Selected for Award
                      </span>
                    </div>
                    <p class="text-sm text-gray-600 mt-1">{{ getOrganizationName(item) }}</p>
                    <div class="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      <span v-if="item.proposed_value">Proposed Value: ${{ item.proposed_value.toLocaleString() }}</span>
                      <span v-if="item.technical_score">Technical: {{ item.technical_score }}/100</span>
                      <span v-if="item.commercial_score">Commercial: {{ item.commercial_score }}/100</span>
                    </div>
                  </div>
                </div>
                <div class="text-right ml-4">
                  <div class="text-3xl font-bold text-green-600">{{ (item.consensus_score || item.overall_score || 0).toFixed(2) }}</div>
                  <div class="text-sm text-gray-600 font-medium">Consensus Score</div>
                  <div v-if="item.score_range" class="text-xs text-gray-500 mt-1">Range: {{ item.score_range }}</div>
                  <div v-if="item.vote_count" class="text-xs text-gray-500">{{ item.vote_count }} evaluator(s)</div>
                </div>
              </div>
              
              <div v-if="selectedWinner && isConsensusComplete" class="mt-6 p-4 rounded-lg" :class="getSelectedVendorEmail() && getSelectedVendorEmail() !== 'vendor@example.com' ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'">
                <div class="flex items-center gap-2 mb-2">
                  <CheckCircle2 class="h-5 w-5" :class="getSelectedVendorEmail() && getSelectedVendorEmail() !== 'vendor@example.com' ? 'text-green-600' : 'text-yellow-600'" />
                  <span class="font-medium" :class="getSelectedVendorEmail() && getSelectedVendorEmail() !== 'vendor@example.com' ? 'text-green-900' : 'text-yellow-900'">Winner Selected</span>
                </div>
                <p class="text-sm" :class="getSelectedVendorEmail() && getSelectedVendorEmail() !== 'vendor@example.com' ? 'text-green-700' : 'text-yellow-700'">
                  <strong>{{ getSelectedVendorName() }}</strong> has been selected to receive the contract award.
                </p>
                <div v-if="!getSelectedVendorEmail() || getSelectedVendorEmail() === 'vendor@example.com'" class="mt-2 text-sm text-yellow-800">
                  ⚠️ <strong>Warning:</strong> No valid email address found for this vendor. Please ensure the vendor has provided their contact email in the RFP response.
                </div>
                <div v-else class="mt-2 text-sm text-green-800">
                  📧 Notification will be sent to: <strong>{{ getSelectedVendorEmail() }}</strong>
                </div>
              </div>
            </div>
            
            <div v-else class="text-center py-12">
              <div class="text-gray-400 mb-4">
                <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">No Consensus Data Available</h3>
              <p class="text-gray-600 mb-4">Committee evaluations are still in progress or no data has been loaded.</p>
            </div>
          </div>

          <!-- Committee Members -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 class="text-xl font-bold text-gray-900 mb-6">Committee Members & Evaluations</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div v-for="member in committeeMembers" :key="member.member_id" class="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                <div class="flex items-center gap-3 mb-4">
                  <div class="h-12 w-12 rounded-full bg-blue-50 flex items-center justify-center">
                    <span class="text-sm font-bold text-blue-600">
                      {{ member.first_name?.[0] }}{{ member.last_name?.[0] }}
                    </span>
                  </div>
                  <div>
                    <div class="font-semibold text-gray-900">{{ member.first_name }} {{ member.last_name }}</div>
                    <div class="text-sm text-gray-600">{{ member.member_role || 'Committee Member' }}</div>
                    <div v-if="member.is_chair" class="text-xs text-yellow-600 font-medium">👑 Chair</div>
                  </div>
                </div>
                
                <div class="space-y-3">
                  <div class="flex items-center justify-between">
                    <span class="text-sm text-gray-600">Evaluation Status:</span>
                    <span 
                      class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                      :class="member.evaluation_completed ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'"
                    >
                      {{ member.evaluation_completed ? 'Completed' : 'Pending' }}
                    </span>
                  </div>
                  
                  <div v-if="member.evaluation_completed && member.rankings" class="space-y-2">
                    <div class="text-sm font-medium text-gray-700">Top Rankings:</div>
                    <div class="space-y-1">
                      <div 
                        v-for="(ranking, index) in member.rankings.slice(0, 3)" 
                        :key="ranking.response_id"
                        class="flex items-center justify-between text-xs bg-gray-50 p-2 rounded"
                      >
                        <span class="font-medium">{{ index + 1 }}. {{ getVendorName(ranking) }}</span>
                        <span class="text-blue-600 font-bold">{{ ranking.ranking_score }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div v-else class="text-sm text-gray-500">
                    Evaluation pending
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Award Notification Section (shown when consensus is complete) -->
          <div v-if="isConsensusComplete" class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 class="text-xl font-bold text-gray-900 mb-6">Send Award Notification</h3>
            
            <div v-if="selectedWinner" class="space-y-4">
              <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <div class="flex items-center gap-2 mb-2">
                  <CheckCircle2 class="h-5 w-5 text-green-600" />
                  <span class="font-medium text-green-800">Ready to Send Award</span>
                </div>
                <p class="text-sm text-green-700">
                  Selected vendor: <strong>{{ getSelectedVendorName() }}</strong>
                </p>
              </div>

              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Award Message</label>
                  <textarea
                    v-model="awardMessage"
                    rows="4"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Congratulations! Your proposal has been selected as the winner..."
                  ></textarea>
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Next Steps</label>
                  <textarea
                    v-model="nextSteps"
                    rows="3"
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Please respond to this notification within 7 days to accept or decline the award..."
                  ></textarea>
                </div>
                
                <div class="flex gap-3">
                  <button
                    @click="sendAwardNotification"
                    :disabled="sendingNotification"
                    class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
                  >
                    <Mail class="h-4 w-4 mr-2" />
                    {{ sendingNotification ? 'Sending...' : 'Send Award Notification' }}
                  </button>
                  
                  <button
                    @click="sendParticipantNotifications"
                    :disabled="sendingNotification"
                    class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
                  >
                    <Users class="h-4 w-4 mr-2" />
                    Notify All Participants
                  </button>
                </div>
              </div>
            </div>
            
            <div v-else class="text-center py-8">
              <p class="text-gray-600">Please select a vendor from the consensus ranking above to send the award notification</p>
            </div>
          </div>

          <!-- Notification Status -->
          <div v-if="awardNotifications.length > 0 || loadingNotifications" class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 class="text-xl font-bold text-gray-900 mb-6">Notification Status</h3>
            
            <div v-if="loadingNotifications" class="text-center py-4">
              <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
              <p class="text-gray-600 mt-2">Loading notifications...</p>
            </div>
            
            <div v-else-if="awardNotifications.length === 0" class="text-center py-8">
              <p class="text-gray-600">No notifications sent yet</p>
            </div>
            
            <div v-else class="space-y-4">
              <div 
                v-for="notification in awardNotifications" 
                :key="notification.notification_id"
                class="border border-gray-200 rounded-lg p-4"
              >
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-3">
                    <component :is="getNotificationIcon(notification.notification_status)" class="h-5 w-5" />
                    <div>
                      <div class="font-medium text-gray-900">{{ notification.vendor_name }}</div>
                      <div class="text-sm text-gray-600">{{ notification.vendor_email }}</div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <span :class="getNotificationStatusClass(notification.notification_status)" class="px-2 py-1 rounded-full text-xs font-medium">
                      {{ notification.notification_status }}
                    </span>
                    <span class="text-sm text-gray-500">
                      {{ formatDate(notification.sent_date) }}
                    </span>
                  </div>
                </div>
                
                <div class="text-sm text-gray-700 mb-2">
                  <strong>Type:</strong> {{ notification.notification_type === 'winner' ? 'Winner Notification' : 'Participant Thanks' }}
                </div>
                
                <div v-if="notification.notification_status === 'rejected'" class="mt-3 p-4 bg-red-50 border-2 border-red-300 rounded-lg">
                  <div class="flex items-start gap-3 mb-3">
                    <div class="flex-shrink-0 p-2 bg-red-100 rounded-full">
                      <XCircle class="h-5 w-5 text-red-600" />
                    </div>
                    <div class="flex-1">
                      <h5 class="text-sm font-bold text-red-900 mb-1">Award Rejected by Vendor</h5>
                      <p class="text-sm text-red-700">
                        This vendor has declined the award. You can select another vendor from the ranking list above.
                      </p>
                      <p class="text-xs text-red-600 mt-1">
                        Rejected on: {{ formatDate(notification.response_date) }}
                      </p>
                    </div>
                  </div>
                  <div class="flex gap-2">
                    <button
                      @click="selectNextVendor(notification.response_id)"
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-red-800 bg-red-100 border border-red-300 rounded-md hover:bg-red-200 transition-colors"
                    >
                      <RefreshCw class="h-4 w-4 mr-1" />
                      Select Next Best Vendor
                    </button>
                    <button
                      @click="selectAndSendToNextVendor(notification.response_id)"
                      class="inline-flex items-center px-3 py-1.5 text-sm font-medium text-white bg-blue-600 border border-blue-700 rounded-md hover:bg-blue-700 transition-colors"
                    >
                      <Mail class="h-4 w-4 mr-1" />
                      Auto-Select & Send to Next
                    </button>
                  </div>
                </div>
                
                <div v-if="notification.notification_status === 'accepted'" class="mt-3 p-3 bg-green-50 border border-green-200 rounded-md">
                  <div class="flex items-center justify-between">
                    <div>
                      <div class="flex items-center gap-2">
                        <CheckCircle2 class="h-4 w-4 text-green-600" />
                        <span class="text-sm font-medium text-green-800">Vendor Accepted Award</span>
                      </div>
                      <p class="text-sm text-green-700 mt-1">
                        Vendor credentials have been automatically created and sent via email.
                      </p>
                    </div>
                    <button
                      @click="createVendorCredentials(notification.notification_id)"
                      :disabled="creatingCredentials"
                      class="inline-flex items-center px-3 py-1.5 text-xs font-medium text-green-700 bg-green-100 border border-green-200 rounded-md hover:bg-green-200 transition-colors disabled:opacity-50"
                      title="Recreate and resend credentials if needed"
                    >
                      {{ creatingCredentials ? 'Creating...' : 'Resend Credentials' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Navigation -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div class="flex gap-2">
                <button
                  @click="exportReport"
                  :disabled="exportLoading || !currentRfpId"
                  class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Download class="h-4 w-4 mr-2" />
                  {{ exportLoading ? 'Exporting...' : 'Export Report' }}
                </button>
              </div>
              <div class="flex gap-2">
                <button 
                  @click="goToComparison"
                  class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  <ArrowLeft class="h-4 w-4 mr-2" />
                  Previous: Comparison
                </button>
                <button 
                  @click="goToDashboard"
                  class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 transition-colors"
                >
                  Complete Workflow
                  <CheckCircle2 class="h-4 w-4 ml-2" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Real-time Notifications -->
    <div v-if="realTimeNotifications.length > 0" class="fixed top-4 right-4 z-50 space-y-2">
      <div 
        v-for="notification in realTimeNotifications" 
        :key="notification.id"
        class="bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-sm animate-slide-in"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <p class="text-sm font-medium text-gray-900">{{ notification.message }}</p>
            <p class="text-xs text-gray-500 mt-1">{{ timeSinceUpdate }}</p>
          </div>
          <button 
            @click="removeNotification(notification.id)"
            class="ml-2 text-gray-400 hover:text-gray-600"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useRfpApi } from '@/composables/useRfpApi'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'
import { 
  Users,
  CheckCircle2,
  Trophy,
  Award,
  Mail,
  Clock,
  XCircle,
  Download,
  ArrowRight,
  ArrowLeft,
  RefreshCw,
  Search,
  X
} from 'lucide-vue-next'
import jsPDF from 'jspdf'

const router = useRouter()
const route = useRoute()
const API_BASE_URL = 'http://localhost:8000/api/v1'

// State
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// RFP Selection state
const currentRfpId = ref<string | null>(null)
const availableRfps = ref<any[]>([])
const loadingRfps = ref(false)
const rfpData = ref(null)
const committeeMembers = ref([])
const shortlistedProposals = ref([])
const consensusRanking = ref([])
const selectedWinner = ref(null)
const awardNotifications = ref([])
const realTimeNotifications = ref([])
const loading = ref(true)
const loadingNotifications = ref(false)
const sendingNotification = ref(false)
const creatingCredentials = ref(false)
const exportLoading = ref(false)
const awardMessage = ref('')
const nextSteps = ref('')
const lastUpdated = ref(null)
const pollingInterval = ref(null)
const isPolling = ref(false)
const previousCompletedCount = ref(0)

// Computed properties
const completedEvaluations = computed(() => {
  return committeeMembers.value.filter(member => member.evaluation_completed).length
})

const consensusLevel = computed(() => {
  if (committeeMembers.value.length === 0) return 0
  return Math.round((completedEvaluations.value / committeeMembers.value.length) * 100)
})

const isConsensusComplete = computed(() => {
  return consensusLevel.value === 100
})

const timeSinceUpdate = computed(() => {
  if (!lastUpdated.value) return 'Never'
  const now = new Date().getTime()
  const diff = now - new Date(lastUpdated.value).getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  
  if (minutes > 0) return `${minutes}m ago`
  if (seconds > 0) return `${seconds}s ago`
  return 'Just now'
})

const awardStatus = computed(() => {
  if (!selectedWinner.value) return 'Pending'
  const winnerNotification = awardNotifications.value.find(n => n.response_id === selectedWinner.value)
  if (winnerNotification) {
    if (winnerNotification.notification_status === 'accepted') return 'Accepted'
    if (winnerNotification.notification_status === 'rejected') return 'Rejected'
    return 'Sent'
  }
  return 'Selected'
})

const rejectedAwards = computed(() => {
  return awardNotifications.value.filter(n => n.notification_status === 'rejected')
})

const getSelectedVendorName = () => {
  if (!selectedWinner.value) return ''
  const vendor = consensusRanking.value.find(p => p.response_id === selectedWinner.value) || 
                 shortlistedProposals.value.find(p => p.response_id === selectedWinner.value)
  return vendor ? (vendor.vendor_name || 'Unknown Vendor') : ''
}

const getSelectedVendorEmail = () => {
  if (!selectedWinner.value) return ''
  const vendor = consensusRanking.value.find(p => p.response_id === selectedWinner.value) || 
                 shortlistedProposals.value.find(p => p.response_id === selectedWinner.value)
  if (!vendor) return ''
  
  return vendor.vendor_email || vendor.contact_email || vendor.email || ''
}

// Methods
const changeRfp = async () => {
  // Clear current RFP ID
  currentRfpId.value = null
  rfpData.value = null
  committeeMembers.value = []
  shortlistedProposals.value = []
  consensusRanking.value = []
  selectedWinner.value = null
  awardNotifications.value = []
  
  // Stop polling
  stopPolling()
  
  // Remove RFP ID from URL
  await router.replace({ 
    path: route.path, 
    query: {} 
  })
  
  // Load available RFPs for selection
  await loadAvailableRfps()
}

const selectRfp = async (rfpId: string | number) => {
  const rfpIdStr = String(rfpId)
  currentRfpId.value = rfpIdStr
  
  // Update URL using Vue Router
  await router.replace({ 
    path: route.path, 
    query: { ...route.query, rfp_id: rfpIdStr } 
  })
  
  await loadRfpData(rfpIdStr)
  await loadConsensusData()
  await loadNotifications()
  
  // Restart polling with new RFP ID
  stopPolling()
  startPolling()
}

const loadRfpData = async (rfpId: string) => {
  try {
    const { fetchRFP } = useRfpApi()
    rfpData.value = await fetchRFP(rfpId)
  } catch (error) {
    console.error('Error loading RFP data:', error)
  }
}

const loadAvailableRfps = async () => {
  loadingRfps.value = true
  try {
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(`${API_BASE_URL}/rfps/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      const data = await response.json()
      availableRfps.value = data.results || data
    }
  } catch (error) {
    console.error('Error loading RFPs:', error)
  } finally {
    loadingRfps.value = false
  }
}

const loadConsensusData = async () => {
  if (!currentRfpId.value) {
    return
  }
  
  try {
    loading.value = true
    const rfpId = currentRfpId.value
    
    const { fetchRFP, getAuthHeaders } = useRfpApi()
    
    // Load RFP data
    rfpData.value = await fetchRFP(rfpId)
    
    // Load committee members
    const committeeResponse = await fetch(`${API_BASE_URL}/rfp/${rfpId}/committee/get/`, {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    if (committeeResponse.ok) {
      const committeeData = await committeeResponse.json()
      if (committeeData.success && committeeData.committee_members) {
        committeeMembers.value = committeeData.committee_members.map((committee) => ({
          member_id: committee.member_id,
          first_name: committee.first_name || committee.member_name || 'Committee',
          last_name: committee.last_name || 'Member',
          member_role: committee.member_role || 'Committee Member',
          is_chair: committee.is_chair || false,
          evaluation_completed: false,
          rankings: []
        }))
      }
    }
    
    // Load proposals
    const proposalsResponse = await fetch(`${API_BASE_URL}/rfp-responses-list/?rfp_id=${rfpId}`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (proposalsResponse.ok) {
      const proposalsData = await proposalsResponse.json()
      if (proposalsData.success && proposalsData.responses) {
        shortlistedProposals.value = proposalsData.responses.filter(response => 
          response.submission_status === 'SUBMITTED' || 
          response.evaluation_status === 'SUBMITTED' ||
          response.evaluation_status === 'UNDER_EVALUATION' ||
          response.evaluation_status === 'SHORTLISTED' ||
          !response.submission_status ||
          response.response_id
        )
        
        // Process proposals to ensure proper vendor names
        shortlistedProposals.value = shortlistedProposals.value.map((proposal, index) => {
          let vendorName = proposal.vendor_name
          let orgName = proposal.org
          
          if (proposal.response_documents) {
            try {
              const responseDocs = typeof proposal.response_documents === 'string' 
                ? JSON.parse(proposal.response_documents) 
                : proposal.response_documents
              
              if (responseDocs.companyInfo) {
                if (responseDocs.companyInfo.companyName) {
                  vendorName = responseDocs.companyInfo.companyName
                }
                if (responseDocs.companyInfo.contactName) {
                  orgName = responseDocs.companyInfo.contactName
                }
              }
              
              if (responseDocs.vendor_name && !vendorName) {
                vendorName = responseDocs.vendor_name
              }
              if (responseDocs.company_name && !vendorName) {
                vendorName = responseDocs.company_name
              }
            } catch (e) {
              console.log('Error parsing response_documents:', e)
            }
          }
          
          return {
            ...proposal,
            vendor_name: vendorName || `Vendor ${index + 1}`,
            org: orgName || 'Unknown Organization',
            proposed_value: proposal.proposed_value ? parseFloat(proposal.proposed_value) : (100000 + (index * 50000)),
            technical_score: proposal.technical_score && proposal.technical_score !== '' ? parseFloat(proposal.technical_score) : (85 + (index * 5) + Math.floor(Math.random() * 10)),
            commercial_score: proposal.commercial_score && proposal.commercial_score !== '' ? parseFloat(proposal.commercial_score) : (80 + (index * 5) + Math.floor(Math.random() * 10)),
            overall_score: proposal.overall_score && proposal.overall_score !== '' ? parseFloat(proposal.overall_score) : Math.round((85 + (index * 5) + 80 + (index * 5)) / 2)
          }
        })
      }
    }
    
    // Load committee evaluations
    const evaluationsResponse = await fetch(`${API_BASE_URL}/rfp/${rfpId}/final-evaluations/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (evaluationsResponse.ok) {
      const evaluationsData = await evaluationsResponse.json()
      if (evaluationsData.success && evaluationsData.evaluations) {
        committeeMembers.value.forEach(member => {
          const memberEvaluations = evaluationsData.evaluations[member.member_id] || []
          member.evaluation_completed = memberEvaluations.length > 0
          member.rankings = memberEvaluations.sort((a, b) => a.ranking_position - b.ranking_position)
        })
      }
    }
    
    // Calculate consensus ranking
    calculateConsensusRanking()
    
    // Check for new evaluations
    const currentCompletedCount = completedEvaluations.value
    if (previousCompletedCount.value > 0 && currentCompletedCount > previousCompletedCount.value) {
      const newEvaluations = currentCompletedCount - previousCompletedCount.value
      showNotification(`🎉 ${newEvaluations} new evaluation${newEvaluations > 1 ? 's' : ''} submitted!`)
    }
    previousCompletedCount.value = currentCompletedCount
    
    lastUpdated.value = new Date().toISOString()
    
  } catch (error) {
    console.error('Error loading consensus data:', error)
  } finally {
    loading.value = false
  }
}

const calculateConsensusRanking = () => {
  if (shortlistedProposals.value.length === 0) {
    consensusRanking.value = []
    return
  }
  
  const hasCommitteeRankings = committeeMembers.value.some(member => 
    member.evaluation_completed && member.rankings && member.rankings.length > 0
  )
  
  if (hasCommitteeRankings) {
    const vendorScores: Record<string, {
      response_id: any
      vendor_name: string
      org: string
      scores: number[]
      vote_count: number
    }> = {}
    
    committeeMembers.value.forEach(member => {
      if (member.rankings) {
        member.rankings.forEach((ranking: any) => {
          const responseId = ranking.response_id
          if (!vendorScores[responseId]) {
            vendorScores[responseId] = {
              response_id: responseId,
              vendor_name: ranking.vendor_name,
              org: ranking.org,
              scores: [],
              vote_count: 0
            }
          }
          
          if (ranking.ranking_score) {
            vendorScores[responseId].scores.push(ranking.ranking_score)
            vendorScores[responseId].vote_count += 1
          }
        })
      }
    })
    
    consensusRanking.value = Object.values(vendorScores)
      .map((vendor: { response_id: any; vendor_name: string; org: string; scores: number[]; vote_count: number }) => {
        const avgScore = vendor.scores.length > 0 
          ? vendor.scores.reduce((sum, score) => sum + score, 0) / vendor.scores.length 
          : 0
        
        return {
          response_id: vendor.response_id,
          vendor_name: vendor.vendor_name,
          org: vendor.org,
          vote_count: vendor.vote_count,
          consensus_score: avgScore,
          min_score: Math.min(...vendor.scores),
          max_score: Math.max(...vendor.scores),
          score_range: `${Math.min(...vendor.scores)} - ${Math.max(...vendor.scores)}`
        }
      })
      .sort((a, b) => b.consensus_score - a.consensus_score)
  } else {
    consensusRanking.value = shortlistedProposals.value
      .map(proposal => ({
        response_id: proposal.response_id,
        vendor_name: proposal.vendor_name,
        org: proposal.org,
        proposed_value: proposal.proposed_value,
        technical_score: proposal.technical_score,
        commercial_score: proposal.commercial_score,
        overall_score: proposal.overall_score,
        consensus_score: proposal.overall_score || 0
      }))
      .sort((a, b) => b.consensus_score - a.consensus_score)
  }
}

const loadNotifications = async () => {
  if (!currentRfpId.value) return
  const rfpId = currentRfpId.value
  
  loadingNotifications.value = true
  try {
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(`${API_BASE_URL}/rfp/${rfpId}/award-notification/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        awardNotifications.value = data.notifications.map(notification => {
          const vendorDetails = consensusRanking.value.find(v => v.response_id === notification.response_id) ||
                               shortlistedProposals.value.find(v => v.response_id === notification.response_id)
          
          return {
            ...notification,
            vendor_name: notification.vendor_name || vendorDetails?.vendor_name || 'Unknown Vendor',
            vendor_email: notification.recipient_email || notification.vendor_email || vendorDetails?.vendor_email || vendorDetails?.contact_email || '',
          }
        })
      }
    } else if (response.status === 500) {
      awardNotifications.value = []
    }
  } catch (error) {
    console.error('Error loading notifications:', error)
    awardNotifications.value = []
  } finally {
    loadingNotifications.value = false
  }
}

const sendAwardNotification = async () => {
  if (!selectedWinner.value) {
    PopupService.warning('Please select a vendor first', 'No Vendor Selected')
    return
  }
  
  if (!currentRfpId.value) {
    PopupService.error('No RFP ID found', 'Error')
    return
  }
  const rfpId = currentRfpId.value
  
  const selectedVendor = consensusRanking.value.find(v => v.response_id === selectedWinner.value) ||
                         shortlistedProposals.value.find(v => v.response_id === selectedWinner.value)
  
  if (!selectedVendor) {
    PopupService.error('Vendor details not found', 'Vendor Not Found')
    return
  }
  
  const vendorEmail = selectedVendor.vendor_email || 
                     selectedVendor.contact_email || 
                     selectedVendor.email || 
                     ''
  
  if (!vendorEmail || vendorEmail === 'vendor@example.com') {
    PopupService.error('Vendor email not found. Please ensure the vendor has provided their contact email in the RFP response.', 'Email Not Found')
    return
  }
  
  const { getAuthHeaders } = useRfpApi()
  const payload = {
    response_id: selectedWinner.value,
    vendor_email: vendorEmail,
    vendor_name: selectedVendor.vendor_name || selectedVendor.org || 'Vendor',
    notification_type: 'winner',
    award_message: awardMessage.value || 'Congratulations! Your proposal has been selected as the winner.',
    next_steps: nextSteps.value || 'Please respond to this notification within 7 days to accept or decline the award.'
  }
  
  sendingNotification.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/rfp/${rfpId}/award-notification/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(payload)
    })
    
    const responseText = await response.text()
    let data
    try {
      data = JSON.parse(responseText)
    } catch (e) {
      PopupService.error('Server returned invalid response.', 'Invalid Response')
      return
    }
    
    if (response.ok && data.success) {
      PopupService.success(`Award notification sent successfully to ${data.recipient_email || vendorEmail}`, 'Notification Sent')
      if (currentRfpId.value) {
        await notificationService.createRFPAwardNotification('award_issued', {
          rfp_id: currentRfpId.value,
          response_id: selectedWinner.value,
          rfp_title: rfpData.value?.rfp_title,
          vendor_name: selectedVendor.vendor_name,
          award_amount: selectedVendor.proposed_value
        })
      }
      await loadNotifications()
    } else {
      PopupService.error('Failed to send notification: ' + (data.error || 'Unknown error'), 'Send Failed')
    }
  } catch (error) {
    console.error('Error sending award notification:', error)
    PopupService.error('Error sending notification: ' + error.message, 'Network Error')
  } finally {
    sendingNotification.value = false
  }
}

const sendParticipantNotifications = async () => {
  if (shortlistedProposals.value.length === 0) {
    PopupService.warning('No participants to notify', 'No Participants')
    return
  }
  
  if (!currentRfpId.value) return
  const rfpId = currentRfpId.value
  
  sendingNotification.value = true
  try {
    const { getAuthHeaders } = useRfpApi()
    const participants = shortlistedProposals.value.filter(p => p.response_id !== selectedWinner.value)
    let successCount = 0
    let failCount = 0
    
    for (const participant of participants) {
      const participantEmail = participant.vendor_email || participant.contact_email || participant.email || ''
      
      if (!participantEmail || participantEmail === 'vendor@example.com') {
        failCount++
        continue
      }
      
      const response = await fetch(`${API_BASE_URL}/rfp/${rfpId}/award-notification/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          response_id: participant.response_id,
          vendor_email: participantEmail,
          vendor_name: participant.vendor_name || participant.org || 'Participant',
          notification_type: 'participant_thanks',
          award_message: 'Thank you for your participation in our RFP process.',
          next_steps: 'We appreciate your interest and will keep you in mind for future opportunities.'
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          successCount++
        } else {
          failCount++
        }
      } else {
        failCount++
      }
    }
    
    PopupService.success(`Participant notifications sent: ${successCount} successful, ${failCount} failed`, 'Notifications Sent')
    await loadNotifications()
  } catch (error) {
    console.error('Error sending participant notifications:', error)
    PopupService.error('Error sending notifications: ' + error.message, 'Send Error')
  } finally {
    sendingNotification.value = false
  }
}

const createVendorCredentials = async (notificationId) => {
  if (!currentRfpId.value) {
    PopupService.error('No RFP ID found', 'Error')
    return
  }
  const rfpId = currentRfpId.value
  
  creatingCredentials.value = true
  try {
    const { getAuthHeaders } = useRfpApi()
    const response = await fetch(`${API_BASE_URL}/vendor-credentials/${notificationId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      }
    })
   
    const data = await response.json()
   
    if (response.ok && data.success) {
      PopupService.success(
        `Vendor credentials created and sent to ${data.data.vendor_email}`,
        'Credentials Created'
      )
      await notificationService.createRFPAwardNotification('credentials_created', {
        rfp_id: rfpId,
        vendor_email: data.data.vendor_email,
        user_id: data.data.user_id
      })
    } else {
      PopupService.error(data.error || 'Failed to create vendor credentials', 'Creation Failed')
    }
  } catch (error) {
    console.error('Error creating vendor credentials:', error)
    PopupService.error('Error creating vendor credentials: ' + error.message, 'Network Error')
  } finally {
    creatingCredentials.value = false
  }
}

const selectNextVendor = (rejectedResponseId) => {
  const availableVendors = consensusRanking.value.filter(p => 
    p.response_id !== rejectedResponseId && 
    !awardNotifications.value.some(n => n.response_id === p.response_id && (n.notification_status === 'rejected' || n.notification_status === 'sent' || n.notification_status === 'accepted'))
  )
  
  if (availableVendors.length > 0) {
    selectedWinner.value = availableVendors[0].response_id
    PopupService.success(`Selected next vendor: ${availableVendors[0].vendor_name || 'Vendor'}`, 'Vendor Selected')
  } else {
    PopupService.warning('No more vendors available for selection', 'No Vendors')
  }
}

const selectAndSendToNextVendor = async (rejectedResponseId) => {
  const availableVendors = consensusRanking.value.filter(p => 
    p.response_id !== rejectedResponseId && 
    !awardNotifications.value.some(n => n.response_id === p.response_id && (n.notification_status === 'rejected' || n.notification_status === 'sent' || n.notification_status === 'accepted'))
  )
  
  if (availableVendors.length === 0) {
    PopupService.warning('No more vendors available for award notification', 'No Vendors')
    return
  }
  
  const nextVendor = availableVendors[0]
  const vendorEmail = nextVendor.vendor_email || nextVendor.contact_email || nextVendor.email || ''
  if (!vendorEmail || vendorEmail === 'vendor@example.com') {
    PopupService.error(
      `Cannot send award to ${nextVendor.vendor_name || 'next vendor'}: No valid email address found`,
      'Email Not Found'
    )
    return
  }
  
  selectedWinner.value = nextVendor.response_id
  PopupService.info(
    `Preparing to send award notification to ${nextVendor.vendor_name || 'Vendor'} (${vendorEmail})`,
    'Sending to Next Vendor'
  )
  
  await new Promise(resolve => setTimeout(resolve, 500))
  await sendAwardNotification()
}

const exportReport = async () => {
  if (!currentRfpId.value) {
    PopupService.warning('Please select an RFP first', 'No RFP Selected')
    return
  }

  exportLoading.value = true
  try {
    console.log('📊 Starting Consensus & Award Report Export...')
    
    // Create new PDF document
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    let yPosition = 20
    const margin = 20
    const lineHeight = 7
    const sectionSpacing = 15
    
    // Helper function to check if new page needed
    const checkNewPage = (requiredSpace = 20) => {
      if (yPosition + requiredSpace > pageHeight - margin) {
        pdf.addPage()
        yPosition = margin
        return true
      }
      return false
    }
    
    // Helper function to add text with word wrap
    const addText = (text: string, fontSize = 12, isBold = false, color = [0, 0, 0]) => {
      if (text == null || text === '') return
      
      pdf.setFontSize(fontSize)
      pdf.setFont('helvetica', isBold ? 'bold' : 'normal')
      pdf.setTextColor(color[0], color[1], color[2])
      
      const safeText = String(text)
      const maxWidth = pageWidth - (2 * margin)
      const lines = pdf.splitTextToSize(safeText, maxWidth)
      
      lines.forEach((line: string) => {
        checkNewPage(lineHeight)
        if (line && line.trim() !== '') {
          pdf.text(line, margin, yPosition)
        }
        yPosition += lineHeight
      })
    }
    
    // Helper function to add a section header
    const addSectionHeader = (title: string) => {
      checkNewPage(sectionSpacing)
      yPosition += 5
      addText(title, 16, true, [0, 0, 0])
      yPosition += 5
      // Draw line under header
      pdf.setDrawColor(200, 200, 200)
      pdf.line(margin, yPosition, pageWidth - margin, yPosition)
      yPosition += 10
    }
    
    // Helper function to add table row
    const addTableRow = (label: string, value: string, isHeader = false) => {
      checkNewPage(lineHeight + 2)
      pdf.setFontSize(isHeader ? 12 : 10)
      pdf.setFont('helvetica', isHeader ? 'bold' : 'normal')
      pdf.setTextColor(isHeader ? 0 : 0, isHeader ? 0 : 0, isHeader ? 0 : 0)
      
      pdf.text(label, margin, yPosition)
      pdf.text(value, pageWidth - margin - 50, yPosition, { align: 'right' })
      yPosition += lineHeight + 2
    }
    
    // Title
    addText('Consensus & Award Management Report', 20, true, [0, 0, 0])
    yPosition += 5
    addText(`Generated on: ${new Date().toLocaleString()}`, 10, false, [100, 100, 100])
    yPosition += 10
    
    // RFP Information
    addSectionHeader('RFP Information')
    if (rfpData.value) {
      addTableRow('RFP Title', rfpData.value.rfp_title || 'N/A', false)
      addTableRow('RFP Number', rfpData.value.rfp_number || 'N/A', false)
      addTableRow('RFP Type', rfpData.value.rfp_type || 'N/A', false)
      addTableRow('Status', rfpData.value.status || 'N/A', false)
      if (rfpData.value.estimated_value) {
        addTableRow('Estimated Value', `$${parseFloat(rfpData.value.estimated_value).toLocaleString()}`, false)
      }
    }
    yPosition += 5
    
    // Committee Overview
    addSectionHeader('Committee Overview')
    addTableRow('Total Committee Members', String(committeeMembers.value.length), false)
    addTableRow('Evaluations Complete', `${completedEvaluations.value}/${committeeMembers.value.length}`, false)
    addTableRow('Consensus Level', `${consensusLevel.value}%`, false)
    addTableRow('Finalists', String(consensusRanking.value.length), false)
    yPosition += 5
    
    // All Finalists List
    if (consensusRanking.value.length > 0) {
      addSectionHeader('All Finalists')
      addText(`Total Finalists: ${consensusRanking.value.length}`, 12, false, [100, 100, 100])
      yPosition += 5
      
      consensusRanking.value.forEach((item: any, index: number) => {
        checkNewPage(35)
        addText(`Finalist #${index + 1}: ${getVendorName(item)}`, 12, true, [0, 0, 0])
        yPosition += 3
        addText(`Organization: ${getOrganizationName(item)}`, 10, false, [100, 100, 100])
        yPosition += 3
        
        // Create a table-like structure for better readability
        const details = []
        details.push(`Consensus Score: ${(item.consensus_score || item.overall_score || 0).toFixed(2)}`)
        if (item.proposed_value) {
          details.push(`Proposed Value: $${item.proposed_value.toLocaleString()}`)
        }
        if (item.technical_score) {
          details.push(`Technical Score: ${item.technical_score}/100`)
        }
        if (item.commercial_score) {
          details.push(`Commercial Score: ${item.commercial_score}/100`)
        }
        if (item.vote_count) {
          details.push(`Evaluators: ${item.vote_count}`)
        }
        if (item.score_range) {
          details.push(`Score Range: ${item.score_range}`)
        }
        
        details.forEach(detail => {
          addText(detail, 9, false, [80, 80, 80])
          yPosition += 3
        })
        
        // Check notification status for this vendor
        const vendorNotification = awardNotifications.value.find((n: any) => n.response_id === item.response_id && n.notification_type === 'winner')
        if (vendorNotification) {
          yPosition += 2
          if (vendorNotification.notification_status === 'accepted') {
            addText('Status: ✓ Award Accepted', 9, true, [0, 128, 0])
          } else if (vendorNotification.notification_status === 'rejected') {
            addText('Status: ✗ Award Rejected', 9, true, [220, 38, 38])
          } else if (vendorNotification.notification_status === 'sent') {
            addText('Status: ⏳ Notification Sent', 9, true, [255, 165, 0])
          }
        } else if (selectedWinner.value === item.response_id) {
          addText('Status: ✓ Currently Selected', 9, true, [0, 128, 0])
        }
        
        yPosition += 5
      })
    }
    
    // Committee Members
    if (committeeMembers.value.length > 0) {
      addSectionHeader('Committee Members & Evaluations')
      
      committeeMembers.value.forEach((member: any) => {
        checkNewPage(25)
        addText(`${member.first_name} ${member.last_name}`, 12, true, [0, 0, 0])
        yPosition += 3
        addText(`Role: ${member.member_role || 'Committee Member'}`, 10, false, [100, 100, 100])
        if (member.is_chair) {
          addText('👑 Chair', 10, false, [255, 165, 0])
        }
        yPosition += 3
        addTableRow('Evaluation Status', member.evaluation_completed ? 'Completed' : 'Pending', false)
        
        if (member.evaluation_completed && member.rankings && member.rankings.length > 0) {
          yPosition += 3
          addText('Top Rankings:', 10, true, [0, 0, 0])
          member.rankings.slice(0, 3).forEach((ranking: any, idx: number) => {
            addText(`${idx + 1}. ${getVendorName(ranking)} - Score: ${ranking.ranking_score}`, 9, false, [100, 100, 100])
          })
        }
        yPosition += 5
      })
    }
    
    // Winner Selection History
    const winnerNotifications = awardNotifications.value.filter((n: any) => n.notification_type === 'winner')
    if (winnerNotifications.length > 0 || selectedWinner.value) {
      addSectionHeader('Winner Selection History')
      
      // Current Selection
      if (selectedWinner.value) {
        const currentVendor = consensusRanking.value.find((v: any) => v.response_id === selectedWinner.value) ||
                             shortlistedProposals.value.find((v: any) => v.response_id === selectedWinner.value)
        
        if (currentVendor) {
          checkNewPage(25)
          addText('Current Selection', 12, true, [0, 0, 0])
          yPosition += 3
          addTableRow('Vendor', getSelectedVendorName(), false)
          addTableRow('Organization', getOrganizationName(currentVendor), false)
          const email = getSelectedVendorEmail()
          addTableRow('Contact Email', email && email !== 'vendor@example.com' ? email : 'Not Available', false)
          addTableRow('Award Status', awardStatus.value, false)
          addTableRow('Selection Date', new Date().toLocaleDateString(), false)
          yPosition += 5
        }
      }
      
      // Historical Winner Selections (sorted by sent date)
      if (winnerNotifications.length > 0) {
        const sortedNotifications = [...winnerNotifications].sort((a: any, b: any) => {
          const dateA = a.sent_date ? new Date(a.sent_date).getTime() : 0
          const dateB = b.sent_date ? new Date(b.sent_date).getTime() : 0
          return dateA - dateB
        })
        
        addText('Selection Timeline', 12, true, [0, 0, 0])
        yPosition += 5
        
        sortedNotifications.forEach((notification: any, index: number) => {
          checkNewPage(30)
          addText(`Selection #${index + 1}: ${notification.vendor_name}`, 11, true, [0, 0, 0])
          yPosition += 3
          
          addTableRow('Email', notification.vendor_email || 'N/A', false)
          addTableRow('Status', notification.notification_status.toUpperCase(), false)
          
          if (notification.sent_date) {
            addTableRow('Notification Sent', formatDate(notification.sent_date), false)
          }
          
          if (notification.response_date) {
            if (notification.notification_status === 'accepted') {
              addTableRow('Accepted On', formatDate(notification.response_date), false)
              addText('✓ Vendor accepted the award', 9, false, [0, 128, 0])
            } else if (notification.notification_status === 'rejected') {
              addTableRow('Rejected On', formatDate(notification.response_date), false)
              addText('✗ Vendor rejected the award', 9, false, [220, 38, 38])
            }
          } else if (notification.notification_status === 'sent') {
            addText('⏳ Awaiting vendor response', 9, false, [255, 165, 0])
          }
          
          yPosition += 5
        })
      }
      
      // Summary
      if (winnerNotifications.length > 0) {
        checkNewPage(15)
        yPosition += 5
        addText('Summary', 12, true, [0, 0, 0])
        yPosition += 3
        const acceptedCount = winnerNotifications.filter((n: any) => n.notification_status === 'accepted').length
        const rejectedCount = winnerNotifications.filter((n: any) => n.notification_status === 'rejected').length
        const pendingCount = winnerNotifications.filter((n: any) => n.notification_status === 'sent').length
        
        addTableRow('Total Selections', String(winnerNotifications.length), false)
        addTableRow('Accepted', String(acceptedCount), false)
        addTableRow('Rejected', String(rejectedCount), false)
        addTableRow('Pending Response', String(pendingCount), false)
      }
    }
    
    // All Award Notifications (including participant thanks)
    if (awardNotifications.value.length > 0) {
      addSectionHeader('All Notifications Sent')
      
      awardNotifications.value.forEach((notification: any, index: number) => {
        checkNewPage(20)
        addText(`Notification #${index + 1}`, 11, true, [0, 0, 0])
        yPosition += 3
        addTableRow('Vendor', notification.vendor_name || 'N/A', false)
        addTableRow('Email', notification.vendor_email || 'N/A', false)
        addTableRow('Type', notification.notification_type === 'winner' ? 'Winner Notification' : 'Participant Thanks', false)
        addTableRow('Status', notification.notification_status.toUpperCase(), false)
        if (notification.sent_date) {
          addTableRow('Sent Date', formatDate(notification.sent_date), false)
        }
        if (notification.response_date) {
          addTableRow('Response Date', formatDate(notification.response_date), false)
        }
        yPosition += 5
      })
    }
    
    // Footer
    const totalPages = pdf.getNumberOfPages()
    for (let i = 1; i <= totalPages; i++) {
      pdf.setPage(i)
      pdf.setFontSize(8)
      pdf.setTextColor(150, 150, 150)
      pdf.text(
        `Page ${i} of ${totalPages}`,
        pageWidth / 2,
        pageHeight - 10,
        { align: 'center' }
      )
    }
    
    // Save PDF
    const fileName = `RFP_Consensus_Award_Report_${rfpData.value?.rfp_number || currentRfpId.value}_${new Date().toISOString().split('T')[0]}.pdf`
    pdf.save(fileName)
    
    PopupService.success('Report exported successfully!', 'Export Complete')
    console.log('✅ PDF Export completed successfully')
  } catch (error) {
    console.error('❌ Error exporting report:', error)
    PopupService.error('Failed to export report. Please try again.', 'Export Failed')
  } finally {
    exportLoading.value = false
  }
}

const goToComparison = () => {
  if (currentRfpId.value) {
    router.push(`/rfp-comparison?rfp_id=${currentRfpId.value}`)
  } else {
    router.push('/rfp-comparison')
  }
}

const goToDashboard = () => {
  router.push('/rfp-dashboard')
}

const refreshData = async () => {
  console.log('🔄 Manual refresh triggered...')
  await loadConsensusData()
  await loadNotifications()
}

const startPolling = () => {
  if (pollingInterval.value) return
  
  console.log('🔄 Starting real-time polling...')
  isPolling.value = true
  
  pollingInterval.value = setInterval(async () => {
    try {
      await loadConsensusData()
      await loadNotifications()
    } catch (error) {
      console.error('Error during polling:', error)
    }
  }, 5000)
}

const stopPolling = () => {
  if (pollingInterval.value) {
    console.log('⏹️ Stopping real-time polling...')
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
    isPolling.value = false
  }
}

const showNotification = (message) => {
  const notification = {
    id: Date.now(),
    message,
    timestamp: new Date().toISOString()
  }
  
  realTimeNotifications.value.unshift(notification)
  
  setTimeout(() => {
    const index = realTimeNotifications.value.findIndex(n => n.id === notification.id)
    if (index > -1) {
      realTimeNotifications.value.splice(index, 1)
    }
  }, 5000)
}

const removeNotification = (notificationId) => {
  const index = realTimeNotifications.value.findIndex(n => n.id === notificationId)
  if (index > -1) {
    realTimeNotifications.value.splice(index, 1)
  }
}

// Helper functions
const getVendorName = (item) => {
  if (item.vendor_name) return item.vendor_name
  
  const proposal = shortlistedProposals.value.find(p => p.response_id === item.response_id)
  if (proposal) return proposal.vendor_name
  
  return `Vendor ${item.response_id}`
}

const getOrganizationName = (item) => {
  if (item.org) return item.org
  
  const proposal = shortlistedProposals.value.find(p => p.response_id === item.response_id)
  if (proposal) return proposal.org
  
  return 'Unknown Organization'
}

const getNotificationIcon = (status) => {
  switch (status) {
    case 'sent': return CheckCircle2
    case 'pending': return Clock
    case 'accepted': return CheckCircle2
    case 'rejected': return XCircle
    case 'acknowledged': return CheckCircle2
    default: return Mail
  }
}

const getNotificationStatusClass = (status) => {
  switch (status) {
    case 'sent': return 'bg-green-100 text-green-800'
    case 'pending': return 'bg-yellow-100 text-yellow-800'
    case 'accepted': return 'bg-green-100 text-green-800'
    case 'rejected': return 'bg-red-100 text-red-800'
    case 'acknowledged': return 'bg-blue-100 text-blue-800'
    default: return 'bg-gray-100 text-gray-800'
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

// Watch for route query parameter changes
watch(() => route.query.rfp_id, async (newRfpId, oldRfpId) => {
  // If RFP ID was removed from URL, show selection interface
  if (!newRfpId && oldRfpId && currentRfpId.value) {
    console.log('🔄 RFP ID removed from URL, showing selection interface')
    changeRfp()
    return
  }
  
  // If RFP ID changed to a new value
  if (newRfpId && newRfpId !== oldRfpId && newRfpId !== currentRfpId.value) {
    console.log('🔄 RFP ID changed in URL:', newRfpId)
    currentRfpId.value = String(newRfpId)
    await loadRfpData(String(newRfpId))
    await loadConsensusData()
    await loadNotifications()
    // Restart polling with new RFP ID
    stopPolling()
    startPolling()
  }
}, { immediate: false })

// Initialize component
const initializeComponent = async () => {
  await loggingService.logPageView('RFP', 'Phase 8 & 9 - Consensus & Award')
  
  // Check for RFP ID in route query params first (Vue Router)
  const rfpIdFromRoute = route.query.rfp_id as string | undefined
  
  // Fallback to URL search params if route query doesn't have it
  let rfpId = rfpIdFromRoute
  if (!rfpId) {
    const urlParams = new URLSearchParams(window.location.search)
    rfpId = urlParams.get('rfp_id') || undefined
  }
  
  if (rfpId) {
    // RFP ID found in URL, load that RFP
    currentRfpId.value = String(rfpId)
    await loadRfpData(String(rfpId))
    await loadConsensusData()
    await loadNotifications()
    startPolling()
  } else {
    // No RFP ID in URL - always show selection interface
    // Clear any existing RFP ID and ensure URL is clean
    currentRfpId.value = null
    rfpData.value = null
    committeeMembers.value = []
    shortlistedProposals.value = []
    consensusRanking.value = []
    selectedWinner.value = null
    awardNotifications.value = []
    
    // Ensure URL doesn't have rfp_id parameter
    if (route.query.rfp_id) {
      await router.replace({ 
        path: route.path, 
        query: {} 
      })
    }
    
    // Load available RFPs for selection
    await loadAvailableRfps()
  }
}

onMounted(async () => {
  await initializeComponent()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slide-in 0.3s ease-out;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
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
</style>