<template>
  <div class="space-y-6">
    <div class="md:flex md:items-center md:justify-between">
      <div class="flex-1 min-w-0">
        <h2 class="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
          Draft Manager
        </h2>
        <p class="mt-1 text-sm text-gray-500">
          Manage your RFP drafts and versions
        </p>
      </div>
      <div class="mt-4 flex md:mt-0 md:ml-4">
        <Button variant="outline" class="mr-3">
          Import Draft
        </Button>
        <Button @click="createNewDraft">
          Create New Draft
        </Button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="bg-white shadow overflow-hidden sm:rounded-md p-8 text-center">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      <p class="mt-2 text-sm text-gray-600">Loading drafts...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!isLoading && drafts.length === 0" class="bg-white shadow overflow-hidden sm:rounded-md p-8 text-center">
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No drafts found</h3>
      <p class="mt-1 text-sm text-gray-500">Get started by creating a new RFP draft.</p>
      <div class="mt-6">
        <Button @click="$router.push('/phase1-creation')">
          Create New RFP
        </Button>
      </div>
    </div>

    <!-- Draft List -->
    <div v-else class="bg-white shadow overflow-hidden sm:rounded-md">
      <ul class="divide-y divide-gray-200">
        <li v-for="draft in drafts" :key="draft.id">
          <div class="px-4 py-4 flex items-center justify-between hover:bg-gray-50">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <div :class="[
                  'h-10 w-10 rounded-lg flex items-center justify-center',
                  draft.isLocal ? 'bg-green-100' : 'bg-blue-100'
                ]">
                  <svg class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
              </div>
              <div class="ml-4">
                <div class="flex items-center">
                  <p class="text-sm font-medium text-gray-900">{{ draft.title }}</p>
                  <span :class="[
                    'ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                    draft.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                    draft.status === 'review' ? 'bg-blue-100 text-blue-800' :
                    'bg-green-100 text-green-800'
                  ]">
                    {{ draft.isLocal ? 'Local Draft' : draft.status }}
                  </span>
                  <span v-if="draft.isLocal" class="ml-1 inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Auto-saved
                  </span>
                </div>
                <p class="text-sm text-gray-500">{{ draft.description }}</p>
                <div class="mt-1 flex items-center text-xs text-gray-400">
                  <span>Last modified: {{ draft.lastModified }}</span>
                  <span class="mx-2">•</span>
                  <span>Version {{ draft.version }}</span>
                  <span v-if="draft.isLocal" class="mx-2">•</span>
                  <span v-if="draft.isLocal" class="text-green-600">Local Storage</span>
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-2">
              <Button size="sm" variant="outline" @click="viewDraft(draft)">
                View
              </Button>
              <Button size="sm" variant="outline" @click="editDraft(draft)">
                {{ draft.isLocal ? 'Continue' : 'Edit' }}
              </Button>
              <Button size="sm" @click="publishDraft(draft)">
                {{ draft.isLocal ? 'Complete & Save' : 'Move to Review' }}
              </Button>
              <Button size="sm" variant="outline" @click="deleteDraft(draft)" class="text-red-600 hover:text-red-700">
                Delete
              </Button>
            </div>
          </div>
        </li>
      </ul>
    </div>

    <!-- Draft Details Modal -->
    <div v-if="selectedDraft" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div class="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
        <div class="mt-3">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-medium text-gray-900">{{ selectedDraft.title }}</h3>
            <button @click="selectedDraft = null" class="text-gray-400 hover:text-gray-600">
              <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Description</label>
              <p class="mt-1 text-sm text-gray-900">{{ selectedDraft.description }}</p>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Status</label>
                <p class="mt-1 text-sm text-gray-900 capitalize">{{ selectedDraft.status }}</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Version</label>
                <p class="mt-1 text-sm text-gray-900">{{ selectedDraft.version }}</p>
              </div>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700">Last Modified</label>
              <p class="mt-1 text-sm text-gray-900">{{ selectedDraft.lastModified }}</p>
            </div>
            
            <div v-if="selectedDraft.isLocal">
              <label class="block text-sm font-medium text-gray-700">Storage Type</label>
              <p class="mt-1 text-sm text-green-600">Local Storage (Auto-saved)</p>
            </div>
            
            <div v-if="selectedDraft.content && selectedDraft.isLocal">
              <label class="block text-sm font-medium text-gray-700">Progress</label>
              <div class="mt-1 text-sm text-gray-900">
                <div v-if="selectedDraft.content.rfpNumber">✓ RFP Number: {{ selectedDraft.content.rfpNumber }}</div>
                <div v-if="selectedDraft.content.type">✓ Type: {{ selectedDraft.content.type }}</div>
                <div v-if="selectedDraft.content.estimatedValue">✓ Budget: {{ selectedDraft.content.currency }} {{ selectedDraft.content.estimatedValue }}</div>
                <div v-if="selectedDraft.content.criteria && selectedDraft.content.criteria.length > 0">
                  ✓ Evaluation Criteria: {{ selectedDraft.content.criteria.length }} criteria
                </div>
              </div>
            </div>
            
            <div v-if="selectedDraft.content && !selectedDraft.isLocal">
              <label class="block text-sm font-medium text-gray-700">Details</label>
              <div class="mt-1 text-sm text-gray-900 space-y-1">
                <div v-if="selectedDraft.content.rfp_type">✓ Type: {{ selectedDraft.content.rfp_type }}</div>
                <div v-if="selectedDraft.content.category">✓ Category: {{ selectedDraft.content.category }}</div>
                <div v-if="selectedDraft.content.estimated_value">
                  ✓ Budget: {{ selectedDraft.content.currency }} {{ selectedDraft.content.estimated_value }}
                </div>
                <div v-if="selectedDraft.content.evaluation_criteria && selectedDraft.content.evaluation_criteria.length > 0">
                  ✓ Evaluation Criteria: {{ selectedDraft.content.evaluation_criteria.length }} criteria
                </div>
                <div v-if="selectedDraft.content.documents && selectedDraft.content.documents.length > 0" class="text-blue-600">
                  📎 Documents: {{ selectedDraft.content.documents.length }} files attached
                </div>
              </div>
            </div>
          </div>
          
          <div class="mt-6 flex justify-end space-x-3">
            <Button variant="outline" @click="selectedDraft = null">Close</Button>
            <Button variant="outline" @click="editDraft(selectedDraft)">
              {{ selectedDraft.isLocal ? 'Continue' : 'Edit' }}
            </Button>
            <Button @click="publishDraft(selectedDraft)">
              {{ selectedDraft.isLocal ? 'Complete & Save' : 'Move to Review' }}
            </Button>
            <Button variant="outline" @click="deleteDraft(selectedDraft)" class="text-red-600 hover:text-red-700">
              Delete
            </Button>
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
import axios from 'axios'
import Button from '@/components_rfp/Button.vue'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import loggingService from '@/services/loggingService'
import { rfpUseToast } from '@/composables/rfpUseToast.js'
import { useRfpApi } from '@/composables/useRfpApi'
import { getTprmApiUrl } from '@/utils/backendEnv'

