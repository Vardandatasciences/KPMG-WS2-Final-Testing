<template>
  <div class="framework-policies-container">
    <div class="export-controls">
      <div class="export-controls-inner">
        <div class="export-select-wrapper" @click.stop="isExportDropdownOpen = !isExportDropdownOpen">
          <button
            type="button"
            class="export-select-trigger"
          >
            <span class="export-select-text">{{ selectedExportFormatLabel }}</span>
            <i class="fas fa-chevron-down export-select-icon"></i>
          </button>
          <div
            v-if="isExportDropdownOpen"
            class="export-select-menu"
          >
            <div
              v-for="opt in exportFormatOptions"
              :key="opt.value || 'placeholder'"
              class="export-select-option"
              :class="{
                'is-placeholder': opt.value === '',
                'is-selected': opt.value === selectedExportFormat
              }"
              @click.stop="selectExportFormatOption(opt)"
            >
              <span
                v-if="opt.value === selectedExportFormat"
                class="export-select-check"
              >
                <i class="fas fa-check"></i>
              </span>
              <span class="export-select-option-label">
                {{ opt.label }}
              </span>
            </div>
          </div>
        </div>
        <button
          class="export-btn"
          @click="exportPolicies"
          :disabled="!selectedExportFormat"
        >
          <i class="fas fa-download"></i>
          Export
        </button>
      </div>
    </div>

    <div class="breadcrumb-tab">
      <span class="breadcrumb-chip">
        {{ frameworkName }}
        <span class="breadcrumb-close" @click="goBack">×</span>
      </span>
    </div>

    <h1>Policies for {{ frameworkName || '…' }}</h1>
    <div class="page-header-underline"></div>

    <div
      v-if="showPoliciesSkeleton"
      class="policy-page-skeleton policy-fwp-skeleton"
      aria-busy="true"
      aria-label="Loading policies"
    >
      <div class="policy-skeleton-summary">
        <div v-for="n in 2" :key="'fwp-sum-' + n" class="policy-skeleton-card"></div>
      </div>
      <div class="policy-skeleton-table">
        <div v-for="n in 8" :key="'fwp-row-' + n" class="policy-skeleton-row"></div>
      </div>
    </div>
    <template v-else>
    <!-- Policy Summary Cards -->
    <div class="summary-section">
      <div class="summary-cards">
        <!-- Policy Cards -->
        <div class="summary-card" :class="{ 'active-policy': activePolicyTab === 'Active' }" @click="filterByStatus('Active', 'policy')">
          <div class="summary-card-content">
            <div class="summary-label">ACTIVE POLICIES</div>
            <div class="summary-value">{{ policyCounts.active }}</div>
          </div>
        </div>
        <div class="summary-card" :class="{ 'active-policy': activePolicyTab === 'Inactive' }" @click="filterByStatus('Inactive', 'policy')">
          <div class="summary-card-content">
            <div class="summary-label">INACTIVE POLICIES</div>
            <div class="summary-value">{{ policyCounts.inactive }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="top-controls">
      <div class="framework-policies-entity-dropdown-section">
        <CustomDropdown
          :config="entityDropdownConfig"
          v-model="selectedEntity"
          :show-search-bar="true"
        />
      </div>

      <!-- View Toggle Controls -->
      <div class="view-toggle-controls">
        <button 
          class="view-toggle-btn" 
          :class="{ active: currentView === 'list' }"
          @click="currentView = 'list'"
          title="List View"
        >
          <i class="fas fa-list"></i>
        </button>
        <button 
          class="view-toggle-btn" 
          :class="{ active: currentView === 'card' }"
          @click="currentView = 'card'"
          title="Card View"
        >
          <i class="fas fa-th-large"></i>
        </button>
      </div>
    </div>

    <!-- Card View (Default/Existing) -->
    <div v-if="currentView === 'card'" class="policy-card-grid">
      <div v-for="policy in policies" :key="policy.id" class="policy-card">
        <div class="policy-card-header">
          <div class="policy-title-section">
            <span class="policy-icon">
              <i class="fas fa-file-alt"></i>
            </span>
            <span class="policy-card-title">{{ policy.name }}</span>
          </div>
        </div>
        <div class="policy-card-meta">
          <span class="policy-card-category">Category: {{ policy.category }}</span>
          <span class="policy-card-type" :class="policy.type === 'External' ? 'external' : ''">
            Type: {{ policy.type || 'External' }}
          </span>
        </div>
        <div class="policy-card-desc">{{ policy.description }}</div>
        <div class="policy-card-actions">
          <div class="action-buttons">
            <label class="switch" @click.stop>
              <input type="checkbox" :checked="policy.status === 'Active'" @change="toggleStatus(policy)" />
              <span class="slider"></span>
            </label>
            <button v-if="policy.status === 'Active'"
                    @click="acknowledgePolicy(policy)"
                    class="acknowledge-btn"
                    title="Create acknowledgement request for this policy">
              Request Ack
            </button>
            <button v-if="policy.status === 'Active'"
                    @click="viewPolicyAcknowledgements(policy)"
                    class="view-reports-btn"
                    title="View acknowledgement reports for this policy">
              View Reports
            </button>
            <span class="document-icon" @click="showPolicyDetails(policy.id)">
              <i class="fas fa-file-lines"></i>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- List View -->
    <div v-if="currentView === 'list'" class="policy-list-container">
      <div class="policy-list-header">
        <div class="list-header-item">Policy</div>
        <div class="list-header-item">Category</div>
        <div class="list-header-item">Type</div>
        <div class="list-header-item">Description</div>
        <div class="list-header-item">Status</div>
        <div class="list-header-item">Actions</div>
      </div>
      
      <div class="policy-list">
        <div v-for="policy in policies" :key="policy.id" class="policy-list-item">
          <div class="list-item-content">
            <div class="policy-name-cell">
              <div class="policy-name-text">
                <div class="policy-title">{{ policy.name }}</div>
                <div class="policy-id">ID: {{ policy.id }}</div>
              </div>
            </div>
            
            <div class="policy-category-cell">
              <span class="category-text">{{ policy.category }}</span>
            </div>
            
            <div class="policy-type-cell">
              <span class="type-text">{{ policy.type || 'External' }}</span>
            </div>
            
            <div class="policy-description-cell">
              <p class="description-text">{{ policy.description }}</p>
            </div>
            
            <div class="policy-status-cell">
              <div class="status-controls">
                <label class="switch" @click.stop>
                  <input type="checkbox" :checked="policy.status === 'Active'" @change="toggleStatus(policy)" />
                  <span class="slider"></span>
                </label>
                <span class="switch-label" :class="policy.status === 'Active' ? 'active' : 'inactive'">{{ policy.status }}</span>
              </div>
            </div>
            
            <div class="policy-actions-cell">
              <div class="list-action-buttons">
                <button v-if="policy.status === 'Active'"
                        @click="acknowledgePolicy(policy)"
                        class="acknowledge-btn-list"
                        title="Create acknowledgement request for this policy">
                  Request Ack
                </button>
                <button v-if="policy.status === 'Active'"
                        @click="viewPolicyAcknowledgements(policy)"
                        class="view-reports-btn-list"
                        title="View acknowledgement reports for this policy">
                  View Reports
                </button>
                <button class="action-btn details-btn" @click="showPolicyDetails(policy.id)">
                  <span>Details</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </template>
 
    <!-- Popup Modal -->
    <PopupModal />
    
    <!-- Acknowledgement Request Modal -->
    <CreateAcknowledgementModal
      v-if="showAcknowledgementModal && selectedPolicyForAck"
      :isVisible="showAcknowledgementModal"
      :policy="selectedPolicyForAck"
      @close="closeAcknowledgementModal"
      @submit="handleAcknowledgementSubmit"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiService from '@/services/apiService.js'
import { PopupService } from '@/modules/popus/popupService'
import PopupModal from '@/modules/popus/PopupModal.vue'
import CustomDropdown from '@/components/CustomDropdown.vue'
import CreateAcknowledgementModal from './CreateAcknowledgementModal.vue'
import {  API_ENDPOINTS } from '../../config/api.js'
import { openDownloadInNewTabWithAnchorFallback } from '@/utils/safeExternalNavigation'
import { useFrameworkStore } from '@/stores/framework'
import { usePolicyStore } from '@/stores/policy'

// Add view state
const currentView = ref('list') // 'list' or 'card' - default to list view

// Add active policy tab state
const activePolicyTab = ref('Active') // 'Active' or 'Inactive'
 
const router = useRouter()
const route = useRoute()
const frameworkId = route.params.frameworkId
const frameworkName = ref('')
const frameworkStatus = ref('')
const policies = ref([])
const allPolicies = ref([]) // Store all policies for filtering
const selectedEntity = ref('')
const frameworkStore = useFrameworkStore()
const policyStore = usePolicyStore()
const entities = ref([])
const isLoading = ref(false)
const showPoliciesSkeleton = computed(
  () => isLoading.value && (!allPolicies.value || allPolicies.value.length === 0)
)

// Acknowledgement modal state
const showAcknowledgementModal = ref(false)
const selectedPolicyForAck = ref(null)

// Add policy counts state
const policyCounts = ref({
  active: 0,
  inactive: 0
})

// Add status filter state
const statusFilter = ref(null)
const typeFilter = ref(null)

// Add export format state
const selectedExportFormat = ref('')
const isExportDropdownOpen = ref(false)
const exportFormatOptions = [
  { value: '', label: 'Select format' },
  { value: 'xlsx', label: 'Excel (.xlsx)' },
  { value: 'pdf', label: 'PDF (.pdf)' },
  { value: 'csv', label: 'CSV (.csv)' },
  { value: 'json', label: 'JSON (.json)' },
  { value: 'xml', label: 'XML (.xml)' },
  { value: 'txt', label: 'Text (.txt)' }
]

const selectedExportFormatLabel = computed(() => {
  const match = exportFormatOptions.find(
    (opt) => opt.value === selectedExportFormat.value
  )
  return match ? match.label : 'Select format'
})

const selectExportFormatOption = (opt) => {
  selectedExportFormat.value = opt.value
  isExportDropdownOpen.value = false
}

// Push notification method
const sendPushNotification = async (notificationData) => {
  try {
    const response = await fetch(API_ENDPOINTS.PUSH_NOTIFICATION, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(notificationData)
    });
    if (response.ok) {
      console.log('Push notification sent successfully');
    } else {
      console.error('Failed to send push notification');
    }
  } catch (error) {
    console.error('Error sending push notification:', error);
  }
}

