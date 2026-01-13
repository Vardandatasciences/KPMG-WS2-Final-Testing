<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
    
    <!-- Header Section -->
    <div class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="py-6">
    <div class="md:flex md:items-center md:justify-between">
      <div class="flex-1 min-w-0">
              <h1 class="text-3xl font-bold text-gray-900 sm:text-4xl">
                Proposal Evaluation
              </h1>
              <p class="mt-2 text-lg text-gray-600">
                Select RFP proposals and assign evaluators for comprehensive assessment
        </p>
      </div>
            <div class="flex items-center gap-3 mt-4 md:mt-0">
              <a href="/rfp-url-generation" class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-all duration-200 shadow-sm">
                <Icons name="arrow-left" class="h-4 w-4 mr-2" />
                Previous
              </a>
              <button @click="navigateToMyApprovals" class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-600 to-indigo-600 border border-transparent rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all duration-200 shadow-lg">
                <Icons name="clipboard-check" class="h-4 w-4 mr-2" />
                My Approvals
              </button>
              <a href="/rfp-comparison" class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 border border-transparent rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-200 shadow-lg">
                Next
                <Icons name="arrow-right" class="h-4 w-4 ml-2" />
        </a>
      </div>
    </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Progress Steps -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
        <h3 class="text-lg font-semibold text-gray-900 mb-6">Evaluation Process</h3>
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <div :class="['w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300', 
                         selectedRFP ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg' : 'bg-gray-200 text-gray-500']">
              <Icons name="check" class="h-5 w-5" v-if="selectedRFP" />
              <span v-else>1</span>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-900">Select RFP</p>
              <p class="text-xs text-gray-500">Choose the RFP for evaluation</p>
            </div>
          </div>
          
          <div class="flex-1 h-0.5 mx-4" :class="selectedRFP ? 'bg-gradient-to-r from-blue-600 to-indigo-600' : 'bg-gray-200'"></div>
          
          <div class="flex items-center">
            <div :class="['w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300', 
                         selectedRFP && proposals.length > 0 ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg' : 'bg-gray-200 text-gray-500']">
              <Icons name="check" class="h-5 w-5" v-if="selectedRFP && proposals.length > 0" />
              <span v-else>2</span>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-900">Review Proposals</p>
              <p class="text-xs text-gray-500">View submitted proposals</p>
            </div>
          </div>
          
          <div class="flex-1 h-0.5 mx-4" :class="selectedRFP && proposals.length > 0 ? 'bg-gradient-to-r from-blue-600 to-indigo-600' : 'bg-gray-200'"></div>
          
          <div class="flex items-center">
            <div :class="['w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300', 
                         selectedProposals.length > 0 ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg' : 'bg-gray-200 text-gray-500']">
              <Icons name="check" class="h-5 w-5" v-if="selectedProposals.length > 0" />
              <span v-else>3</span>
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-900">Assign Evaluators</p>
              <p class="text-xs text-gray-500">Create evaluation workflow</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Status Banner -->
      <div v-if="selectedRFP" class="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-4 mb-8">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <Icons name="check-circle" class="h-6 w-6 text-green-500" />
            </div>
            <div class="ml-3 flex-1">
              <p class="text-sm font-medium text-green-800">
                <strong>RFP Selected:</strong> {{ selectedRFPDetails?.rfp_title }} 
              </p>
              <p v-if="proposals.length > 0" class="text-sm text-green-700 mt-1">
                <strong>{{ proposals.length }} proposals</strong> available for evaluation. Select proposals and assign evaluators.
              </p>
              <p v-else-if="!loading" class="text-sm text-yellow-700 mt-1">
                No proposals submitted yet. You can still proceed to comparison or wait for proposals.
              </p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <div v-if="selectedProposals.length > 0" class="flex items-center gap-2">
              <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                {{ selectedProposals.length }} selected
              </span>
            </div>
            <Button 
              @click="loadRFPProposals" 
              size="sm" 
              variant="outline"
              class="flex items-center"
              :disabled="loading"
            >
              <Icons name="refresh-cw" class="h-4 w-4 mr-1" />
              Refresh
            </Button>
            <Button 
              v-if="proposals.length > 0"
              @click="navigateToComparison" 
              size="sm" 
              variant="outline"
              class="flex items-center"
            >
              <Icons name="arrow-right" class="h-4 w-4 mr-1" />
              Go to Comparison
            </Button>
          </div>
        </div>
      </div>

      <!-- Proposals Section -->
      <div v-if="selectedRFP && proposals.length > 0" class="space-y-8 mb-8">
        <!-- Proposals Header with Bulk Actions -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200">
          <div class="px-6 py-4 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="text-xl font-semibold text-gray-900">Vendor Proposals</h3>
                <p class="text-sm text-gray-600 mt-1">{{ proposals.length }} proposals submitted for {{ selectedRFPDetails?.rfp_title }}</p>
              </div>
              <div class="flex items-center gap-3">
                <div class="flex items-center gap-2">
                  <input
                    type="checkbox" 
                    :checked="selectedProposals.length === proposals.length && proposals.length > 0"
                    :indeterminate="selectedProposals.length > 0 && selectedProposals.length < proposals.length"
                    @change="toggleAllProposals"
                    class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span class="text-sm font-medium text-gray-700">Select All</span>
                </div>
                <Button 
                  v-if="selectedProposals.length > 0"
                  @click="assignEvaluatorsToSelected"
                  class="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-4 py-2 rounded-lg font-medium transition-all duration-200 shadow-lg"
                >
                  <Icons name="users" class="h-4 w-4 mr-2" />
                  Assign Evaluators ({{ selectedProposals.length }})
                </Button>
              </div>
            </div>
          </div>
        </div>

        <!-- Proposals Grid -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200">
          <div class="p-6">
            <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              <div 
                v-for="proposal in proposals" 
                :key="proposal.response_id" 
                class="relative bg-white border-2 rounded-xl p-6 transition-all duration-200 hover:shadow-lg"
                :class="selectedProposals.includes(proposal.response_id) ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'"
              >
              <!-- Selection Checkbox -->
              <div class="absolute top-4 right-4">
                <input
                  type="checkbox" 
                  :checked="selectedProposals.includes(proposal.response_id)"
                  @change="toggleProposalSelection(proposal.response_id)"
                  class="h-5 w-5 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
              </div>

              <!-- Proposal Header -->
              <div class="pr-8">
                <div class="flex items-start justify-between mb-4">
                  <div class="flex-1">
                    <h4 class="text-lg font-semibold text-gray-900 mb-1">{{ proposal.vendor_name || 'Unknown Vendor' }}</h4>
                    <p class="text-sm text-gray-600 font-medium">
                      {{ proposal.organization_name || proposal.company_name || proposal.org || 'No organization specified' }}
                    </p>
                  </div>
                  <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                        :class="getStatusBadgeClass(proposal.evaluation_status)">
                    {{ proposal.evaluation_status }}
                  </span>
                </div>
                
                <!-- Proposal Details -->
                <div class="space-y-3">
                  <div class="flex items-center text-sm text-gray-600">
                    <Icons name="calendar" class="h-4 w-4 mr-2" />
                    Submitted: {{ formatDate(proposal.submitted_at) }}
                  </div>
                  <div v-if="proposal.proposed_value" class="flex items-center text-sm text-gray-600">
                    <Icons name="dollar-sign" class="h-4 w-4 mr-2" />
                    Value: ${{ proposal.proposed_value.toLocaleString() }}
                  </div>
                  <div v-if="proposal.contact_email" class="flex items-center text-sm text-gray-600">
                    <Icons name="mail" class="h-4 w-4 mr-2" />
                    {{ proposal.contact_email }}
                  </div>
                </div>
                
                <!-- Action Buttons -->
                <div class="flex items-center gap-2 mt-6">
                  <Button 
                    size="sm" 
                    variant="outline" 
                    @click="viewProposal(proposal)"
                    class="flex-1"
                  >
                    <Icons name="eye" class="h-4 w-4 mr-1" />
                    View
                  </Button>
                  <Button 
                    size="sm" 
                    @click="assignEvaluator(proposal)"
                    class="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white"
                  >
                    <Icons name="user-plus" class="h-4 w-4 mr-1" />
                    Assign
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-16 mb-8">
        <div class="text-center">
          <div class="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mx-auto mb-6"></div>
          <h3 class="text-lg font-semibold text-gray-900 mb-2">Loading proposals...</h3>
          <p class="text-sm text-gray-600">Please wait while we fetch the data.</p>
        </div>
      </div>

      <!-- No Proposals Message -->
      <div v-if="selectedRFP && proposals.length === 0 && !loading" class="text-center py-16 mb-8">
        <div class="max-w-md mx-auto">
          <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Icons name="inbox" class="h-10 w-10 text-gray-400" />
          </div>
          <h3 class="text-xl font-semibold text-gray-900 mb-2">No proposals found</h3>
          <p class="text-gray-600 mb-6">No proposals were found for this RFP. This could mean:</p>
          <ul class="text-sm text-gray-500 text-left mb-6 space-y-1">
            <li>• No vendors have submitted proposals yet</li>
            <li>• Proposals exist but have different submission statuses</li>
            <li>• There might be a data issue</li>
          </ul>
          <div class="flex flex-col sm:flex-row gap-3 justify-center">
            <Button @click="loadRFPProposals" variant="outline" class="flex items-center">
              <Icons name="refresh-cw" class="h-4 w-4 mr-2" />
              Refresh Proposals
            </Button>
            <Button @click="onRFPSelectionChange" variant="outline" class="flex items-center">
              <Icons name="arrow-left" class="h-4 w-4 mr-2" />
              Select Different RFP
            </Button>
          </div>
          <div class="mt-4 text-xs text-gray-400">
            Check the browser console for detailed debug information
          </div>
        </div>
      </div>

      <!-- RFP Selection -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-200 mb-8">
        <div class="px-6 py-4 border-b border-gray-200">
          <h3 class="text-xl font-semibold text-gray-900">Select RFP for Evaluation</h3>
          <p class="mt-1 text-sm text-gray-600">Choose the RFP you want to evaluate proposals for</p>
        </div>
        <div class="p-6">
          <div class="space-y-6">
            <!-- RFP Selection Controls - Unified Card Grid -->
            <div class="space-y-4">
              <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <div class="flex items-center gap-3">
                  <label class="text-sm font-semibold text-gray-700 whitespace-nowrap">RFP Selection Type:</label>
                  <div class="flex gap-2">
                    <label class="relative flex items-center px-4 py-2.5 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:bg-blue-50" 
                           :class="rfpSelectionType === 'user' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'">
                      <input 
                        type="radio" 
                        v-model="rfpSelectionType" 
                        value="user" 
                        class="sr-only"
                        @change="onRFPSelectionTypeChange"
                      />
                      <div class="flex items-center">
                        <div class="w-4 h-4 border-2 rounded-full mr-2 flex items-center justify-center"
                             :class="rfpSelectionType === 'user' ? 'border-blue-500' : 'border-gray-300'">
                          <div v-if="rfpSelectionType === 'user'" class="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                        </div>
                        <span class="text-sm font-medium text-gray-900">My RFPs</span>
                      </div>
                    </label>
                    
                    <label class="relative flex items-center px-4 py-2.5 border-2 rounded-lg cursor-pointer transition-all duration-200 hover:bg-blue-50"
                           :class="rfpSelectionType === 'all' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'">
                      <input 
                        type="radio" 
                        v-model="rfpSelectionType" 
                        value="all" 
                        class="sr-only"
                        @change="onRFPSelectionTypeChange"
                      />
                      <div class="flex items-center">
                        <div class="w-4 h-4 border-2 rounded-full mr-2 flex items-center justify-center"
                             :class="rfpSelectionType === 'all' ? 'border-blue-500' : 'border-gray-300'">
                          <div v-if="rfpSelectionType === 'all'" class="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
                        </div>
                        <span class="text-sm font-medium text-gray-900">All RFPs</span>
                      </div>
                    </label>
                  </div>
                </div>
                
                <div class="text-sm text-gray-600">
                  <span class="inline-flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-green-500"></span>
                    {{ availableRFPs.length }} RFPs Available
                  </span>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    @click="rfpViewMode = 'grid'"
                    :class="rfpViewMode === 'grid' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-white text-gray-700 border-gray-200'"
                    class="px-3 py-1.5 text-sm font-medium border rounded-lg hover:bg-blue-50 transition"
                  >
                    Grid
                  </button>
                  <button
                    @click="rfpViewMode = 'list'"
                    :class="rfpViewMode === 'list' ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-white text-gray-700 border-gray-200'"
                    class="px-3 py-1.5 text-sm font-medium border rounded-lg hover:bg-blue-50 transition"
                  >
                    List
                  </button>
                </div>
              </div>

              <div v-if="loading" class="flex items-center gap-2 text-sm text-gray-500">
                <Icons name="loader" class="h-4 w-4 animate-spin" />
                Loading RFPs...
              </div>
              <div v-else-if="availableRFPs.length === 0" class="text-sm text-gray-500">
                No RFPs found for the selected type.
              </div>
              <div v-else>
                <div v-if="rfpViewMode === 'grid'" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  <button
                    v-for="rfp in availableRFPs"
                    :key="rfp.rfp_id"
                    type="button"
                    @click="selectRfpCard(rfp)"
                    class="group w-full text-left bg-white border rounded-xl p-5 shadow-sm transition-all duration-200 hover:border-blue-400 hover:shadow-md focus:ring-2 focus:ring-blue-500"
                    :class="selectedRFP === rfp.rfp_id ? 'border-blue-500 shadow-md' : 'border-gray-200'"
                  >
                    <div class="flex items-start justify-between mb-3">
                      <div class="pr-6">
                        <h4 class="text-base font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
                          {{ rfp.rfp_title || rfp.title || 'Untitled RFP' }}
                        </h4>
                        <p class="text-sm text-gray-600 mt-1 line-clamp-2">
                          {{ rfp.description || 'No description available.' }}
                        </p>
                      </div>
                      <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-800 border border-blue-100">
                        {{ rfp.rfp_number || rfp.number || 'N/A' }}
                      </span>
                    </div>

                    <div class="flex items-center justify-between text-xs text-gray-500">
                      <span class="inline-flex items-center px-2 py-1 rounded-full font-medium"
                            :class="getStatusBadgeClass(rfp.status)">
                        {{ rfp.status || 'N/A' }}
                      </span>
                      <span class="flex items-center gap-1">
                        <Icons name="calendar" class="h-4 w-4" />
                        {{ formatDate(rfp.submission_deadline) }}
                      </span>
                    </div>
                  </button>
                </div>

                <div v-else class="space-y-3">
                  <button
                    v-for="rfp in availableRFPs"
                    :key="rfp.rfp_id"
                    type="button"
                    @click="selectRfpCard(rfp)"
                    class="group w-full text-left bg-white border rounded-lg p-4 shadow-sm transition-all duration-200 hover:border-blue-400 hover:shadow-md focus:ring-2 focus:ring-blue-500 flex items-center justify-between"
                    :class="selectedRFP === rfp.rfp_id ? 'border-blue-500 shadow-md' : 'border-gray-200'"
                  >
                    <div class="flex-1 pr-4">
                      <h4 class="text-base font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">
                        {{ rfp.rfp_title || rfp.title || 'Untitled RFP' }}
                      </h4>
                      <p class="text-sm text-gray-600 mt-1 line-clamp-1">
                        {{ rfp.description || 'No description available.' }}
                      </p>
                      <div class="flex items-center gap-3 mt-2 text-xs text-gray-500">
                        <span class="inline-flex items-center px-2 py-1 rounded-full font-medium"
                              :class="getStatusBadgeClass(rfp.status)">
                          {{ rfp.status || 'N/A' }}
                        </span>
                        <span class="flex items-center gap-1">
                          <Icons name="calendar" class="h-4 w-4" />
                          {{ formatDate(rfp.submission_deadline) }}
                        </span>
                      </div>
                    </div>
                    <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-800 border border-blue-100">
                      {{ rfp.rfp_number || rfp.number || 'N/A' }}
                    </span>
                  </button>
                </div>
              </div>
            </div>

            <!-- RFP Details Card -->
            <div v-if="selectedRFPDetails" class="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <h4 class="text-lg font-semibold text-gray-900 mb-2">{{ selectedRFPDetails.rfp_title }}</h4>
                  <p class="text-sm text-gray-600 mb-4">{{ selectedRFPDetails.description }}</p>
                  <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="bg-white rounded-lg p-3 shadow-sm">
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Type</p>
                      <p class="text-sm font-semibold text-gray-900">{{ selectedRFPDetails.rfp_type }}</p>
                    </div>
                    <div class="bg-white rounded-lg p-3 shadow-sm">
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Status</p>
                      <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                            :class="getStatusBadgeClass(selectedRFPDetails.status)">
                        {{ selectedRFPDetails.status }}
                      </span>
                    </div>
                    <div class="bg-white rounded-lg p-3 shadow-sm">
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Deadline</p>
                      <p class="text-sm font-semibold text-gray-900">{{ formatDate(selectedRFPDetails.submission_deadline) }}</p>
                    </div>
                    <div class="bg-white rounded-lg p-3 shadow-sm" v-if="selectedRFPDetails.estimated_value">
                      <p class="text-xs font-medium text-gray-500 uppercase tracking-wide">Value</p>
                      <p class="text-sm font-semibold text-gray-900">${{ selectedRFPDetails.estimated_value.toLocaleString() }}</p>
                    </div>
                  </div>
                </div>
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotifications } from '@/composables/useNotifications'
import { useRfpApi } from '@/composables/useRfpApi'
import loggingService from '@/services/loggingService'
import Card from '@/components_rfp/Card.vue'
import Button from '@/components_rfp/Button.vue'
import Badge from '@/components_rfp/ui/Badge.vue'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import Icons from '@/components_rfp/ui/Icons.vue'

