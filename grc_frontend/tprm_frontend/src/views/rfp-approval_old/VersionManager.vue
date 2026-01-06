<template>
  <div class="version-manager max-w-7xl mx-auto p-6">
    <!-- Header -->
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm mb-6">
      <div class="px-6 py-4 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div>
            <h1 class="text-2xl font-bold text-gray-900">Version Management</h1>
            <p class="text-gray-600 mt-1">
              Manage and track RFP approval versions, review changes, and maintain audit trail
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
              <span>Back</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Approval Info -->
      <div class="px-6 py-4 bg-gray-50">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <span class="text-sm font-medium text-gray-700">Approval ID:</span>
            <p class="text-sm text-gray-900 font-mono">{{ approvalId }}</p>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">Current Version:</span>
            <p class="text-sm text-gray-900">{{ currentVersion?.version_number || 'N/A' }}</p>
          </div>
          <div>
            <span class="text-sm font-medium text-gray-700">Total Versions:</span>
            <p class="text-sm text-gray-900">{{ versions.length }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Version Actions -->
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm mb-6">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">Version Actions</h2>
          <div class="flex items-center space-x-3">
            <button 
              @click="loadVersions"
              :disabled="loading"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <svg v-if="!loading" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>{{ loading ? 'Loading...' : 'Refresh Versions' }}</span>
            </button>
            <button 
              @click="showCreateVersionModal = true"
              :disabled="!canCreateVersion"
              class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
              </svg>
              <span>Create New Version</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Version List -->
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Version History</h2>
        <p class="text-sm text-gray-600 mt-1">Track all versions and their changes</p>
      </div>

      <div v-if="loading" class="p-8 text-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p class="text-sm text-gray-600 mt-2">Loading versions...</p>
      </div>

      <div v-else-if="versions.length === 0" class="p-8 text-center">
        <div class="text-gray-400 mb-4">
          <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
        </div>
        <h3 class="text-lg font-medium text-gray-900 mb-2">No Versions Found</h3>
        <p class="text-gray-600">This approval request doesn't have any versions yet.</p>
      </div>

      <div v-else class="divide-y divide-gray-200">
        <div 
          v-for="version in versions" 
          :key="version.version_id"
          class="p-6 hover:bg-gray-50 transition-colors"
        >
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-3 mb-3">
                <div class="flex items-center space-x-2">
                  <div :class="getVersionTypeBadgeClass(version.version_type)" class="px-3 py-1 text-sm font-medium rounded-full">
                    {{ version.version_type }}
                  </div>
                  <div class="text-lg font-semibold text-gray-900">v{{ version.version_number }}</div>
                  <div v-if="version.is_current" class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                    Current
                  </div>
                  <div v-if="version.is_approved" class="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                    Approved
                  </div>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <h4 class="text-sm font-medium text-gray-700 mb-1">Version Label</h4>
                  <p class="text-sm text-gray-900">{{ version.version_label || 'No label' }}</p>
                </div>
                <div>
                  <h4 class="text-sm font-medium text-gray-700 mb-1">Created By</h4>
                  <p class="text-sm text-gray-900">{{ version.created_by_name }} ({{ version.created_by_role }})</p>
                </div>
                <div>
                  <h4 class="text-sm font-medium text-gray-700 mb-1">Created At</h4>
                  <p class="text-sm text-gray-900">{{ formatDate(version.created_at) }}</p>
                </div>
                <div v-if="version.parent_version_id">
                  <h4 class="text-sm font-medium text-gray-700 mb-1">Parent Version</h4>
                  <p class="text-sm text-gray-900">v{{ getParentVersionNumber(version.parent_version_id) }}</p>
                </div>
              </div>

              <div v-if="version.changes_summary" class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-1">Changes Summary</h4>
                <p class="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">{{ version.changes_summary }}</p>
              </div>

              <div v-if="version.change_reason" class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-1">Change Reason</h4>
                <p class="text-sm text-gray-900 bg-blue-50 p-3 rounded-md border border-blue-200">{{ version.change_reason }}</p>
              </div>

              <!-- Version Actions -->
              <div class="flex items-center space-x-3">
                <button 
                  @click="viewVersion(version)"
                  class="px-3 py-1 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors text-sm font-medium"
                >
                  View Details
                </button>
                <button 
                  @click="compareVersions(version)"
                  class="px-3 py-1 bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200 transition-colors text-sm font-medium"
                >
                  Compare
                </button>
                <button 
                  v-if="!version.is_current && canCreateVersion"
                  @click="createRevisionFromVersion(version)"
                  class="px-3 py-1 bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors text-sm font-medium"
                >
                  Create Revision
                </button>
                <button 
                  v-if="version.is_current && !version.is_approved"
                  @click="approveVersion(version)"
                  class="px-3 py-1 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm font-medium"
                >
                  Approve Version
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Version Modal -->
    <div v-if="showCreateVersionModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">Create New Version</h3>
            <button 
              @click="showCreateVersionModal = false"
              class="text-gray-400 hover:text-gray-600"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>

        <form @submit.prevent="createVersion" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Version Type</label>
            <select 
              v-model="newVersion.version_type"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="REVISION">Revision</option>
              <option value="CONSOLIDATION">Consolidation</option>
              <option value="FINAL">Final</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Version Label</label>
            <input 
              v-model="newVersion.version_label"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g., Updated Budget, Final Review"
              required
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Changes Summary</label>
            <textarea 
              v-model="newVersion.changes_summary"
              rows="3"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Describe what changes were made in this version..."
              required
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Change Reason</label>
            <textarea 
              v-model="newVersion.change_reason"
              rows="2"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Why were these changes necessary?"
            ></textarea>
          </div>

          <div class="flex items-center justify-end space-x-3 pt-4">
            <button 
              type="button"
              @click="showCreateVersionModal = false"
              class="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button 
              type="submit"
              :disabled="creating"
              class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <svg v-if="creating" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span>{{ creating ? 'Creating...' : 'Create Version' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Version Details Modal -->
    <div v-if="showVersionDetailsModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">Version Details - v{{ selectedVersion?.version_number }}</h3>
            <button 
              @click="showVersionDetailsModal = false"
              class="text-gray-400 hover:text-gray-600"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>

        <div v-if="selectedVersion" class="p-6">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="space-y-4">
              <div>
                <h4 class="text-sm font-medium text-gray-700 mb-2">Version Information</h4>
                <div class="bg-gray-50 p-4 rounded-lg space-y-2">
                  <div class="flex justify-between">
                    <span class="text-sm text-gray-600">Version Number:</span>
                    <span class="text-sm font-medium text-gray-900">v{{ selectedVersion.version_number }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-sm text-gray-600">Type:</span>
                    <span :class="getVersionTypeBadgeClass(selectedVersion.version_type)" class="px-2 py-1 text-xs font-medium rounded-full">
                      {{ selectedVersion.version_type }}
                    </span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-sm text-gray-600">Label:</span>
                    <span class="text-sm font-medium text-gray-900">{{ selectedVersion.version_label || 'N/A' }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-sm text-gray-600">Created By:</span>
                    <span class="text-sm font-medium text-gray-900">{{ selectedVersion.created_by_name }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-sm text-gray-600">Created At:</span>
                    <span class="text-sm font-medium text-gray-900">{{ formatDate(selectedVersion.created_at) }}</span>
                  </div>
                </div>
              </div>

              <div v-if="selectedVersion.changes_summary">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Changes Summary</h4>
                <div class="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <p class="text-sm text-gray-900">{{ selectedVersion.changes_summary }}</p>
                </div>
              </div>

              <div v-if="selectedVersion.change_reason">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Change Reason</h4>
                <div class="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                  <p class="text-sm text-gray-900">{{ selectedVersion.change_reason }}</p>
                </div>
              </div>
            </div>

            <div>
              <h4 class="text-sm font-medium text-gray-700 mb-2">Version Data</h4>
              <div class="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                <pre class="text-xs text-gray-900 whitespace-pre-wrap">{{ formatJsonData(selectedVersion.json_payload) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Compare Versions Modal -->
    <div v-if="showCompareModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b border-gray-200">
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-900">Compare Versions</h3>
            <button 
              @click="showCompareModal = false"
              class="text-gray-400 hover:text-gray-600"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>

        <div class="p-6">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 class="text-sm font-medium text-gray-700 mb-2">Version A - v{{ comparisonVersionA?.version_number }}</h4>
              <div class="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                <pre class="text-xs text-gray-900 whitespace-pre-wrap">{{ formatJsonData(comparisonVersionA?.json_payload) }}</pre>
              </div>
            </div>
            <div>
              <h4 class="text-sm font-medium text-gray-700 mb-2">Version B - v{{ comparisonVersionB?.version_number }}</h4>
              <div class="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto">
                <pre class="text-xs text-gray-900 whitespace-pre-wrap">{{ formatJsonData(comparisonVersionB?.json_payload) }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { API_CONFIG, API_ENDPOINTS, buildApiUrl, apiCall } from '@/config/api.js'
import { useRfpApi } from '@/composables/useRfpApi'
import { useNotifications } from '@/composables/useNotifications'
import loggingService from '@/services/loggingService'

// Router
const route = useRoute()
const router = useRouter()

// Notifications
const { showSuccess, showError, showWarning, showInfo } = useNotifications()

// Get authenticated headers for axios requests
const { getAuthHeaders } = useRfpApi()

// Props
const props = defineProps({
  approvalId: {
    type: String,
    required: true
  },
  userId: {
    type: String,
    required: false
  }
})

// Reactive data
const approvalId = ref(props.approvalId || route.query.approvalId as string || '')
const versions = ref([])
const loading = ref(false)
const creating = ref(false)

// Modals
const showCreateVersionModal = ref(false)
const showVersionDetailsModal = ref(false)
const showCompareModal = ref(false)

// Selected version for details
const selectedVersion = ref(null)

// Comparison versions
const comparisonVersionA = ref(null)
const comparisonVersionB = ref(null)

// New version form
const newVersion = reactive({
  version_type: 'REVISION',
  version_label: '',
  changes_summary: '',
  change_reason: ''
})

// Computed properties
const currentVersion = computed(() => {
  return versions.value.find(v => v.is_current) || versions.value[0]
})

const canCreateVersion = computed(() => {
  // User can create version if they have permission and there's an existing version
  return versions.value.length > 0 && !loading.value
})

// Methods
const loadVersions = async () => {
  if (!approvalId.value) return
  
  try {
    loading.value = true
    console.log('🔄 Loading versions for approval:', approvalId.value)
    
    const url = buildApiUrl(`/approval-request-versions/${approvalId.value}/`)
    const response = await apiCall(url)
    
    if (response.success && response.versions) {
      versions.value = response.versions
      console.log('✅ Versions loaded:', versions.value.length)
    } else {
      console.log('⚠️ No versions found or API error')
      versions.value = []
    }
  } catch (error) {
    console.error('❌ Error loading versions:', error)
    showError('Failed to load version history')
    versions.value = []
  } finally {
    loading.value = false
  }
}

const createVersion = async () => {
  try {
    creating.value = true
    
    const versionData = {
      approval_id: approvalId.value,
      version_type: newVersion.version_type,
      version_label: newVersion.version_label,
      changes_summary: newVersion.changes_summary,
      change_reason: newVersion.change_reason,
      created_by: props.userId || '1',
      created_by_name: 'Current User', // This should come from user context
      created_by_role: 'Reviewer' // This should come from user context
    }
    
    const url = buildApiUrl('/approval-request-versions/')
    const response = await apiCall(url, {
      method: 'POST',
      body: JSON.stringify(versionData)
    })
    
    if (response.success) {
      showSuccess('Version created successfully')
      showCreateVersionModal.value = false
      
      // Reset form
      Object.assign(newVersion, {
        version_type: 'REVISION',
        version_label: '',
        changes_summary: '',
        change_reason: ''
      })
      
      // Reload versions
      await loadVersions()
    } else {
      showError(response.message || 'Failed to create version')
    }
  } catch (error) {
    console.error('❌ Error creating version:', error)
    showError('Failed to create version')
  } finally {
    creating.value = false
  }
}

const viewVersion = (version) => {
  selectedVersion.value = version
  showVersionDetailsModal.value = true
}

const compareVersions = (version) => {
  // For now, compare with current version
  const current = currentVersion.value
  if (current && current.version_id !== version.version_id) {
    comparisonVersionA.value = current
    comparisonVersionB.value = version
    showCompareModal.value = true
  } else {
    showWarning('Cannot compare version with itself')
  }
}

const createRevisionFromVersion = (version) => {
  // Pre-fill the form with version info
  newVersion.version_type = 'REVISION'
  newVersion.version_label = `Revision of v${version.version_number}`
  newVersion.change_reason = `Based on version ${version.version_number}`
  showCreateVersionModal.value = true
}

const approveVersion = async (version) => {
  try {
    const url = buildApiUrl(`/approval-request-versions/${version.version_id}/approve/`)
    const response = await apiCall(url, {
      method: 'POST'
    })
    
    if (response.success) {
      showSuccess('Version approved successfully')
      await loadVersions()
    } else {
      showError(response.message || 'Failed to approve version')
    }
  } catch (error) {
    console.error('❌ Error approving version:', error)
    showError('Failed to approve version')
  }
}

const getParentVersionNumber = (parentVersionId) => {
  const parent = versions.value.find(v => v.version_id === parentVersionId)
  return parent ? parent.version_number : 'Unknown'
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

const formatDate = (dateString) => {
  if (!dateString) return 'Not set'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return dateString
  }
}

const formatJsonData = (data) => {
  if (!data) return 'No data available'
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}

const goBack = () => {
  try {
    router.go(-1)
  } catch (error) {
    console.error('Navigation error:', error)
    window.history.back()
  }
}

// Lifecycle
onMounted(async () => {
  await loggingService.logPageView('RFP', 'Version Manager')
  await loadVersions()
})
</script>

<style scoped>
.version-manager {
  min-height: 100vh;
  background-color: #f9fafb;
}
</style>