// Export policies function
const exportPolicies = async () => {
  if (!selectedExportFormat.value) {
    PopupService.warning('Please select a format.', 'Missing Selection');
    return;
  }
  try {
    const res = await apiService.post(`/frameworks/${frameworkId}/policies/export/`, {
      format: selectedExportFormat.value
    });
    const { file_url, file_name } = res;
    if (!file_url || !file_name) {
      PopupService.error('Export failed: No file URL or name returned.', 'Export Error');
      sendPushNotification({
        title: 'Policy Export Failed',
        message: 'Export failed: No file URL or name returned.',
        category: 'policy',
        priority: 'high',
        user_id: 'default_user'
      });
      return;
    }
    const ok = await openDownloadInNewTabWithAnchorFallback(file_url, file_name)
    if (ok) {
      PopupService.success('Export completed successfully! File opened or downloaded.', 'Export Success');
      sendPushNotification({
        title: 'Policy Export Completed',
        message: `Policy export completed successfully in ${selectedExportFormat.value.toUpperCase()} format.`,
        category: 'policy',
        priority: 'medium',
        user_id: 'default_user'
      });
    } else {
      PopupService.warning('Export link is not from an allowed host.', 'Export');
    }
  } catch (err) {
    PopupService.error('Export failed. Please try again.', 'Export Error');
    sendPushNotification({
      title: 'Policy Export Failed',
      message: `Failed to export policies: ${err.response?.data?.error || err.message}`,
      category: 'policy',
      priority: 'high',
      user_id: 'default_user'
    });
    console.error(err);
  }
};
 
