<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="space-y-8">
    <!-- Header -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
    <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
              <h1 class="text-3xl font-bold tracking-tight text-gray-900">Phase 9: Contract Award</h1>
              <p class="text-gray-600 mt-2">
          Finalize contract award and notify all stakeholders of the decision.
        </p>
              <div class="mt-2 flex items-center gap-4 text-sm text-gray-500">
                <span>RFP: {{ rfpData?.rfp_title || 'Loading...' }}</span>
                <span>#{{ rfpData?.rfp_number }}</span>
                <span v-if="consensusRanking.length > 0">{{ consensusRanking.length }} finalists</span>
              </div>
      </div>
      <div class="flex items-center gap-2">
              <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
          Contract Award
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

    <!-- Award Overview -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
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
              <div class="p-3 rounded-lg bg-green-50">
                <CheckCircle2 class="h-6 w-6 text-green-600" />
            </div>
            <div>
                <p class="text-sm font-medium text-gray-600">Winner Selected</p>
                <p class="text-2xl font-bold text-gray-900">{{ selectedWinner ? 'Yes' : 'No' }}</p>
              </div>
            </div>
          </div>
          
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div class="flex items-center gap-4">
              <div class="p-3 rounded-lg bg-blue-50">
                <Mail class="h-6 w-6 text-blue-600" />
            </div>
            <div>
                <p class="text-sm font-medium text-gray-600">Notifications Sent</p>
                <p class="text-2xl font-bold text-gray-900">{{ notifications.length }}</p>
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

        <!-- RFP Selection -->
        <div v-if="!selectedRfpId" class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div class="flex items-center justify-between mb-6">
            <div>
              <h3 class="text-2xl font-bold text-gray-900">Select RFP for Award</h3>
              <p class="text-gray-600 mt-1">Choose an RFP to manage contract awards</p>
            </div>
          </div>
          
          <div v-if="loadingRfps" class="text-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p class="text-gray-600 mt-2">Loading RFPs...</p>
          </div>
          
          <div v-else-if="availableRfps.length === 0" class="text-center py-8">
            <p class="text-gray-600">No RFPs available for award management</p>
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
              <p class="text-sm text-gray-600 mb-2">{{ rfp.description?.substring(0, 100) }}...</p>
              <div class="flex items-center justify-between text-xs text-gray-500">
                <span>{{ rfp.status }}</span>
                <span>{{ new Date(rfp.created_at).toLocaleDateString() }}</span>
            </div>
            </div>
            </div>
          </div>

        <!-- Award Management -->
        <div v-else class="space-y-6">
          <!-- RFP Info -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div class="flex items-center justify-between mb-4">
              <div>
                <h2 class="text-xl font-bold text-gray-900">{{ rfpData?.rfp_title }}</h2>
                <p class="text-gray-600">{{ rfpData?.rfp_number }}</p>
              </div>
              <button 
                @click="selectedRfpId = null"
                class="text-gray-400 hover:text-gray-600"
              >
                <X class="h-5 w-5" />
              </button>
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

          <!-- Consensus Ranking & Winner Selection -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div class="flex items-center justify-between mb-6">
              <div>
                <h3 class="text-xl font-bold text-gray-900">Final Consensus Ranking</h3>
                <p class="text-sm text-gray-600 mt-1">Select the vendor to receive the contract award based on consensus ranking</p>
              </div>
              <button 
                @click="refreshData"
                class="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 transition-colors"
              >
                <RefreshCw class="h-4 w-4 mr-1" />
                Refresh Data
              </button>
            </div>
            
            <div v-if="loading" class="text-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p class="text-gray-600 mt-2">Loading consensus data...</p>
            </div>
            
            <div v-else-if="consensusRanking.length === 0" class="text-center py-8">
              <div class="text-gray-400 mb-4">
                <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </div>
              <h3 class="text-lg font-medium text-gray-900 mb-2">No Consensus Data Available</h3>
              <p class="text-gray-600 mb-4">Please complete the consensus phase first.</p>
              <button 
                @click="goToConsensus"
                class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 transition-colors"
              >
                Go to Consensus Phase
                <ArrowRight class="h-4 w-4 ml-2" />
              </button>
            </div>
            
            <div v-else class="space-y-4">
              <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <div class="flex items-start gap-3">
                  <div class="p-2 bg-blue-100 rounded-lg">
                    <Award class="h-5 w-5 text-blue-600" />
                  </div>
                  <div class="flex-1">
                    <h4 class="text-sm font-medium text-blue-900 mb-1">Award Selection Guidelines</h4>
                    <p class="text-sm text-blue-700">
                      The vendors are ranked based on committee consensus scores. You can select the top-ranked vendor or choose a different vendor based on your business requirements.
                    </p>
                  </div>
                </div>
              </div>
              
              <div class="space-y-3">
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
                  @click="selectedWinner = item.response_id"
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
                          ✓ Selected
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
                    <div v-if="item.vote_count" class="text-xs text-gray-500 mt-1">{{ item.vote_count }} evaluator(s)</div>
                    <div v-if="item.score_range" class="text-xs text-gray-500">Range: {{ item.score_range }}</div>
                  </div>
                </div>
              </div>
              
              <div v-if="selectedWinner" class="mt-6 p-4 rounded-lg" :class="getSelectedVendorEmail() && getSelectedVendorEmail() !== 'vendor@example.com' ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'">
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
          </div>

          <!-- Award Notification -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
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
              <p class="text-gray-600">Please select a vendor to send the award notification</p>
            </div>
          </div>

          <!-- Notification Status -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 class="text-xl font-bold text-gray-900 mb-6">Notification Status</h3>
            
            <div v-if="loadingNotifications" class="text-center py-4">
              <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto"></div>
              <p class="text-gray-600 mt-2">Loading notifications...</p>
            </div>
            
            <div v-else-if="notifications.length === 0" class="text-center py-8">
              <p class="text-gray-600">No notifications sent yet</p>
        </div>
            
            <div v-else class="space-y-4">
              <div 
                v-for="notification in notifications" 
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

    <!-- Actions -->
          <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div class="flex gap-2">
                <button
                  @click="generateContract"
                  class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
              <FileText class="h-4 w-4 mr-2" />
              Generate Contract
                </button>
                <button
                  @click="exportReport"
                  class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
              <Download class="h-4 w-4 mr-2" />
              Export Report
                </button>
          </div>
          <div class="flex gap-2">
                <button 
                  @click="goToConsensus"
                  class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
              Previous: Consensus
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
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useRfpApi } from '@/composables/useRfpApi'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'
import { 
  Award,
  Trophy,
  Building2,
  CheckCircle2,
  Mail,
  Clock,
  XCircle,
  FileText,
  Download,
  ArrowRight,
  ArrowLeft,
  Users,
  RefreshCw,
  X
} from 'lucide-vue-next'