// API base URL
import { getTprmApiV1BaseUrl } from '@/utils/backendEnv'
const API_BASE_URL = getTprmApiV1BaseUrl()

// Router
const router = useRouter()

// Reactive data
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

const rfpSelectionType = ref('user')
const selectedRFP = ref('')
const rfpViewMode = ref<'grid' | 'list'>('grid')
const availableRFPs = ref([])
const selectedRFPDetails = ref(null)
const proposals = ref([])
const loading = ref(false)
const selectedProposals = ref([])

// Methods
const onRFPSelectionTypeChange = async () => {
  selectedRFP.value = ''
  proposals.value = []
  selectedRFPDetails.value = null
  
  if (rfpSelectionType.value === 'user') {
    await loadUserRFPs()
  } else if (rfpSelectionType.value === 'all') {
    await loadAllRFPs()
  }
}

const onRFPSelectionChange = async () => {
  selectedProposals.value = []
  
  if (selectedRFP.value) {
    try {
      await loadRFPProposals()
      console.log('✅ Proposals loaded. Users can now assign evaluators or proceed to comparison.')
    } catch (error) {
      console.error('Error loading proposals:', error)
      PopupService.error('Failed to load proposals. Please try again.', 'Loading Failed')
    }
    
    // Store RFP data in localStorage for potential use in comparison page later
    // But don't redirect automatically - let users assign evaluators first
    if (selectedRFPDetails.value) {
      const rfpData = {
        rfp_id: selectedRFP.value,
        rfp_title: selectedRFPDetails.value?.rfp_title,
        rfp_number: selectedRFPDetails.value?.rfp_number,
        description: selectedRFPDetails.value?.description,
        rfp_type: selectedRFPDetails.value?.rfp_type,
        status: selectedRFPDetails.value?.status,
        proposal_count: proposals.value?.length || 0
      }
      localStorage.setItem('selected_rfp_for_comparison', JSON.stringify(rfpData))
      localStorage.setItem('selected_rfp_proposals', JSON.stringify(proposals.value || []))
      console.log('📋 RFP data stored for later use:', rfpData)
    }
  } else {
    proposals.value = []
    selectedRFPDetails.value = null
  }
}