// Format date for display
// Check for selected framework from session and set it as default
const checkSelectedFrameworkFromSession = async () => {
  try {
    console.log('🔍 DEBUG: Checking for selected framework from session in FrameworkPolicies...')
    console.log('🔍 DEBUG: Current route frameworkId:', frameworkId)
    await frameworkStore.loadFrameworkFromSession()
    const response = {
      success: true,
      frameworkId: frameworkStore.selectedFrameworkId,
    }
    console.log('📊 DEBUG: Selected framework response:', response)
    
    if (response && response.success) {
      // Check if a framework is selected (not null)
      if (response.frameworkId) {
        const sessionFrameworkId = response.frameworkId
        console.log('✅ DEBUG: Found selected framework in session:', sessionFrameworkId)
        
        // Update the frameworkId from route params to use session framework
        if (sessionFrameworkId.toString() !== frameworkId.toString()) {
          console.log('🔄 DEBUG: Updating frameworkId from session:', sessionFrameworkId)
          console.log('🔄 DEBUG: Current route frameworkId:', frameworkId)
          // Update the route parameter to use the session framework
          await router.replace({ 
            name: 'FrameworkPolicies', 
            params: { frameworkId: sessionFrameworkId },
            query: route.query 
          })
          console.log('✅ DEBUG: Route updated to use session framework')
        } else {
          console.log('✅ DEBUG: Route already using session framework')
        }
      } else {
        // "All Frameworks" is selected (frameworkId is null)
        console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
        console.log('🌐 DEBUG: Redirecting to Framework Explorer to show all frameworks')
        // Redirect back to Framework Explorer when "All Frameworks" is selected
        await router.push({ name: 'FrameworkExplorer' })
      }
    } else {
      console.log('ℹ️ DEBUG: No framework found in session, using route frameworkId:', frameworkId)
    }
  } catch (error) {
    console.error('❌ DEBUG: Error checking selected framework from session:', error)
  }
}

const applyPoliciesListResponse = (response) => {
  allPolicies.value = response.policies || []
  if (response.framework) {
    frameworkName.value = response.framework.name
    frameworkStatus.value = response.framework.status || 'Unknown'
  }
  const activeCount = allPolicies.value.filter((policy) => policy.status === 'Active').length
  const inactiveCount = allPolicies.value.filter((policy) => policy.status === 'Inactive').length
  policyCounts.value = {
    active: response.policy_counts?.active ?? activeCount,
    inactive: response.policy_counts?.inactive ?? inactiveCount,
  }
}

/** Authoritative API refresh; updates Pinia cache for instant return visits */
const syncPoliciesFromNetwork = async (frameworkId) => {
  const fid = String(frameworkId)
  const response = await apiService.get(API_ENDPOINTS.FRAMEWORK_GET_POLICIES_LIST(fid))
  applyPoliciesListResponse(response)
  policyStore.setFrameworkPoliciesListCache(fid, allPolicies.value)
}

// Fetch policies for the selected framework (Pinia cache-first + background sync)
const fetchPolicies = async () => {
  isLoading.value = true
  let currentFrameworkId = route.params.frameworkId
  try {
    await checkSelectedFrameworkFromSession()
    currentFrameworkId = route.params.frameworkId
    console.log('🔍 DEBUG: Fetching policies for framework:', currentFrameworkId)

    if (policyStore.hasFrameworkPoliciesListCache(currentFrameworkId)) {
      const cached = policyStore.getFrameworkPoliciesListCached(currentFrameworkId)
      allPolicies.value = (cached || []).map((policy) => ({
        ...policy,
        status: policy.status || policy.ActiveInactive || 'Unknown',
      }))
      if (!frameworkName.value) {
        const frameworks = await policyStore.getAllFrameworks({ force: false })
        const selectedFramework = (frameworks || []).find(
          (fw) => Number(fw.FrameworkId || fw.id) === Number(currentFrameworkId)
        )
        frameworkName.value =
          selectedFramework?.FrameworkName || selectedFramework?.name || frameworkName.value
      }
      const activeCount = allPolicies.value.filter((policy) => policy.status === 'Active').length
      const inactiveCount = allPolicies.value.filter((policy) => policy.status === 'Inactive').length
      policyCounts.value = { active: activeCount, inactive: inactiveCount }
      isLoading.value = false
      void syncPoliciesFromNetwork(currentFrameworkId).catch((e) =>
        console.warn('[FrameworkPolicies] Background policy sync failed:', e)
      )
      return
    }

    await syncPoliciesFromNetwork(currentFrameworkId)
  } catch (error) {
    console.error('Error fetching policies:', error)
    try {
      const cachedPolicies = await policyStore.getPoliciesByFramework(currentFrameworkId)
      allPolicies.value = (cachedPolicies || []).map((policy) => ({
        ...policy,
        status: policy.status || policy.ActiveInactive || 'Unknown',
      }))

      if (!frameworkName.value) {
        const frameworks = await policyStore.getAllFrameworks()
        const selectedFramework = (frameworks || []).find(
          (fw) => Number(fw.FrameworkId || fw.id) === Number(currentFrameworkId)
        )
        frameworkName.value = selectedFramework?.FrameworkName || selectedFramework?.name || frameworkName.value
      }

      const activeCount = allPolicies.value.filter((policy) => policy.status === 'Active').length
      const inactiveCount = allPolicies.value.filter((policy) => policy.status === 'Inactive').length
      policyCounts.value = { active: activeCount, inactive: inactiveCount }
      return
    } catch (fallbackError) {
      console.error('Policy store fallback failed:', fallbackError)
    }
    sendPushNotification({
      title: 'Policy List Loading Failed',
      message: `Failed to load policies for framework "${frameworkName.value || 'Unknown Framework'}": ${error.response?.data?.error || error.message}`,
      category: 'policy',
      priority: 'high',
      user_id: 'default_user',
    })
  } finally {
    isLoading.value = false
  }
}

// Fetch entities from API
const fetchEntities = async () => {
  try {
    const response = await apiService.get(API_ENDPOINTS.ENTITIES)
    entities.value = response.entities || []
  } catch (error) {
    console.error('Error fetching entities:', error)
    sendPushNotification({
      title: 'Entity List Loading Failed',
      message: `Failed to load entities for policy filtering: ${error.response?.data?.error || error.message}`,
      category: 'policy',
      priority: 'medium',
      user_id: 'default_user'
    });
  }
}