const router = useRouter()
const API_BASE_URL = 'https://grc-tprm.vardaands.com/api/tprm/rfp'
const { getAuthHeaders } = useRfpApi()

// State
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const selectedRfpId = ref(null)
const availableRfps = ref([])
const rfpData = ref(null)
const shortlistedProposals = ref([])
const consensusRanking = ref([])
const selectedWinner = ref(null)
const notifications = ref([])
const loading = ref(false)
const loadingRfps = ref(false)
const loadingNotifications = ref(false)
const sendingNotification = ref(false)
const awardMessage = ref('')
const nextSteps = ref('')
const pollingInterval = ref(null)
const isPolling = ref(false)
const lastUpdated = ref(null)
const creatingCredentials = ref(false)
 
// Computed
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
  
  // Try multiple possible email fields
  return vendor.vendor_email || vendor.contact_email || vendor.email || ''
}

const awardStatus = computed(() => {
  if (!selectedWinner.value) return 'Pending'
  const winnerNotification = notifications.value.find(n => n.response_id === selectedWinner.value)
  if (winnerNotification) {
    if (winnerNotification.notification_status === 'accepted') return 'Accepted'
    if (winnerNotification.notification_status === 'rejected') return 'Rejected'
    return 'Sent'
  }
  return 'Selected'
})