const loadUserRFPs = async () => {
  loading.value = true
  try {
    const { fetchRFPs } = useRfpApi()
    const currentUserId = getCurrentUserId()
    
    // Use authenticated API with filters
    const data = await fetchRFPs({ 
      created_by: currentUserId, 
      status: 'EVALUATION' 
    })
    
    availableRFPs.value = data.results || data
    
  } catch (error) {
    console.error('Error loading user RFPs:', error)
    availableRFPs.value = []
    PopupService.error('Failed to load your RFPs. Please try again.', 'Loading Failed')
  } finally {
    loading.value = false
  }
}

const loadAllRFPs = async () => {
  loading.value = true
  try {
    const { fetchRFPs } = useRfpApi()
    
    // Use authenticated API with status filter
    const data = await fetchRFPs({ status: 'EVALUATION' })
    
    availableRFPs.value = data.results || data
    
  } catch (error) {
    console.error('Error loading all RFPs:', error)
    availableRFPs.value = []
    PopupService.error('Failed to load RFPs. Please try again.', 'Loading Failed')
  } finally {
    loading.value = false
  }
}

const loadRFPProposals = async () => {
  if (!selectedRFP.value) {
    proposals.value = []
    selectedRFPDetails.value = null
    return
  }

  loading.value = true
  try {
    const { fetchRFP, getAuthHeaders } = useRfpApi()
    
    // Load RFP details with authentication
    const rfpData = await fetchRFP(selectedRFP.value)
    selectedRFPDetails.value = rfpData

    // Load all proposals for this RFP with authentication
    const proposalsResponse = await fetch(`${API_BASE_URL}/rfp-responses-list/?rfp_id=${selectedRFP.value}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    if (!proposalsResponse.ok) {
      throw new Error(`HTTP error! status: ${proposalsResponse.status}`)
    }
    const proposalsData = await proposalsResponse.json()
    
    // Ensure we get all proposals - handle both response formats
    let rawProposals = []
    if (proposalsData.success && proposalsData.responses) {
      rawProposals = proposalsData.responses
      console.log(`Loaded ${proposalsData.responses.length} proposals for RFP ${selectedRFP.value}`)
      
      // Log debug information if available
      if (proposalsData.debug_info) {
        console.log('Debug info from API:', proposalsData.debug_info)
        console.log(`Total responses found: ${proposalsData.debug_info.total_responses_found}`)
        console.log(`Submitted responses: ${proposalsData.debug_info.submitted_responses}`)
        console.log(`Responses returned: ${proposalsData.debug_info.responses_returned}`)
      }
    } else if (Array.isArray(proposalsData)) {
      rawProposals = proposalsData
      console.log(`Loaded ${proposalsData.length} proposals for RFP ${selectedRFP.value}`)
    } else {
      rawProposals = []
      console.warn('No proposals found or unexpected response format:', proposalsData)
    }
    
    // Process proposals to extract organization name from multiple sources
    proposals.value = rawProposals.map(proposal => {
      // Extract organization name from multiple possible sources
      let orgName = proposal.org
        || proposal.organization_name
        || proposal.company_name
      
      // If not found in direct fields, check response_documents
      if (!orgName && proposal.response_documents) {
        let responseDocs = proposal.response_documents
        // Handle case where response_documents might be a string
        if (typeof responseDocs === 'string') {
          try {
            responseDocs = JSON.parse(responseDocs)
          } catch (e) {
            console.warn('Could not parse response_documents:', e)
            responseDocs = {}
          }
        }
        
        if (responseDocs && typeof responseDocs === 'object') {
          orgName = responseDocs.organization_name
            || responseDocs.company_name
            || responseDocs.org
            || responseDocs.vendor?.organization_name
            || responseDocs.vendor?.company_name
            || responseDocs.vendor?.org
            || responseDocs.company?.name
            || responseDocs.organization?.name
        }
      }
      
      // Return proposal with extracted organization name
      return {
        ...proposal,
        org: orgName || proposal.org || 'No organization specified',
        organization_name: orgName || proposal.organization_name,
        company_name: orgName || proposal.company_name
      }
    })
    
    // Log proposal details for debugging
    if (proposals.value.length > 0) {
      console.log('Proposals loaded with organization names:', proposals.value.map(p => ({
        response_id: p.response_id,
        vendor_name: p.vendor_name,
        org: p.org,
        organization_name: p.organization_name,
        submission_status: p.submission_status,
        evaluation_status: p.evaluation_status,
        submitted_at: p.submitted_at
      })))
    } else {
      console.warn('No proposals loaded - this might indicate an issue with the API or data')
    }
    
  } catch (error) {
    console.error('Error loading RFP proposals:', error)
    proposals.value = []
    selectedRFPDetails.value = null
    PopupService.error(`Failed to load RFP proposals: ${error.message}. Please try again.`, 'Loading Failed')
  } finally {
    loading.value = false
  }
}

const toggleProposalSelection = (proposalId) => {
  const index = selectedProposals.value.indexOf(proposalId)
  if (index > -1) {
    selectedProposals.value.splice(index, 1)
  } else {
    selectedProposals.value.push(proposalId)
  }
}

const toggleAllProposals = () => {
  if (selectedProposals.value.length === proposals.value.length) {
    selectedProposals.value = []
  } else {
    selectedProposals.value = proposals.value.map(p => p.response_id)
  }
}

const assignEvaluatorsToSelected = async () => {
  if (selectedProposals.value.length === 0) {
    PopupService.warning('Please select at least one proposal.', 'No Proposals Selected')
    return
  }
  
  try {
    // Get the actual proposal objects
    const selectedProposalObjects = proposals.value.filter(p => 
      selectedProposals.value.includes(p.response_id)
    )
    
    // Prepare RFP data for the workflow creator
    const rfpData = {
      rfp_id: selectedRFP.value,
      rfp_title: selectedRFPDetails.value?.rfp_title,
      rfp_number: selectedRFPDetails.value?.rfp_number,
      description: selectedRFPDetails.value?.description,
      rfp_type: selectedRFPDetails.value?.rfp_type,
      status: selectedRFPDetails.value?.status,
      // Add proposal information for bulk evaluation
      selected_proposals: selectedProposalObjects,
      proposal_count: selectedProposalObjects.length,
      workflow_type: 'bulk_proposal_evaluation'
    }
    
    // Store data for the ApprovalWorkflowCreator
    localStorage.setItem('rfp_for_approval_workflow', JSON.stringify(rfpData))
    localStorage.setItem('selected_proposals_for_evaluation', JSON.stringify(selectedProposalObjects))
    localStorage.setItem('workflowType', 'bulk_proposal_evaluation')
    localStorage.setItem('current_rfp_id', selectedRFP.value)
    
    // Navigate to ApprovalWorkflowCreator for bulk proposal evaluation
    router.push('/approval-workflow-creator?type=bulk_proposal_evaluation')
    
  } catch (error) {
    console.error('Error preparing bulk assignment:', error)
    PopupService.error('Failed to prepare bulk assignment. Please try again.', 'Assignment Failed')
  }
}

const assignEvaluator = async (proposal) => {
  if (!selectedRFP.value) {
    PopupService.warning('Please select an RFP first.', 'No RFP Selected')
    return
  }
  
  try {
    const { getAuthHeaders } = useRfpApi()
    
    // Use the correct endpoint to fetch proposal details with authentication
    const response = await fetch(`${API_BASE_URL}/rfp-responses-detail/${proposal.response_id}/`, {
      method: 'GET',
      headers: getAuthHeaders(),
    })
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const responseData = await response.json()
    const proposalData = responseData.data || responseData
    
    const rfpData = {
      rfp_id: selectedRFP.value,
      rfp_title: selectedRFPDetails.value?.rfp_title,
      rfp_number: selectedRFPDetails.value?.rfp_number,
      description: selectedRFPDetails.value?.description,
      rfp_type: selectedRFPDetails.value?.rfp_type,
      status: selectedRFPDetails.value?.status
    }
    
    // Store data for approval workflow creator
    localStorage.setItem('rfp_for_approval_workflow', JSON.stringify(rfpData))
    localStorage.setItem('proposal_for_evaluation', JSON.stringify(proposalData))
    localStorage.setItem('workflowType', 'proposal_evaluation')
    localStorage.setItem('current_rfp_id', selectedRFP.value)
    localStorage.setItem('current_proposal_id', proposal.response_id)
    
    // Navigate to ApprovalWorkflowCreator for proposal evaluation
    router.push('/approval-workflow-creator?type=proposal_evaluation')
    
  } catch (error) {
    console.error('Error fetching proposal data:', error)
    PopupService.error('Failed to fetch proposal data. Please try again.', 'Fetch Failed')
  }
}

const selectRfpCard = async (rfp) => {
  if (!rfp || loading.value) return
  selectedRFP.value = rfp.rfp_id
  selectedRFPDetails.value = rfp
  await onRFPSelectionChange()
}

const navigateToMyApprovals = () => {
  router.push('/my-approvals')
}

const navigateToComparison = () => {
  if (selectedRFP.value) {
    router.push({
      path: '/rfp-comparison',
      query: { rfp_id: selectedRFP.value }
    }).catch(err => {
      console.error('Navigation error:', err)
      window.location.href = `/rfp-comparison?rfp_id=${selectedRFP.value}`
    })
  } else {
    PopupService.warning('Please select an RFP first.', 'No RFP Selected')
  }
}

const viewProposal = (proposal) => {
  console.log('Viewing proposal:', proposal)
  // Navigate to ProposalEvaluation with the proposal data
  router.push(`/proposal-evaluation?response_id=${proposal.response_id}`)
}

// Initialize component
onMounted(async () => {
  await loggingService.logPageView('RFP', 'Phase 6 - RFP Evaluation')
  // Get URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  const response_id = urlParams.get('response_id');
  const fromApprovals = urlParams.get('fromApprovals') === 'true';
  
  if (fromApprovals && response_id) {
    try {
      const { getAuthHeaders } = useRfpApi()
      
      // Fetch the proposal data directly using response_id with authentication
      const response = await fetch(`${API_BASE_URL}/users/rfp_responses/${response_id}/`, {
        method: 'GET',
        headers: getAuthHeaders(),
      });
      if (!response.ok) {
        throw new Error('Failed to fetch proposal data');
      }
      const proposalData = await response.json();
      
      // Set up direct evaluation
      selectedRFP.value = proposalData.rfp_id;
      selectedRFPDetails.value = {
        rfp_id: proposalData.rfp_id,
        rfp_title: proposalData.rfp_title || 'RFP Evaluation',
        rfp_number: proposalData.rfp_number,
        description: proposalData.description
      };
      
      // Set the proposal for evaluation
      proposals.value = [proposalData];
      
      
    } catch (error) {
      console.error('Error loading proposal for evaluation:', error);
      PopupService.error('Failed to load proposal data. Returning to approvals.', 'Loading Failed');
      window.location.href = '/my-approvals';
    }
  } else {
    // Regular flow - load initial data
    if (rfpSelectionType.value === 'user') {
      loadUserRFPs();
    } else {
      loadAllRFPs();
    }
  }
});

// Helper functions
const getCurrentUserId = () => {
  return 1 // Replace with actual user ID from your auth system
}

const getStatusBadgeClass = (status) => {
  const key = (status || '').toString().toUpperCase()
  const map = {
    APPROVED: 'bg-green-100 text-green-800',
    ACTIVE: 'bg-green-100 text-green-800',
    IN_REVIEW: 'bg-yellow-100 text-yellow-800',
    PENDING: 'bg-yellow-100 text-yellow-800',
    DRAFT: 'bg-gray-100 text-gray-800',
    EVALUATION: 'bg-blue-100 text-blue-800',
    SUBMITTED: 'bg-blue-100 text-blue-800',
    UNDER_EVALUATION: 'bg-yellow-100 text-yellow-800',
    SHORTLISTED: 'bg-green-100 text-green-800',
    AWARDED: 'bg-green-100 text-green-800',
    CLOSED: 'bg-gray-100 text-gray-800'
  }
  return map[key] || 'bg-gray-100 text-gray-800'
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString()
}
</script>

<style scoped>
/* Additional evaluation-specific styles can be added here */
</style>