// Filter policies based on selected entity
const filteredPolicies = computed(() => {
  let result = allPolicies.value
  
  // Apply entity filter
  if (selectedEntity.value) {
    console.log('Filtering policies with entity:', selectedEntity.value)
    console.log('Total policies before filtering:', allPolicies.value.length)
    
    result = result.filter(policy => {
      // If policy has no entities field, don't show it when filtering
      if (!policy.Entities) return false
      
      // If policy applies to all entities, always show it when any entity filter is active
      if (policy.Entities === 'all') {
        return true
      }
      
      // If "All Entities" is selected, show all policies
      if (selectedEntity.value === 'all') {
        return true
      }
      
      // For specific entity selection
      if (Array.isArray(policy.Entities)) {
        // Show policy if it applies to all entities OR includes the selected entity
        // Handle both string and numeric entity IDs
        const selectedEntityInt = parseInt(selectedEntity.value)
        const selectedEntityStr = selectedEntity.value.toString()
        
        return policy.Entities.includes('all') || 
               policy.Entities.includes(selectedEntityInt) || 
               policy.Entities.includes(selectedEntityStr)
      }
      
      return false
    })
  }
  
  // Apply status filter
  if (statusFilter.value && typeFilter.value === 'policy') {
    result = result.filter(policy => policy.status === statusFilter.value)
  }
  
  console.log('Filtered policies count:', result.length)
  console.log('Filtered policies:', result.map(p => ({ name: p.name, entities: p.Entities, status: p.status })))
  
  return result
})

// Filter by status function
const filterByStatus = (status, type) => {
  // Check if we're clicking the same filter that's already active
  if (statusFilter.value === status && typeFilter.value === type) {
    // Clear the filter if it's already active
    clearFilter();
  } else {
    // Apply the new filter
    statusFilter.value = status;
    typeFilter.value = type;
    
    // Update active policy tab for visual indicator
    if (type === 'policy') {
      activePolicyTab.value = status;
    }
  }
}

// Clear all filters
const clearFilter = () => {
  statusFilter.value = null
  typeFilter.value = null
  selectedEntity.value = ''
  activePolicyTab.value = 'Active' // Reset to default
}

// Assign filtered policies to the reactive ref
watch(filteredPolicies, (newPolicies) => {
  policies.value = newPolicies
}, { immediate: true })
 
// Show policy details page
const showPolicyDetails = (policyId) => {
  router.push({
    name: 'FrameworkPolicyDetails',
    params: {
      frameworkId: route.params.frameworkId,
      policyId
    }
  })
}
 
// Toggle policy status
const toggleStatus = async (policy) => {
  // Prevent multiple simultaneous calls for the same policy
  if (policy.isProcessing) {
    console.log('Policy is already being processed, skipping duplicate request');
    return;
  }
  
  // Set processing flag
  policy.isProcessing = true;
  
  try {
    // Check if we're deactivating (Active -> Inactive)
    if (policy.status === 'Active') {
      // First: Show reviewer selection popup
      try {
        const response = await apiService.get(API_ENDPOINTS.USERS_FOR_REVIEWER_SELECTION);
        const reviewers = response;
        
        if (reviewers.length === 0) {
          PopupService.warning('No reviewers available. Please contact administrator.', 'No Reviewers');
          sendPushNotification({
            title: 'No Reviewers Available',
            message: 'No reviewers are available for policy deactivation requests. Please contact administrator.',
            category: 'policy',
            priority: 'high',
            user_id: 'default_user'
          });
          return;
        }
        
        // Step 1: Select reviewer
        const reviewerOptions = reviewers.map(reviewer => ({
          value: reviewer.UserId,
          label: `${reviewer.UserName} (${reviewer.Email})`
        }));
        
        PopupService.select(
          'Select a reviewer for this policy deactivation request:',
          'Select Reviewer',
          reviewerOptions,
          async (selectedReviewerId) => {
            console.log('Selected reviewer ID:', selectedReviewerId);
            
            // Step 2: Get reason after reviewer selection
            PopupService.comment(
              'Please provide a reason for deactivating this policy:',
              'Policy Deactivation Reason',
              async (reason) => {
                if (!reason || reason.trim() === '') {
                  PopupService.warning('Deactivation reason is required.', 'Missing Information');
                  sendPushNotification({
                    title: 'Missing Deactivation Reason',
                    message: 'Policy deactivation request cancelled: Reason is required.',
                    category: 'policy',
                    priority: 'medium',
                    user_id: 'default_user'
                  });
                  return;
                }
                
                try {
                  // Call the API to request status change approval with reviewer ID
                  await apiService.post(`/policies/${policy.id}/toggle-status/`, {
                    reason: reason.trim(),
                    ReviewerId: selectedReviewerId,
                    cascadeSubpolicies: true
                  });
                  
                  // Show success message
                  PopupService.success('Policy deactivation request submitted. Awaiting approval.', 'Request Submitted');
                  
                  sendPushNotification({
                    title: 'Policy Deactivation Request Submitted',
                    message: `Policy "${policy.name}" deactivation request has been submitted and is awaiting approval.`,
                    category: 'policy',
                    priority: 'high',
                    user_id: 'default_user'
                  });
                  
                  // Refresh data to reflect the new 'Under Review' status
                  await fetchPolicies();
                } catch (error) {
                  console.error('Error submitting deactivation request:', error);
                  
                  // Handle specific error cases
                  if (error.response?.status === 400) {
                    const errorMessage = error.response?.data?.error || '';
                    
                    if (errorMessage.includes('already a pending status change request')) {
                      PopupService.error(
                        'There is already a pending status change request for this policy. Please wait for the current request to be processed.',
                        'Duplicate Request'
                      );
                      sendPushNotification({
                        title: 'Duplicate Policy Deactivation Request',
                        message: `Policy "${policy.name}" already has a pending deactivation request. Please wait for approval.`,
                        category: 'policy',
                        priority: 'medium',
                        user_id: 'default_user'
                      });
                    } else {
                      PopupService.error(
                        `Failed to submit deactivation request: ${errorMessage}`,
                        'Request Failed'
                      );
                      sendPushNotification({
                        title: 'Policy Deactivation Request Failed',
                        message: `Failed to submit deactivation request for policy "${policy.name}": ${errorMessage}`,
                        category: 'policy',
                        priority: 'high',
                        user_id: 'default_user'
                      });
                    }
                  } else {
                    PopupService.error('Failed to submit deactivation request. Please try again.', 'Request Failed');
                    sendPushNotification({
                      title: 'Policy Deactivation Request Failed',
                      message: `Failed to submit deactivation request for policy "${policy.name}": ${error.response?.data?.error || error.message}`,
                      category: 'policy',
                      priority: 'high',
                      user_id: 'default_user'
                    });
                  }
                } finally {
                  // Clear processing flag
                  policy.isProcessing = false;
                }
              }
            );
          }
        );
      } catch (error) {
        console.error('Error fetching reviewers:', error);
        PopupService.error('Failed to load reviewers. Please try again.', 'Load Error');
        sendPushNotification({
          title: 'Reviewers Loading Failed',
          message: `Failed to load reviewers for policy deactivation: ${error.response?.data?.error || error.message}`,
          category: 'policy',
          priority: 'high',
          user_id: 'default_user'
        });
      }
    } else {
      // For activation (Inactive -> Active), use the direct toggle endpoint
      const response = await apiService.post(`/policies/${policy.id}/toggle-status/`, {
        cascadeSubpolicies: true
      });
     
      // Update local state
      policy.status = response.status || 'Active';
     
      // Show feedback to the user
      let message = `Policy status change request submitted.`;
     
      if (response.other_versions_deactivated > 0) {
        message += ` ${response.other_versions_deactivated} previous version(s) of this policy were automatically deactivated.`;
      }
     
      if (response.subpolicies_affected > 0) {
        message += ` ${response.subpolicies_affected} subpolicies were also activated.`;
      }
     
      PopupService.success(message, 'Status Update');
      
      sendPushNotification({
        title: 'Policy Activation Successful',
        message: `Policy "${policy.name}" has been successfully activated.`,
        category: 'policy',
        priority: 'high',
        user_id: 'default_user'
      });
     
      // Keep Pinia list cache in sync; background refresh matches server
      policyStore.setFrameworkPoliciesListCache(route.params.frameworkId, allPolicies.value)
      void syncPoliciesFromNetwork(route.params.frameworkId).catch(() => {})
    }
  } catch (error) {
    console.error('Error toggling policy status:', error);
    
    // Handle specific error cases
    if (error.response?.status === 400) {
      const errorMessage = error.response?.data?.error || '';
      
      if (errorMessage.includes('already a pending status change request')) {
        PopupService.error(
          'There is already a pending status change request for this policy. Please wait for the current request to be processed.',
          'Duplicate Request'
        );
        sendPushNotification({
          title: 'Duplicate Policy Status Change Request',
          message: `Policy "${policy.name}" already has a pending status change request. Please wait for approval.`,
          category: 'policy',
          priority: 'medium',
          user_id: 'default_user'
        });
      } else {
        PopupService.error(
          `Failed to update policy status: ${errorMessage}`,
          'Update Failed'
        );
        sendPushNotification({
          title: 'Policy Status Update Failed',
          message: `Failed to update status for policy "${policy.name}": ${errorMessage}`,
          category: 'policy',
          priority: 'high',
          user_id: 'default_user'
        });
      }
    } else {
      PopupService.error('Failed to update policy status. Please try again.', 'Update Failed');
      sendPushNotification({
        title: 'Policy Status Update Failed',
        message: `Failed to update status for policy "${policy.name}": ${error.response?.data?.error || error.message}`,
        category: 'policy',
        priority: 'high',
        user_id: 'default_user'
      });
    }
  } finally {
    // Clear processing flag
    policy.isProcessing = false;
  }
}
 