const API_BASE_URL = getTprmApiUrl('rfp')
const { success, error } = rfpUseToast()
const router = useRouter()
const { getAuthHeaders } = useRfpApi()

const selectedDraft = ref(null)
const drafts = ref([])
const isLoading = ref(false)

// Load drafts from database
const loadServerDrafts = async () => {
  try {
    isLoading.value = true
    console.log('📥 Fetching draft RFPs from database...')
    
    // Fetch RFPs with DRAFT status from the database
    const response = await axios.get(`${API_BASE_URL}/rfps/`, {
      params: {
        status: 'DRAFT'
      },
      headers: getAuthHeaders()
    })
    
    console.log('✅ Received draft RFPs:', response.data)
    
    // Transform database drafts to match component format
    const serverDrafts = (response.data.results || response.data || []).map(rfp => {
      // Log each draft to debug data completeness
      console.log(`📄 Draft ${rfp.rfp_id}:`, {
        has_description: !!rfp.description,
        has_type: !!rfp.rfp_type,
        has_budget: !!rfp.estimated_value,
        has_dates: !!rfp.issue_date,
        has_criteria: !!(rfp.evaluation_criteria && rfp.evaluation_criteria.length > 0)
      })
      
      return {
        id: rfp.rfp_id || rfp.id,
        title: rfp.rfp_title || rfp.title || 'Untitled RFP',
        description: rfp.description || 'No description provided',
        status: rfp.status?.toLowerCase() || 'draft',
        version: rfp.version_number?.toString() || '1.0',
        lastModified: rfp.updated_at 
          ? new Date(rfp.updated_at).toLocaleString() 
          : new Date(rfp.created_at).toLocaleString(),
        content: rfp, // Store complete RFP data including evaluation_criteria
        isLocal: false,
        rfpNumber: rfp.rfp_number,
        estimatedValue: rfp.estimated_value,
        currency: rfp.currency,
        createdAt: rfp.created_at
      }
    })
    
    console.log(`✅ Loaded ${serverDrafts.length} draft RFPs from database`)
    
    // Replace mock data with real drafts
    drafts.value = serverDrafts
    
  } catch (err) {
    console.error('❌ Error loading server drafts:', err)
    if (err.response) {
      console.error('Error response:', err.response.data)
    }
    error('Load Error', 'Failed to load drafts from server. Showing local drafts only.')
    drafts.value = [] // Clear mock data even on error
  } finally {
    isLoading.value = false
  }
}