const timeSinceUpdate = computed(() => {
  if (!lastUpdated.value) return 'Never'
  const now = new Date()
  const diff = now - new Date(lastUpdated.value)
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(diff / 60)
  
  if (minutes > 0) return `${minutes}m ago`
  if (seconds > 0) return `${seconds}s ago`
  return 'Just now'
})

const rejectedAwards = computed(() => {
  return notifications.value.filter(n => n.notification_status === 'rejected')
})

// Methods
const selectRfp = async (rfpId) => {
  selectedRfpId.value = rfpId
  await loadRfpData(rfpId)
  await loadConsensusData()
  await loadNotifications()
}

const loadRfpData = async (rfpId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/rfps/${rfpId}/get_full_details/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      const data = await response.json()
      rfpData.value = data.rfp
    }
  } catch (error) {
    console.error('Error loading RFP data:', error)
  }
}

const loadConsensusData = async () => {
  if (!selectedRfpId.value) return
  
  loading.value = true
  try {
    console.log('🔄 Loading consensus ranking data...')
    
    // First, load RFP responses to get vendor details
    const responsesResponse = await fetch(`${API_BASE_URL}/rfp-responses-list/?rfp_id=${selectedRfpId.value}`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    let rfpResponses = []
    if (responsesResponse.ok) {
      const responsesData = await responsesResponse.json()
      console.log('📊 RFP responses data (FULL):', JSON.stringify(responsesData, null, 2))
      if (responsesData.success && responsesData.responses) {
        rfpResponses = responsesData.responses
        shortlistedProposals.value = rfpResponses
        
        // Debug: Log each response to see what fields are available
        console.log('🔍 Analyzing RFP responses:')
        rfpResponses.forEach((response, index) => {
          console.log(`Response ${index + 1} (ID: ${response.response_id}):`, {
            vendor_name: response.vendor_name,
            org: response.org,
            contact_email: response.contact_email,
            vendor_email: response.vendor_email,
            email: response.email,
            has_response_documents: !!response.response_documents,
            response_documents_keys: response.response_documents ? Object.keys(response.response_documents) : []
          })
        })
      }
    }
    
    // Create a map of response_id to vendor details for quick lookup
    const vendorMap = {}
    rfpResponses.forEach(proposal => {
      // The backend already extracts these fields from response_documents
      // and returns them at the top level of the proposal object
      let vendorName = proposal.vendor_name || ''
      let orgName = proposal.org || ''
      let vendorEmail = proposal.contact_email || ''
      
      console.log(`📋 Initial vendor data for ${proposal.response_id}:`, {
        vendor_name: vendorName,
        org: orgName,
        contact_email: vendorEmail,
        has_response_docs: !!proposal.response_documents
      })
      
      // ALWAYS try to extract from response_documents as backup
      if (proposal.response_documents) {
        try {
          const responseDocs = typeof proposal.response_documents === 'string' 
            ? JSON.parse(proposal.response_documents) 
            : proposal.response_documents
          
          console.log(`📄 Response documents for ${proposal.response_id}:`, JSON.stringify(responseDocs, null, 2))
          
          // Check top-level fields first
          if (responseDocs.contact_email && !vendorEmail) {
            vendorEmail = responseDocs.contact_email
            console.log(`✅ Found email in responseDocs.contact_email: ${vendorEmail}`)
          }
          if (responseDocs.vendor_name && !vendorName) {
            vendorName = responseDocs.vendor_name
          }
          if (responseDocs.org && !orgName) {
            orgName = responseDocs.org
          }
          
          // Then check nested companyInfo
          if (responseDocs.companyInfo) {
            console.log(`📋 Found companyInfo:`, responseDocs.companyInfo)
            
            if (responseDocs.companyInfo.companyName && !vendorName) {
              vendorName = responseDocs.companyInfo.companyName
            }
            if (responseDocs.companyInfo.contactName && !orgName) {
              orgName = responseDocs.companyInfo.contactName
            }
            if (responseDocs.companyInfo.email && !vendorEmail) {
              vendorEmail = responseDocs.companyInfo.email
              console.log(`✅ Found email in companyInfo.email: ${vendorEmail}`)
            }
            if (responseDocs.companyInfo.contactEmail && !vendorEmail) {
              vendorEmail = responseDocs.companyInfo.contactEmail
              console.log(`✅ Found email in companyInfo.contactEmail: ${vendorEmail}`)
            }
          }
          
          // Try other possible fields
          if (responseDocs.email && !vendorEmail) {
            vendorEmail = responseDocs.email
            console.log(`✅ Found email in responseDocs.email: ${vendorEmail}`)
          }
          if (responseDocs.company_name && !vendorName) {
            vendorName = responseDocs.company_name
          }
          
          // Check proposalData if it exists
          if (responseDocs.proposalData && responseDocs.proposalData.companyInfo) {
            const propData = responseDocs.proposalData.companyInfo
            console.log(`📋 Found proposalData.companyInfo:`, propData)
            
            if (propData.companyName && !vendorName) {
              vendorName = propData.companyName
            }
            if (propData.contactName && !orgName) {
              orgName = propData.contactName
            }
            if (propData.email && !vendorEmail) {
              vendorEmail = propData.email
              console.log(`✅ Found email in proposalData.companyInfo.email: ${vendorEmail}`)
            }
            if (propData.contactEmail && !vendorEmail) {
              vendorEmail = propData.contactEmail
              console.log(`✅ Found email in proposalData.companyInfo.contactEmail: ${vendorEmail}`)
            }
          }
        } catch (e) {
          console.error('❌ Error parsing response_documents:', e)
        }
      }
      
      // Final validation
      if (!vendorEmail || vendorEmail === 'vendor@example.com') {
        console.warn(`⚠️ No valid email found for vendor ${proposal.response_id}`)
      }
      
      vendorMap[proposal.response_id] = {
        vendor_name: vendorName || `Vendor ${proposal.response_id}`,
        org: orgName || 'Unknown Organization',
        vendor_email: vendorEmail,
        proposed_value: proposal.proposed_value || 0,
        technical_score: proposal.technical_score || 0,
        commercial_score: proposal.commercial_score || 0,
        overall_score: proposal.overall_score || 0
      }
      
      console.log(`✅ Final vendor map for ${proposal.response_id}:`, vendorMap[proposal.response_id])
    })
    
    console.log('📋 Vendor map created:', vendorMap)
    
    // Now load consensus ranking
    const consensusResponse = await fetch(`${API_BASE_URL}/rfp/${selectedRfpId.value}/consensus-ranking/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (consensusResponse.ok) {
      const consensusData = await consensusResponse.json()
      console.log('📊 Consensus ranking data:', consensusData)
      
      if (consensusData.success && consensusData.consensus_ranking) {
        consensusRanking.value = consensusData.consensus_ranking.map((proposal, index) => {
          // Get vendor details from the map
          const vendorDetails = vendorMap[proposal.response_id] || {}
          
          return {
            ...proposal,
            vendor_name: vendorDetails.vendor_name || proposal.vendor_name || `Vendor ${index + 1}`,
            org: vendorDetails.org || proposal.org || 'Unknown Organization',
            vendor_email: vendorDetails.vendor_email || proposal.contact_email || '',
            proposed_value: vendorDetails.proposed_value || proposal.proposed_value || 0,
            technical_score: vendorDetails.technical_score || proposal.technical_score || 0,
            commercial_score: vendorDetails.commercial_score || proposal.commercial_score || 0,
            overall_score: vendorDetails.overall_score || proposal.overall_score || 0
          }
        })
        
        console.log('✅ Consensus ranking loaded with vendor details:', consensusRanking.value)
      }
    } else {
      // If no consensus ranking, create one from RFP responses
      console.log('⚠️ No consensus ranking found, creating from RFP responses')
      consensusRanking.value = rfpResponses.map((proposal, index) => {
        const vendorDetails = vendorMap[proposal.response_id] || {}
        return {
          ...proposal,
          response_id: proposal.response_id,
          vendor_name: vendorDetails.vendor_name || proposal.vendor_name || `Vendor ${index + 1}`,
          org: vendorDetails.org || proposal.org || 'Unknown Organization',
          vendor_email: vendorDetails.vendor_email || proposal.contact_email || '',
          proposed_value: vendorDetails.proposed_value || proposal.proposed_value || 0,
          technical_score: vendorDetails.technical_score || proposal.technical_score || 0,
          commercial_score: vendorDetails.commercial_score || proposal.commercial_score || 0,
          overall_score: vendorDetails.overall_score || proposal.overall_score || 0,
          consensus_score: vendorDetails.overall_score || proposal.overall_score || 0
        }
      }).sort((a, b) => (b.consensus_score || 0) - (a.consensus_score || 0))
    }
    
    // Update last updated timestamp
    lastUpdated.value = new Date().toISOString()
    
  } catch (error) {
    console.error('Error loading consensus data:', error)
  } finally {
    loading.value = false
  }
}

const loadNotifications = async () => {
  if (!selectedRfpId.value) return
  
  loadingNotifications.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/rfp/${selectedRfpId.value}/award-notification/`, {
      method: 'GET',
      headers: getAuthHeaders()
    })
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        // Enhance notifications with vendor details from consensus ranking
        notifications.value = data.notifications.map(notification => {
          // Find vendor details from consensus ranking or shortlisted proposals
          const vendorDetails = consensusRanking.value.find(v => v.response_id === notification.response_id) ||
                               shortlistedProposals.value.find(v => v.response_id === notification.response_id)
          
          return {
            ...notification,
            vendor_name: notification.vendor_name || vendorDetails?.vendor_name || 'Unknown Vendor',
            vendor_email: notification.recipient_email || notification.vendor_email || vendorDetails?.vendor_email || vendorDetails?.contact_email || '',
          }
        })
        
        console.log('📧 Loaded notifications with vendor details:', notifications.value)
      }
    } else if (response.status === 500) {
      // Handle 500 error - likely table doesn't exist yet
      console.log('Award notification table not available yet, using empty notifications')
      notifications.value = []
    }
  } catch (error) {
    console.error('Error loading notifications:', error)
    // Don't show error to user, just use empty notifications
    notifications.value = []
  } finally {
    loadingNotifications.value = false
  }
}