// Add acknowledge policy function - Opens modal to request acknowledgement
const acknowledgePolicy = async (policy) => {
  // Open the acknowledgement request modal for admins
  selectedPolicyForAck.value = policy
  showAcknowledgementModal.value = true
}

const handleAcknowledgementSubmit = ({ requestData, policy_name, total_users }) => {
  closeAcknowledgementModal()
  void apiService
    .post(API_ENDPOINTS.CREATE_ACKNOWLEDGEMENT_REQUEST, requestData, { background: true })
    .then((response) => {
      void handleAcknowledgementCreated({
        ...response,
        policy_name: response.policy_name || policy_name,
        total_users: response.total_users ?? total_users,
        acknowledgement_request_id: response.acknowledgement_request_id,
      })
    })
    .catch((error) => {
      console.error('Error creating acknowledgement request:', error)
      PopupService.error(
        error.response?.data?.error || 'Failed to create acknowledgement request',
        'Error'
      )
    })
}

const handleAcknowledgementCreated = async (data) => {
  showAcknowledgementModal.value = false
  selectedPolicyForAck.value = null

  sendPushNotification({
    title: 'Acknowledgement Request Created',
    message: `Acknowledgement request created for "${data.policy_name || 'policy'}". ${data.total_users} users assigned.`,
    category: 'policy',
    priority: 'high',
    user_id: 'default_user',
  })

  if (data.acknowledgement_request_id) {
    PopupService.confirm(
      `Acknowledgement request created successfully. ${data.total_users} users assigned.\n\nWould you like to view the report now?`,
      'Request Created',
      async () => {
        router.push({
          name: 'AcknowledgementReport',
          params: { requestId: data.acknowledgement_request_id },
        })
      },
      async () => {
        await fetchPolicies()
      }
    )
  } else {
    await fetchPolicies()
  }
}

// Close acknowledgement modal
const closeAcknowledgementModal = () => {
  showAcknowledgementModal.value = false
  selectedPolicyForAck.value = null
}

// View policy acknowledgement reports
const viewPolicyAcknowledgements = async (policy) => {
  try {
    // Fetch all acknowledgement requests for this policy
    const response = await apiService.get(API_ENDPOINTS.GET_POLICY_ACKNOWLEDGEMENT_REQUESTS(policy.id))
    
    if (response && response.success && response.acknowledgement_requests && response.acknowledgement_requests.length > 0) {
      // If there are multiple requests, show the most recent one
      const latestRequest = response.acknowledgement_requests[0]
      
      // Navigate to the report page
      router.push({
        name: 'AcknowledgementReport',
        params: { requestId: latestRequest.acknowledgement_request_id }
      })
    } else {
      // No reports found - show info message instead of error
      PopupService.info(
        'There are no reports for this policy.',
        'No Reports Found'
      )
    }
  } catch (error) {
    console.error('Error fetching acknowledgement requests:', error)
    
    // For any error when fetching acknowledgement reports, show "no reports found"
    // This handles cases where policy doesn't exist, no requests exist, or any other error
    PopupService.info(
      'There are no reports for this policy.',
      'No Reports Found'
    )
  }
}
 