// Load local drafts from localStorage
const loadLocalDrafts = () => {
  try {
    const currentDraft = localStorage.getItem('rfp_draft_current')
    if (currentDraft) {
      const draftData = JSON.parse(currentDraft)
      
      // Check if there's meaningful content
      const hasContent = draftData.title?.trim() || 
                        draftData.description?.trim() || 
                        draftData.rfpNumber?.trim()
      
      if (hasContent) {
        // Add local draft to the beginning of the list
        const localDraft = {
          id: 'local-current',
          title: draftData.title || 'Untitled RFP Draft',
          description: draftData.description || 'Auto-saved local draft',
          status: 'draft',
          version: draftData.version || '1.0',
          lastModified: draftData.lastSaved ? new Date(draftData.lastSaved).toLocaleString() : 'Just now',
          content: draftData,
          isLocal: true,
          rfpNumber: draftData.rfpNumber,
          estimatedValue: draftData.estimatedValue,
          currency: draftData.currency
        }
        
        // Remove any existing local draft
        drafts.value = drafts.value.filter(d => d.id !== 'local-current')
        // Add to beginning
        drafts.value.unshift(localDraft)
      }
    }
  } catch (error) {
    console.error('Error loading local drafts:', error)
  }
}

const viewDraft = (draft: any) => {
  selectedDraft.value = draft
}

const createNewDraft = () => {
  // Clear any stale draft IDs to ensure we create a new RFP
  localStorage.removeItem('current_rfp_id')
  localStorage.removeItem('edit_rfp_draft')
  localStorage.removeItem('rfp_draft_current')
  console.log('Cleared draft state - creating new RFP')
  
  // Navigate to creation page
  router.push('/rfp-creation')
}

const editDraft = async (draft: any) => {
  if (draft.isLocal) {
    // For local drafts, navigate to Phase1Creation page
    router.push('/rfp-creation')
  } else {
    // For server drafts, fetch FULL details and load into edit page
    console.log('📝 Editing draft:', draft.id)
    
    try {
      // Fetch full RFP details including evaluation criteria
      console.log('📥 Fetching full RFP details for editing...')
      const response = await axios.get(`${API_BASE_URL}/rfps/${draft.id}/`, {
        headers: getAuthHeaders()
      })
      const fullRfpData = response.data
      
      console.log('✅ Full RFP data fetched:', fullRfpData)
      console.log('📋 Evaluation criteria in response:', fullRfpData.evaluation_criteria?.length || 0)
      
      // Store the draft RFP ID and FULL data in localStorage for Phase1Creation to load
      localStorage.setItem('current_rfp_id', draft.id.toString())
      localStorage.setItem('edit_rfp_draft', JSON.stringify(fullRfpData))
      
      console.log('✅ Stored full RFP data in localStorage')
      
      // Navigate to Phase1Creation page using Vue Router
      router.push('/rfp-creation')
    } catch (err) {
      console.error('❌ Error fetching full RFP details:', err)
      error('Load Error', 'Failed to load RFP details for editing.')
    }
  }
}

const publishDraft = async (draft: any) => {
  if (draft.isLocal) {
    // For local drafts, navigate to Phase1Creation page to complete and save
    router.push('/rfp-creation')
  } else {
    // For server drafts, update status to IN_REVIEW
    try {
      const response = await axios.patch(`${API_BASE_URL}/rfps/${draft.id}/`, {
        status: 'IN_REVIEW'
      }, {
        headers: getAuthHeaders()
      })
      
      success('Draft Published', `RFP "${draft.title}" has been moved to review status.`)
      
      // Reload drafts
      await loadServerDrafts()
      await loadLocalDrafts()
      
      // Close modal if open
      selectedDraft.value = null
      
    } catch (err) {
      console.error('Error publishing draft:', err)
      error('Publish Error', 'Failed to publish draft. Please try again.')
    }
  }
}

const deleteDraft = async (draft: any) => {
  if (draft.isLocal) {
    PopupService.confirm(
      'Are you sure you want to delete this local draft?',
      'Confirm Deletion',
      async () => {
        localStorage.removeItem('rfp_draft_current')
        await loadServerDrafts()
        await loadLocalDrafts() // Reload to update the list
      }
    )
  } else {
    // Delete server draft
    PopupService.confirm(
      `Are you sure you want to delete "${draft.title}"? This action cannot be undone.`,
      'Confirm Deletion',
      async () => {
        try {
          await axios.delete(`${API_BASE_URL}/rfps/${draft.id}/`, {
            headers: getAuthHeaders()
          })
          
          success('Draft Deleted', `RFP "${draft.title}" has been deleted successfully.`)
          
          // Reload drafts
          await loadServerDrafts()
          await loadLocalDrafts()
          
          // Close modal if open
          selectedDraft.value = null
          
        } catch (err) {
          console.error('Error deleting draft:', err)
          error('Delete Error', 'Failed to delete draft. Please try again.')
        }
      }
    )
  }
}

// Load drafts on component mount
onMounted(async () => {
  await loggingService.logPageView('RFP', 'Draft Manager')
  // Load server drafts first, then local drafts
  await loadServerDrafts()
  await loadLocalDrafts()
})
</script>

<style scoped>
/* Additional draft manager specific styles can be added here */
</style>