const sendAwardNotification = async () => {
  console.log('🚀 sendAwardNotification called')
  console.log('📋 selectedWinner.value:', selectedWinner.value)
  console.log('📋 consensusRanking.value:', consensusRanking.value)
  console.log('📋 shortlistedProposals.value:', shortlistedProposals.value)
  
  if (!selectedWinner.value) {
    PopupService.warning('Please select a vendor first', 'No Vendor Selected')
    return
  }
  
  // Get the selected vendor's details
  const selectedVendor = consensusRanking.value.find(v => v.response_id === selectedWinner.value) ||
                         shortlistedProposals.value.find(v => v.response_id === selectedWinner.value)
  
  console.log('📋 selectedVendor found:', selectedVendor)
  
  if (!selectedVendor) {
    console.error('❌ Vendor details not found for response_id:', selectedWinner.value)
    PopupService.error('Vendor details not found', 'Vendor Not Found')
    return
  }
  
  // Get email from multiple possible fields
  const vendorEmail = selectedVendor.vendor_email || 
                     selectedVendor.contact_email || 
                     selectedVendor.email || 
                     ''
  
  console.log('📧 Email extraction:', {
    vendor_email: selectedVendor.vendor_email,
    contact_email: selectedVendor.contact_email,
    email: selectedVendor.email,
    finalEmail: vendorEmail
  })
  
  // Check if vendor email is available
  if (!vendorEmail || vendorEmail === 'vendor@example.com') {
    console.error('❌ No valid vendor email found')
    console.error('❌ Available fields:', Object.keys(selectedVendor))
    PopupService.error('Vendor email not found. Please ensure the vendor has provided their contact email in the RFP response.', 'Email Not Found')
    return
  }
  
  console.log('✅ Sending award notification to:', vendorEmail)
  console.log('📧 Full vendor details:', {
    response_id: selectedWinner.value,
    vendor_email: vendorEmail,
    vendor_name: selectedVendor.vendor_name,
    org: selectedVendor.org,
    all_fields: selectedVendor
  })
  
  // Prepare the request payload
  const payload = {
    response_id: selectedWinner.value,
    vendor_email: vendorEmail,
    vendor_name: selectedVendor.vendor_name || selectedVendor.org || 'Vendor',
    notification_type: 'winner',
    award_message: awardMessage.value || 'Congratulations! Your proposal has been selected as the winner.',
    next_steps: nextSteps.value || 'Please respond to this notification within 7 days to accept or decline the award.'
  }
  
  console.log('📤 Full payload being sent to backend:', JSON.stringify(payload, null, 2))
  console.log('📤 Backend URL:', `${API_BASE_URL}/rfp/${selectedRfpId.value}/award-notification/`)
  
  sendingNotification.value = true
  try {
    console.log('🔄 Making fetch request...')
    const response = await fetch(`${API_BASE_URL}/rfp/${selectedRfpId.value}/award-notification/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(payload)
    })
    
    console.log('📥 Response status:', response.status)
    console.log('📥 Response headers:', Object.fromEntries(response.headers.entries()))
    
    const responseText = await response.text()
    console.log('📥 Raw response text:', responseText)
    
    let data
    try {
      data = JSON.parse(responseText)
      console.log('📥 Parsed response data:', data)
    } catch (e) {
      console.error('❌ Failed to parse response as JSON:', e)
      console.error('❌ Response text was:', responseText)
      PopupService.error('Server returned invalid response. Please check the console for details.', 'Invalid Response')
      return
    }
    
    if (response.ok) {
      if (data.success) {
        console.log('✅ Award notification sent successfully')
        console.log('✅ Recipient email:', data.recipient_email || vendorEmail)
        PopupService.success(`Award notification sent successfully to ${data.recipient_email || vendorEmail}`, 'Notification Sent')
        
        // Create notification
        await notificationService.createRFPAwardNotification('award_issued', {
          rfp_id: selectedRfpId.value,
          response_id: selectedWinner.value?.response_id,
          rfp_title: rfpData.value?.rfp_title,
          vendor_name: selectedWinner.value?.vendor_name,
          award_amount: selectedWinner.value?.proposed_value
        })
        
        await loadNotifications()
      } else {
        console.error('❌ Backend returned success=false:', data.error)
        PopupService.error('Failed to send notification: ' + data.error, 'Send Failed')
        
        // Create error notification
        await notificationService.createRFPErrorNotification('send_award_notification', data.error, {
          title: 'Notification Send Failed',
          rfp_id: selectedRfpId.value,
          vendor_name: selectedWinner.value?.vendor_name
        })
      }
    } else {
      console.error('❌ HTTP error:', response.status)
      console.error('❌ Error data:', data)
      
      // Extract error message from various possible formats
      let errorMessage = 'Unknown error'
      if (data.message) {
        errorMessage = data.message
      } else if (typeof data.error === 'string') {
        errorMessage = data.error
      } else if (data.error && typeof data.error === 'object') {
        errorMessage = data.error.message || JSON.stringify(data.error)
      } else if (data.error) {
        errorMessage = String(data.error)
      } else {
        errorMessage = `HTTP ${response.status}: ${response.status === 401 ? 'Authentication required' : response.status === 403 ? 'Permission denied' : 'Request failed'}`
      }
      
      PopupService.error(`Failed to send notification: ${errorMessage}`, 'HTTP Error')
      
      // Create error notification
      await notificationService.createRFPErrorNotification('send_award_notification', errorMessage, {
        title: 'HTTP Error',
        rfp_id: selectedRfpId.value
      })
    }
  } catch (error) {
    console.error('❌ Network error sending award notification:', error)
    console.error('❌ Error stack:', error.stack)
    PopupService.error('Error sending notification: ' + error.message, 'Network Error')
  } finally {
    sendingNotification.value = false
    console.log('🏁 sendAwardNotification completed')
  }
}

const sendParticipantNotifications = async () => {
  if (shortlistedProposals.value.length === 0) {
    PopupService.warning('No participants to notify', 'No Participants')
    return
  }
  
  sendingNotification.value = true
  try {
    // Send notifications to all participants except the winner
    const participants = shortlistedProposals.value.filter(p => p.response_id !== selectedWinner.value)
    let successCount = 0
    let failCount = 0
    
    console.log('📧 Sending notifications to participants:', participants.length)
    
    for (const participant of participants) {
      // Get email from multiple possible fields
      const participantEmail = participant.vendor_email || participant.contact_email || participant.email || ''
      
      // Check if participant has a valid email
      if (!participantEmail || participantEmail === 'vendor@example.com') {
        console.warn(`⚠️ No valid email found for participant ${participant.vendor_name || participant.response_id}, skipping...`)
        failCount++
        continue
      }
      
      console.log(`📧 Sending notification to ${participant.vendor_name || 'Participant'} (${participantEmail})`)
      
      const response = await fetch(`${API_BASE_URL}/rfp/${selectedRfpId.value}/award-notification/`, {
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
          console.log(`✅ Notification sent to ${participant.vendor_name} (${participantEmail})`)
        } else {
          failCount++
          console.error(`❌ Failed to send notification to ${participant.vendor_name}:`, data.error)
        }
      } else {
        failCount++
        const errorText = await response.text()
        console.error(`❌ HTTP ${response.status} - Failed to send notification to ${participant.vendor_name}:`, errorText)
      }
    }
    
    PopupService.success(`Participant notifications sent: ${successCount} successful, ${failCount} failed`, 'Notifications Sent')
    await loadNotifications()
  } catch (error) {
    console.error('❌ Error sending participant notifications:', error)
    PopupService.error('Error sending notifications: ' + error.message, 'Send Error')
  } finally {
    sendingNotification.value = false
  }
}

const createVendorCredentials = async (notificationId) => {
  console.log('🔐 Creating vendor credentials for notification:', notificationId)
 
  creatingCredentials.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/vendor-credentials/${notificationId}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      }
    })
   
    const data = await response.json()
    console.log('📥 Credential creation response:', data)
   
    if (response.ok && data.success) {
      PopupService.success(
        `Vendor credentials created and sent to ${data.data.vendor_email}`,
        'Credentials Created'
      )
     
      // Create notification
      await notificationService.createRFPAwardNotification('credentials_created', {
        rfp_id: selectedRfpId.value,
        vendor_email: data.data.vendor_email,
        user_id: data.data.user_id
      })
     
      console.log('✅ Vendor credentials created successfully:', {
        user_id: data.data.user_id,
        username: data.data.username,
        vendor_email: data.data.vendor_email
      })
    } else {
      console.error('❌ Failed to create credentials:', data.error)
      PopupService.error(data.error || 'Failed to create vendor credentials', 'Creation Failed')
     
      // Create error notification
      await notificationService.createRFPErrorNotification('create_credentials', data.error, {
        title: 'Credential Creation Failed',
        notification_id: notificationId
      })
    }
  } catch (error) {
    console.error('❌ Error creating vendor credentials:', error)
    PopupService.error('Error creating vendor credentials: ' + error.message, 'Network Error')
  } finally {
    creatingCredentials.value = false
  }
}


const selectNextVendor = (rejectedResponseId) => {
  // Find the next highest-ranked vendor that hasn't been rejected
  const availableVendors = consensusRanking.value.filter(p => 
    p.response_id !== rejectedResponseId && 
    !notifications.value.some(n => n.response_id === p.response_id && (n.notification_status === 'rejected' || n.notification_status === 'sent' || n.notification_status === 'accepted'))
  )
  
  if (availableVendors.length > 0) {
    selectedWinner.value = availableVendors[0].response_id
    PopupService.success(`Selected next vendor: ${availableVendors[0].vendor_name || 'Vendor'}`, 'Vendor Selected')
    
    // Scroll to the vendor selection area
    setTimeout(() => {
      const element = document.querySelector('.border-blue-500')
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 100)
  } else {
    PopupService.warning('No more vendors available for selection', 'No Vendors')
  }
}

const selectAndSendToNextVendor = async (rejectedResponseId) => {
  console.log('🔄 Auto-selecting and sending to next vendor...')
  
  // Find the next highest-ranked vendor that hasn't been awarded or rejected
  const availableVendors = consensusRanking.value.filter(p => 
    p.response_id !== rejectedResponseId && 
    !notifications.value.some(n => n.response_id === p.response_id && (n.notification_status === 'rejected' || n.notification_status === 'sent' || n.notification_status === 'accepted'))
  )
  
  if (availableVendors.length === 0) {
    PopupService.warning('No more vendors available for award notification', 'No Vendors')
    return
  }
  
  const nextVendor = availableVendors[0]
  
  // Check if vendor has valid email
  const vendorEmail = nextVendor.vendor_email || nextVendor.contact_email || nextVendor.email || ''
  if (!vendorEmail || vendorEmail === 'vendor@example.com') {
    PopupService.error(
      `Cannot send award to ${nextVendor.vendor_name || 'next vendor'}: No valid email address found`,
      'Email Not Found'
    )
    return
  }
  
  // Select the vendor
  selectedWinner.value = nextVendor.response_id
  
  // Show confirmation
  PopupService.info(
    `Preparing to send award notification to ${nextVendor.vendor_name || 'Vendor'} (${vendorEmail})`,
    'Sending to Next Vendor'
  )
  
  // Wait a moment for UI to update
  await new Promise(resolve => setTimeout(resolve, 500))
  
  // Automatically send the award notification
  await sendAwardNotification()
}

const generateContract = () => {
  PopupService.warning('Contract generation functionality will be implemented', 'Coming Soon')
}

const exportReport = () => {
  PopupService.warning('Report export functionality will be implemented', 'Coming Soon')
}

const goToConsensus = () => {
  router.push({
    path: '/rfp-consensus',
    query: { rfp_id: selectedRfpId.value }
  })
}

const goToDashboard = () => {
  router.push('/rfp-dashboard')
}

const refreshData = async () => {
  console.log('🔄 Manual refresh triggered...')
  await loadConsensusData()
  await loadNotifications()
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

// Real-time polling functions
const startPolling = () => {
  if (pollingInterval.value) return
  console.log('🔄 Starting real-time polling for award notifications...')
  isPolling.value = true
  pollingInterval.value = setInterval(async () => {
    if (selectedRfpId.value) {
      try {
        console.log('🔄 Polling for updates...')
        await loadConsensusData()
        await loadNotifications()
      } catch (error) {
        console.error('Error during polling:', error)
      }
    }
  }, 10000) // Poll every 10 seconds
}

const stopPolling = () => {
  if (pollingInterval.value) {
    console.log('⏹️ Stopping real-time polling...')
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
    isPolling.value = false
  }
}

// Load available RFPs on mount
onMounted(async () => {
  await loggingService.logPageView('RFP', 'Phase 9 - RFP Award')
  // Check if RFP ID is in URL query params
  const urlParams = new URLSearchParams(window.location.search)
  const rfpId = urlParams.get('rfp_id')
  
  if (rfpId) {
    console.log('🔄 RFP ID found in URL:', rfpId)
    await selectRfp(rfpId)
  } else {
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
  
  // Start polling when component mounts
  startPolling()
})

// Clean up polling when component unmounts
onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
/* Custom styles for the award page */
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