function goBack() {
  const routeParams = { name: 'FrameworkExplorer' }
  
  // If an entity filter is selected, pass it back as a query parameter
  if (selectedEntity.value) {
    routeParams.query = { entity: selectedEntity.value }
  }
  
  router.push(routeParams)
}
 
// Fetch policies on component mount
// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.export-select-wrapper')) {
    isExportDropdownOpen.value = false
  }
}

onMounted(async () => {
  // Add click outside listener
  document.addEventListener('click', handleClickOutside)
  
  // Check for session framework first, then fetch policies
  await checkSelectedFrameworkFromSession()
  await fetchPolicies()
  await fetchEntities()
  
  // Check if there's an entity filter from the route query parameters
  const entityFromRoute = route.query.entity
  if (entityFromRoute) {
    selectedEntity.value = entityFromRoute
  }
})

onUnmounted(() => {
  // Remove click outside listener
  document.removeEventListener('click', handleClickOutside)
})

const entityDropdownConfig = computed(() => ({
  label: 'Entity',
  values: [
    { value: '', label: 'All Entities' },
    ...entities.value.map(e => ({ value: e.id, label: e.label }))
  ]
}))
</script>
 
<style scoped>
@import '@/assets/css/dropdown.css';
@import '@/assets/css/main.css';

.framework-policies-container {
  padding: 24px 32px;
  margin-left: 280px;
  width: calc(100vw - 280px - 64px);
  max-width: 100%;
  box-sizing: border-box;
  position: relative;
  padding-top: 25px; /* Add space for export controls */
  overflow-x: hidden;
}

h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 8px 0;
  letter-spacing: -1px;
  text-align: left;
  margin-bottom: 50px;
  margin-top: 0;
}


.export-controls {
  position: absolute;
  top: 20px;
  right: 32px;
  z-index: 10;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  width: auto;
  margin-bottom: 0;
}

.export-controls-inner {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* Export controls styles are imported from main.css with colorblindness support */
 
.breadcrumb-tab {
  margin-bottom: 24px;
}
 
.breadcrumb-chip {
  background: #e8edfa;
  color: #4f6cff;
  border-radius: 24px;
  padding: 10px 12px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  font-size: 0.95rem;
  box-shadow: 0 2px 8px rgba(79,108,255,0.12);
  letter-spacing: 0.01em;
  transition: all 0.2s ease;
}
 
.breadcrumb-chip:hover {
  box-shadow: 0 4px 12px rgba(79,108,255,0.18);
  transform: translateY(-1px);
}
 
.breadcrumb-close {
  margin-left: 12px;
  color: #888;
  font-size: 1.1rem;
  cursor: pointer;
  font-weight: bold;
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
}
 
.breadcrumb-close:hover {
  color: #e53935;
  background-color: rgba(229, 57, 53, 0.1);
}

.top-controls {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
  margin-bottom: 5px;
  width: 100%;
  flex-wrap: wrap;
  max-width: 100%;
}

.framework-policies-entity-dropdown-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 0;
}

/* View Toggle Controls */
.view-toggle-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  border-radius: 8px;
  padding: 4px;
  border: 1px solid #333d54;
  margin-left: auto;
}

.view-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
}

.view-toggle-btn:hover {
  background: #e8edfa;
  color: #4f6cff;
}

.view-toggle-btn.active {
  background: #4f6cff;
  color: white;
  box-shadow: 0 2px 4px rgba(79, 108, 255, 0.2);
}

/* Card View Styles (Existing) */
.policy-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  width: 100%;
  max-width: 100%;
  margin-top: 24px;
  box-sizing: border-box;
  padding: 0 8px;
  overflow-x: hidden;
}
 
.policy-card {
  background: #f7f7fa;
  border-radius: 12px;
  padding: 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  font-size: 0.85rem;
  cursor: pointer;
  min-height: 100px;
  box-shadow: 0 2px 8px rgba(79,108,255,0.08);
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  margin: 0;
  min-width: 0;
  overflow: hidden;
}
 
.policy-card:hover {
  transform: translateY(-2px) scale(1.025);
  box-shadow: 0 8px 24px rgba(79,108,255,0.13);
}
 
.policy-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.1rem;
  font-weight: 700;
  width: 100%;
  margin-bottom: 4px;
}
 
.policy-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #e8edfa;
  border-radius: 8px;
  color: #000000;
  font-size: 1rem;
}
 
.policy-card-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.policy-card-category {
  font-size: 0.85rem;
  color: #000000;
  font-weight: 600;
  background: #e8edfa;
  border-radius: 8px;
  padding: 2px 8px;
  width: fit-content;
  margin-bottom: 6px;
}

.policy-card-type {
  font-size: 0.85rem;
  font-weight: 600;
  background: #ffeaea;
  color: #e53935;
  border-radius: 8px;
  padding: 2px 8px;
  width: fit-content;
}

.policy-card-type.external {
  background: #ffeaea;
  color: #e53935;
}
 
.policy-card-desc {
  font-size: 0.9rem;
  line-height: 1.6;
  color: #444;
  font-weight: 400;
  flex-grow: 1;
}
 
.policy-card-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  width: 100%;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

.policy-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}
 
.policy-card-title {
  margin-left: 0;
  word-break: break-word;
  color: #000000;
}

.document-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #f0f4ff;
  border-radius: 50%;
  color: #4f6cff;
  cursor: pointer;
  transition: all 0.2s ease;
}
 
.document-icon:hover {
  background: #e0e7ff;
  transform: translateY(-2px);
}

/* .acknowledge-btn {
  height: 28px !important;
  font-size: 0.95rem !important;
  min-width: 90px;
  border-radius: 6px !important;
  padding: 0 12px;
  font-weight: 600 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: #4f6cff;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
 
.acknowledge-btn.acknowledged {
  background: #22a722 !important;
  color: #fff !important;
  opacity: 1;
  cursor: default;
  box-shadow: 0 2px 8px rgba(34, 167, 34, 0.3);
}
 
.acknowledge-btn.acknowledged::before {
  content: "✓ ";
  margin-right: 4px;
  font-weight: bold;
}
 
.acknowledge-btn:hover:not(.acknowledged) {
  background: #4441d6 !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.3);
}

/* View Reports Button */
.view-reports-btn {
  height: 28px !important;
  font-size: 0.9rem !important;
  min-width: 100px;
  border-radius: 6px !important;
  padding: 0 12px;
  font-weight: 600 !important;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid #4f6cff;
  background: #fff;
  color: #4f6cff;
  cursor: pointer;
  transition: all 0.2s;
}

.view-reports-btn:hover {
  background: #4f6cff;
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.3);
}

.view-reports-btn-list {
  padding: 6px 12px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 6px;
  border: 1.5px solid #4f6cff;
  background: #fff;
  color: #4f6cff;
  cursor: pointer;
  transition: all 0.2s;
}

.view-reports-btn-list:hover {
  background: #4f6cff;
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.3);
}

/* List View Styles */
.policy-list-container {
  width: 100%;
  margin-top: 20px;
  background: transparent;
  background-color: transparent;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid #42464f;
}

.policy-list-header {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 2.5fr 1.2fr 1.5fr;
  gap: 20px;
  padding: 20px 24px;
  border-bottom: 2px solid #45484e;
  font-weight: 700;
  font-size: 0.9rem;
  color: #000;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.list-header-item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  color: #000 !important;
  font-weight: bold !important;
}

.list-header-item:last-child {
  justify-content: center;
}

.policy-list {
  background: transparent;
  background-color: transparent;
}

.policy-list-item {
  border-bottom: 1px solid #000000;
}

.policy-list-item:last-child {
  border-bottom: none;
}

.list-item-content {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 2.5fr 1.2fr 1.5fr;
  gap: 18px;
  padding: 18px 18px;
  align-items: center;
  font-size: 0.85rem;
}

.list-item-content .policy-title,
.list-item-content .category-badge,
.list-item-content .type-badge,
.list-item-content .description-text,
.list-item-content .status-badge,
.list-item-content .policy-actions {
  font-size: 0.85rem;
}

.policy-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.policy-icon-list {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #e8edfa 0%, #d0d9f7 100%);
  border-radius: 12px;
  color: #4f6cff;
  font-size: 1.1rem;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(79, 108, 255, 0.15);
}

.policy-name-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.policy-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1.2;
}

.policy-id {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 500;
}

.policy-category-cell {
  display: flex;
  align-items: center;
}

.category-text {
  color: #000;
  font-size: 0.9rem;
  font-weight: 500;
}

.policy-type-cell {
  display: flex;
  align-items: center;
}

.type-text {
  color: #000;
  font-size: 0.9rem;
  font-weight: 500;
}

.policy-description-cell {
  display: flex;
  align-items: center;
}

.description-text {
  font-size: 0.9rem;
  color: #64748b;
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.policy-status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.policy-actions-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.list-action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* .acknowledge-btn-list {
  padding: 6px 12px;
  border-radius: 6px;
  border: none;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  background: #4f6cff;
  color: #fff;
  transition: all 0.2s ease;
  min-width: 80px;
  position: relative;
}

.acknowledge-btn-list.acknowledged {
  background: #22a722;
  color: #fff;
  cursor: default;
  box-shadow: 0 2px 8px rgba(34, 167, 34, 0.3);
}

.acknowledge-btn-list.acknowledged::before {
  content: "✓ ";
  margin-right: 4px;
  font-weight: bold;
}

.acknowledge-btn-list:hover:not(.acknowledged) {
  background: #3a57e8;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.3);
} */

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  background: linear-gradient(135deg, #f0f4ff 0%, #e0e7ff 100%);
  color: #4f6cff;
  border: 1px solid #c7d0f0;
}

.action-btn:hover {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 108, 255, 0.2);
}

.action-btn i {
  font-size: 0.9rem;
}

/* Switch and slider styles now use global styles from main.css */

/* Modal styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
 
.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 700px;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 5px 30px rgba(0, 0, 0, 0.15);
}
 
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  background: white;
  z-index: 2;
}
 
.modal-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.4rem;
}
 
.close-btn {
  font-size: 1.8rem;
  font-weight: bold;
  color: #666;
  cursor: pointer;
  transition: color 0.2s;
}
 
.close-btn:hover {
  color: #e53935;
}
 
.modal-body {
  padding: 24px;
}
 
.modal-loading, .modal-error {
  padding: 24px;
  text-align: center;
  color: #666;
}
 
.detail-row {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
}
 
.detail-label {
  font-weight: 600;
  width: 140px;
  color: #555;
}
 
.detail-value {
  flex: 1;
  min-width: 200px;
}
 
.doc-link {
  color: #4f6cff;
  text-decoration: none;
  font-weight: 600;
}
 
.doc-link:hover {
  text-decoration: underline;
}
 
/* Subpolicies section */
.subpolicies-section {
  margin-top: 24px;
  border-top: 1px solid #eee;
  padding-top: 16px;
}
 
.subpolicies-section h4 {
  font-size: 1.2rem;
  margin-bottom: 16px;
  color: #2c3e50;
}
 
.subpolicy-item {
  background: #f8f9fd;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  border-left: 3px solid #4f6cff;
}
 
.subpolicy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
 
.subpolicy-name {
  font-weight: 600;
  font-size: 1rem;
  color: #2c3e50;
}
 
.subpolicy-status {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}
 
.subpolicy-status.approved {
  color: #22a722;
  background: #e8f7ee;
}
 
.subpolicy-status.inactive, .subpolicy-status.rejected {
  color: #e53935;
  background: #fbeaea;
}
 
.subpolicy-status.under.review {
  color: #f5a623;
  background: #fff5e6;
}
 
.subpolicy-detail {
  margin-bottom: 6px;
  font-size: 0.9rem;
}
 
.subpolicy-label {
  font-weight: 600;
  color: #555;
  margin-right: 6px;
}
 
.no-subpolicies {
  margin-top: 16px;
  color: #666;
  font-style: italic;
  text-align: center;
}

/* Summary Section */
.summary-section {
  margin-bottom: 32px;
}

.summary-section-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 20px 0;
  text-align: center;
  letter-spacing: -0.5px;
}

.summary-cards {
  display: flex;
  width: 100%;
  max-width: 300px;
  margin: 0;
}

.summary-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  background: white;
  border-radius: 0;
  padding: 12px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  text-align: left;
  min-width: 150px;
  min-height: 60px;
  box-shadow: none;
  transition: border-bottom 0.3s ease, background 0.3s ease;
  position: relative;
  cursor: pointer;
  flex: 1;
  border: none;
  border-bottom: none;
}

.summary-card.active-policy {
  background: transparent !important;
  background-color: transparent !important;
  border-bottom: 3px solid #4f6cff !important;
  border-radius: 0;
}

.summary-card.active-policy:hover {
  background: transparent !important;
  background-color: transparent !important;
  border-bottom: 3px solid #4f6cff !important;
}

/* Colorblindness support for summary card active border */
[data-colorblind="protanopia"] .summary-card.active-policy,
[data-colorblind="deuteranopia"] .summary-card.active-policy {
  border-bottom-color: var(--cb-blue-4f6cff, #4f6cff) !important;
}
[data-colorblind="protanopia"] .summary-card.active-policy:hover,
[data-colorblind="deuteranopia"] .summary-card.active-policy:hover {
  border-bottom-color: var(--cb-blue-4f6cff, #4f6cff) !important;
}
[data-colorblind="tritanopia"] .summary-card.active-policy {
  border-bottom-color: var(--cb-blue-4f6cff, #7c3aed) !important;
}
[data-colorblind="tritanopia"] .summary-card.active-policy:hover {
  border-bottom-color: var(--cb-blue-4f6cff, #7c3aed) !important;
}

.summary-card.inactive-policy {
  background: transparent;
  background-color: transparent;
  border-radius: 0;
  border-bottom: none;
}

.summary-card.inactive-policy:hover {
  border-color: rgba(245, 166, 35, 0.4);
  box-shadow: 0 8px 30px rgba(245, 166, 35, 0.25);
}

.summary-card.framework-status-card {
  background: linear-gradient(135deg, #f0f4ff 60%, #f2f2f7 100%);
}

.summary-card.total-policy {
  background: linear-gradient(135deg, #f8f9fa 60%, #f2f2f7 100%);
}

.summary-card-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  width: 100%;
  height: 100%;
  text-align: left;
  padding: 8px 0;
  gap: 4px;
}

.summary-label {
  font-size: 0.75rem !important;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 3px;
  letter-spacing: 0.2px;
  white-space: nowrap;
  overflow: visible;
  text-overflow: clip;
}

.summary-value {
  display: block;
  font-size: 0.6rem;
  font-weight: 300;
  margin-top: 0;
  color: #222;
  text-shadow: none;
  text-align: left!important;
}

.summary-icon-wrapper {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  font-size: 1.4rem;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.active-policy .summary-icon-wrapper {
  background: #e6f7ff;
  color: #4f6cff;
}

/* Colorblindness support for summary icon wrapper */
[data-colorblind="protanopia"] .active-policy .summary-icon-wrapper,
[data-colorblind="deuteranopia"] .active-policy .summary-icon-wrapper {
  background: var(--cb-primary-light, #e6f7ff);
  color: var(--cb-blue-4f6cff, #4f6cff);
}
[data-colorblind="tritanopia"] .active-policy .summary-icon-wrapper {
  background: var(--cb-primary-light, #f3e8ff);
  color: var(--cb-blue-4f6cff, #7c3aed);
}

.inactive-policy .summary-icon-wrapper {
  background: #fff5e6;
  color: #f5a623;
}

.framework-status-card .summary-icon-wrapper {
  background: #f0f4ff;
  color: #4f6cff;
}

.total-policy .summary-icon-wrapper {
  background: #f8f9fa;
  color: #6c757d;
}

.framework-status {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.framework-status.active {
  color: #22a722;
}

.framework-status.inactive {
  color: #e53935;
}

.summary-card:hover .summary-icon-wrapper {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}

.summary-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(79,108,255,0.15);
}

/* Responsive Design */
@media (max-width: 1400px) {
  .policy-list-header,
  .list-item-content {
    grid-template-columns: 1.8fr 1fr 0.8fr 2fr 1fr 1.2fr;
    gap: 16px;
  }
  
  .policy-card-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }
}

@media (max-width: 1200px) {
  .policy-list-header,
  .list-item-content {
    grid-template-columns: 2fr 1fr 0.8fr 1.5fr 1fr 1fr;
    gap: 12px;
  }
  
  .policy-list-container {
    margin-left: -20px;
    margin-right: -20px;
    border-radius: 0;
  }
  
  .policy-card-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
  }
}


@media (max-width: 800px) {
  .summary-cards {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .summary-card {
    padding: 12px 10px;
    min-height: 80px;
  }
  
  .summary-section-title {
    font-size: 1.2rem;
    margin-bottom: 16px;
  }
  
  .policy-list-header {
    display: none;
  }
  
  .list-item-content {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 16px;
  }
  
  .policy-name-cell,
  .policy-category-cell,
  .policy-type-cell,
  .policy-description-cell,
  .policy-status-cell,
  .policy-actions-cell {
    width: 100%;
    justify-content: flex-start;
  }
  
  .policy-list-item:hover {
    transform: none;
    box-shadow: none;
  }
  
  .policy-card-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 0 4px;
  }
  
  .framework-policies-container {
    padding: 20px;
  }
  
  .view-toggle-controls {
    margin-left: 0;
    margin-top: 10px;
  }
  
  .top-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
}

.policy-page-skeleton.policy-fwp-skeleton {
  padding: 8px 0 24px;
}
.policy-fwp-skeleton .policy-skeleton-summary {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}
.policy-fwp-skeleton .policy-skeleton-card {
  height: 88px;
  border-radius: 12px;
  background: linear-gradient(90deg, #eef2f7 0%, #f8fafc 50%, #eef2f7 100%);
  background-size: 200% 100%;
  animation: policyFwpSkeletonPulse 1.35s ease infinite;
}
.policy-fwp-skeleton .policy-skeleton-table {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e8ecf2;
}
.policy-fwp-skeleton .policy-skeleton-row {
  height: 48px;
  border-bottom: 1px solid #eef2f7;
  background: linear-gradient(90deg, #f4f6fa 0%, #fafbfd 50%, #f4f6fa 100%);
  background-size: 200% 100%;
  animation: policyFwpSkeletonPulse 1.35s ease infinite;
}
.policy-fwp-skeleton .policy-skeleton-row:last-child {
  border-bottom: none;
}
@keyframes policyFwpSkeletonPulse {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}
</style>