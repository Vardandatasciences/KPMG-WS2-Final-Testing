<template>
  <div class="page">
    <div>

    <!-- Add Plan Type Modal -->
    <div v-if="showAddPlanTypeModal" class="modal-overlay" @click="closeAddPlanTypeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">Add New Plan Type</h3>
          <button class="modal-close" @click="closeAddPlanTypeModal">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label for="new-plan-type" class="form-label">
              Plan Type Name <span class="required-asterisk">*</span>
            </label>
            <input
              id="new-plan-type"
              type="text"
              class="form-input"
              v-model="newPlanTypeValue"
              placeholder="e.g., CRP, ERP, etc."
              @keyup.enter="saveNewPlanType"
              ref="newPlanTypeInput"
            />
            <p class="form-hint">Enter a unique plan type name (e.g., Crisis Recovery Plan, Emergency Response Plan)</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn--outline" @click="closeAddPlanTypeModal">Cancel</button>
          <button 
            class="btn btn--primary" 
            @click="saveNewPlanType"
            :disabled="!newPlanTypeValue.trim() || isSavingPlanType"
          >
            <span v-if="isSavingPlanType">Saving...</span>
            <span v-else>Save Plan Type</span>
          </button>
        </div>
      </div>
    </div>

    <div class="main-layout">
      <!-- Left Column - Form -->
      <div class="form-column">
        <div class="card">
          <div class="card-content space-y-6">
            <h2 class="text-lg font-semibold">Plan Data</h2>
            <!-- Unified Form -->
            <div class="unified-form">
              <div class="form-row">
                <div>
                  <label for="strategy-name" class="label flex items-center gap-2">
                    <span>Strategy Name *</span>
                    <div class="bcp-data-type-circle-toggle-wrapper">
                      <div class="bcp-data-type-circle-toggle">
                        <div 
                          class="bcp-circle-option bcp-personal-circle" 
                          :class="{ active: getPlanDataType('strategyName') === 'personal' }"
                          @click="setPlanDataType('strategyName', 'personal')"
                          title="Personal Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                        <div 
                          class="bcp-circle-option bcp-confidential-circle" 
                          :class="{ active: getPlanDataType('strategyName') === 'confidential' }"
                          @click="setPlanDataType('strategyName', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                        <div 
                          class="bcp-circle-option bcp-regular-circle" 
                          :class="{ active: getPlanDataType('strategyName') === 'regular' }"
                          @click="setPlanDataType('strategyName', 'regular')"
                          title="Regular Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </label>
                  <input
                    id="strategy-name"
                    class="input"
                    placeholder="e.g., Payments Resilience 2025"
                    v-model="strategyName"
                  />
                </div>
              </div>

              <div class="form-row">
                <div>
                  <label for="plan-name" class="label flex items-center gap-2">
                    <span>Plan Name *</span>
                    <div class="bcp-data-type-circle-toggle-wrapper">
                      <div class="bcp-data-type-circle-toggle">
                        <div 
                          class="bcp-circle-option bcp-personal-circle" 
                          :class="{ active: getPlanDataType('planName') === 'personal' }"
                          @click="setPlanDataType('planName', 'personal')"
                          title="Personal Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                        <div 
                          class="bcp-circle-option bcp-confidential-circle" 
                          :class="{ active: getPlanDataType('planName') === 'confidential' }"
                          @click="setPlanDataType('planName', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                        <div 
                          class="bcp-circle-option bcp-regular-circle" 
                          :class="{ active: getPlanDataType('planName') === 'regular' }"
                          @click="setPlanDataType('planName', 'regular')"
                          title="Regular Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </label>
                  <label for="plan-type-select" class="label">Plan Type *</label>
                  <div class="custom-dropdown-wrapper">
                    <div 
                      class="custom-dropdown"
                      :class="{ 'is-open': isPlanTypeDropdownOpen, 'has-value': currentDoc.planType }"
                      @click="togglePlanTypeDropdown"
                      @blur="closePlanTypeDropdown"
                      tabindex="0"
                    >
                      <div class="dropdown-selected">
                        <span v-if="currentDoc.planType" class="selected-value">{{ currentDoc.planType }}</span>
                        <span v-else class="placeholder">Select plan type</span>
                        <svg 
                          class="dropdown-arrow" 
                          :class="{ 'rotated': isPlanTypeDropdownOpen }"
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                        </svg>
                      </div>
                      <Transition name="dropdown">
                        <div v-if="isPlanTypeDropdownOpen" class="dropdown-menu">
                          <div 
                            v-for="pt in planTypes" 
                            :key="pt.id" 
                            class="dropdown-item"
                            :class="{ 'is-selected': currentDoc.planType === pt.value }"
                            @click.stop="selectPlanType(pt.value)"
                          >
                            <span class="item-text">{{ pt.value }}</span>
                            <svg 
                              v-if="currentDoc.planType === pt.value"
                              class="check-icon"
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                            >
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                          </div>
                          <div class="dropdown-divider"></div>
                          <div 
                            class="dropdown-item add-new-item"
                            @click.stop="openAddPlanTypeModal"
                          >
                            <svg class="add-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                            </svg>
                            <span class="item-text">Add New Plan Type</span>
                          </div>
                        </div>
                      </Transition>
                    </div>
                  </div>
                </div>
                <div>
                  <label for="plan-name" class="label">Plan Name *</label>
                  <input
                    id="plan-name"
                    class="input"
                    placeholder="e.g., Cloud BCP"
                    v-model="currentDoc.planName"
                  />
                </div>
              </div>

              <div class="form-row">
                <div>
                  <label for="scope" class="label flex items-center gap-2">
                    <span>Scope</span>
                    <div class="bcp-data-type-circle-toggle-wrapper">
                      <div class="bcp-data-type-circle-toggle">
                        <div 
                          class="bcp-circle-option bcp-personal-circle" 
                          :class="{ active: getPlanDataType('scope') === 'personal' }"
                          @click="setPlanDataType('scope', 'personal')"
                          title="Personal Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                        <div 
                          class="bcp-circle-option bcp-confidential-circle" 
                          :class="{ active: getPlanDataType('scope') === 'confidential' }"
                          @click="setPlanDataType('scope', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                        <div 
                          class="bcp-circle-option bcp-regular-circle" 
                          :class="{ active: getPlanDataType('scope') === 'regular' }"
                          @click="setPlanDataType('scope', 'regular')"
                          title="Regular Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </label>
                  <select
                    id="scope"
                    class="select"
                    v-model="currentDoc.scope"
                  >
                    <option value="">Select scope</option>
                    <option v-for="scope in scopeOptions" :key="scope.id" :value="scope.value">
                      {{ scope.value }}
                    </option>
                  </select>
                </div>
                <div>
                  <label for="criticality" class="label flex items-center gap-2">
                    <span>Criticality *</span>
                    <div class="bcp-data-type-circle-toggle-wrapper">
                      <div class="bcp-data-type-circle-toggle">
                        <div 
                          class="bcp-circle-option bcp-personal-circle" 
                          :class="{ active: getPlanDataType('criticality') === 'personal' }"
                          @click="setPlanDataType('criticality', 'personal')"
                          title="Personal Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                        <div 
                          class="bcp-circle-option bcp-confidential-circle" 
                          :class="{ active: getPlanDataType('criticality') === 'confidential' }"
                          @click="setPlanDataType('criticality', 'confidential')"
                          title="Confidential Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                        <div 
                          class="bcp-circle-option bcp-regular-circle" 
                          :class="{ active: getPlanDataType('criticality') === 'regular' }"
                          @click="setPlanDataType('criticality', 'regular')"
                          title="Regular Data"
                        >
                          <div class="bcp-circle-inner"></div>
                        </div>
                      </div>
                    </div>
                  </label>
                  <select
                    id="criticality"
                    class="select"
                    v-model="currentDoc.criticality"
                  >
                    <option value="">Select criticality</option>
                    <option value="LOW">LOW</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                  </select>
                  <label for="scope-select" class="label">Scope</label>
                  <div class="custom-dropdown-wrapper">
                    <div 
                      class="custom-dropdown"
                      :class="{ 'is-open': isScopeDropdownOpen, 'has-value': currentDoc.scope }"
                      @click="toggleScopeDropdown"
                      @blur="closeScopeDropdown"
                      tabindex="0"
                    >
                      <div class="dropdown-selected">
                        <span v-if="currentDoc.scope" class="selected-value">{{ currentDoc.scope }}</span>
                        <span v-else class="placeholder">Select scope</span>
                        <svg 
                          class="dropdown-arrow" 
                          :class="{ 'rotated': isScopeDropdownOpen }"
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                        </svg>
                      </div>
                      <Transition name="dropdown">
                        <div v-if="isScopeDropdownOpen" class="dropdown-menu">
                          <div 
                            v-for="scope in scopeOptions" 
                            :key="scope.id" 
                            class="dropdown-item"
                            :class="{ 'is-selected': currentDoc.scope === scope.value }"
                            @click.stop="selectScope(scope.value)"
                          >
                            <span class="item-text">{{ scope.value }}</span>
                            <svg 
                              v-if="currentDoc.scope === scope.value"
                              class="check-icon"
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                            >
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                          </div>
                        </div>
                      </Transition>
                    </div>
                  </div>
                </div>
                <div>
                  <label for="criticality-select" class="label">Criticality *</label>
                  <div class="custom-dropdown-wrapper">
                    <div 
                      class="custom-dropdown"
                      :class="{ 'is-open': isCriticalityDropdownOpen, 'has-value': currentDoc.criticality }"
                      @click="toggleCriticalityDropdown"
                      @blur="closeCriticalityDropdown"
                      tabindex="0"
                    >
                      <div class="dropdown-selected">
                        <span v-if="currentDoc.criticality" class="selected-value">{{ currentDoc.criticality }}</span>
                        <span v-else class="placeholder">Select criticality</span>
                        <svg 
                          class="dropdown-arrow" 
                          :class="{ 'rotated': isCriticalityDropdownOpen }"
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                        </svg>
                      </div>
                      <Transition name="dropdown">
                        <div v-if="isCriticalityDropdownOpen" class="dropdown-menu">
                          <div 
                            v-for="option in criticalityOptions" 
                            :key="option.value" 
                            class="dropdown-item"
                            :class="{ 'is-selected': currentDoc.criticality === option.value }"
                            @click.stop="selectCriticality(option.value)"
                          >
                            <span class="item-text">{{ option.label }}</span>
                            <svg 
                              v-if="currentDoc.criticality === option.value"
                              class="check-icon"
                              fill="none" 
                              stroke="currentColor" 
                              viewBox="0 0 24 24"
                            >
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                            </svg>
                          </div>
                        </div>
                      </Transition>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <label for="file-upload" class="label flex items-center gap-2">
                  <span>File *</span>
                  <div class="bcp-data-type-circle-toggle-wrapper">
                    <div class="bcp-data-type-circle-toggle">
                      <div 
                        class="bcp-circle-option bcp-personal-circle" 
                        :class="{ active: getPlanDataType('file') === 'personal' }"
                        @click="setPlanDataType('file', 'personal')"
                        title="Personal Data"
                      >
                        <div class="bcp-circle-inner"></div>
                      </div>
                      <div 
                        class="bcp-circle-option bcp-confidential-circle" 
                        :class="{ active: getPlanDataType('file') === 'confidential' }"
                        @click="setPlanDataType('file', 'confidential')"
                        title="Confidential Data"
                      >
                        <div class="bcp-circle-inner"></div>
                      </div>
                      <div 
                        class="bcp-circle-option bcp-regular-circle" 
                        :class="{ active: getPlanDataType('file') === 'regular' }"
                        @click="setPlanDataType('file', 'regular')"
                        title="Regular Data"
                      >
                        <div class="bcp-circle-inner"></div>
                      </div>
                    </div>
                  </div>
                </label>
                <div class="file-upload-area" @click="triggerFileUpload">
                  <svg class="h-6 w-6 text-muted-foreground mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                  </svg>
                  <p class="text-sm text-muted-foreground mb-2">
                    {{ selectedFile ? selectedFile.name : 'Choose File' }}
                  </p>
                  <input
                    ref="fileInput"
                    id="file-upload"
                    type="file"
                    accept=".pdf,.doc,.docx"
                    class="hidden"
                    @change="handleFileSelect"
                  />
                  <button type="button" class="btn btn--outline btn--sm">Choose File</button>
                </div>
              </div>

              <div class="mt-4">
                <button @click="addDocument" class="btn btn--primary w-full">
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                  </svg>
                  Add Document
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column - Documents -->
      <div class="documents-column">
        <div class="card">
          <div class="card-content">
            <h2 class="text-lg font-semibold mb-4">Documents</h2>
            <div v-if="documents.length > 0" class="documents-cards">
              <div v-for="(doc, index) in documents" :key="index" class="document-card">
                <div class="document-header">
                  <h3 class="document-title">{{ doc.planName }}</h3>
                  <div class="document-actions">
                    <button @click="editDocument(index)" class="btn btn--outline btn--sm" title="Edit">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                    </button>
                    <button @click="removeDocument(index)" class="btn btn--outline btn--sm text-destructive" title="Remove">
                      <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                    </button>
                  </div>
                </div>
                <div class="document-details">
                  <div class="detail-row">
                    <span class="detail-label">Type:</span>
                    <span class="detail-value">{{ doc.planType || 'N/A' }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">File Name:</span>
                    <span class="detail-value">{{ doc.fileName }}</span>
                  </div>
                  <div class="detail-row">
                    <span class="detail-label">Criticality:</span>
                    <span class="detail-value">
                      {{ doc.criticality }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center text-muted-foreground py-8">
              No documents added yet
            </div>
          </div>
        </div>

        <div class="mt-6 flex gap-4">
          <button @click="loadMockData" class="btn btn--outline flex-1">
            <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
            </svg>
            Load Data
          </button>
          <button @click="submitDocuments" class="btn btn--primary flex-1">
            Submit
          </button>
        </div>
      </div>
    </div>
    </div>
  </div>

  <!-- Popup Modal -->
  <PopupModal />
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import api from '../../services/api_bcp.js'
import PopupModal from '@/popup/PopupModal.vue'
import { PopupService } from '@/popup/popupService'
import { useNotifications } from '@/composables/useNotifications'
import notificationService from '@/services/notificationService'
import loggingService from '@/services/loggingService'

export default {
  name: 'VendorUpload',
  components: {
    PopupModal
  },
  setup() {
    const { showSuccess, showError, showWarning, showInfo } = useNotifications()

    const planTypes = ref([])
    const isPlanTypeDropdownOpen = ref(false)
    const isScopeDropdownOpen = ref(false)
    const isCriticalityDropdownOpen = ref(false)
    const showAddPlanTypeModal = ref(false)
    const newPlanTypeValue = ref('')
    const isSavingPlanType = ref(false)
    const strategyName = ref('')
    const selectedFile = ref(null)
    const fileInput = ref(null)
    const scopeOptions = ref([])
    const newPlanTypeInput = ref(null)
    
    // Criticality options
    const criticalityOptions = [
      { value: 'LOW', label: 'LOW' },
      { value: 'MEDIUM', label: 'MEDIUM' },
      { value: 'HIGH', label: 'HIGH' },
      { value: 'CRITICAL', label: 'CRITICAL' }
    ]
    
    const currentDoc = reactive({
      planType: '',
      planName: '',
      criticality: '',
      scope: ''
    })

    const documents = ref([])

    // Data type classification for plan fields
    const planFieldDataTypes = reactive({
      strategyName: 'regular',
      planName: 'regular',
      scope: 'regular',
      criticality: 'regular',
      file: 'confidential'
    })

    // Method to set data type for a plan field
    const setPlanDataType = (fieldName, type) => {
      if (planFieldDataTypes.hasOwnProperty(fieldName)) {
        planFieldDataTypes[fieldName] = type
        console.log(`Data type selected for plan field ${fieldName}:`, type)
      }
    }

    // Get data type for a plan field
    const getPlanDataType = (fieldName) => {
      return planFieldDataTypes[fieldName] || 'regular'
    }

    // Helper function to build data_inventory JSON for plan
    const buildPlanDataInventory = () => {
      const fieldLabelMap = {
        strategyName: 'Strategy Name',
        planName: 'Plan Name',
        scope: 'Scope',
        criticality: 'Criticality',
        file: 'File'
      }

      const dataInventory = {}
      
      // Build flat structure: {"Field Label": "data_type"}
      for (const [fieldName, dataType] of Object.entries(planFieldDataTypes)) {
        if (fieldLabelMap[fieldName]) {
          const fieldLabel = fieldLabelMap[fieldName]
          dataInventory[fieldLabel] = dataType
        }
      }
      
      console.log('📋 Plan Data Inventory JSON:', JSON.stringify(dataInventory, null, 2))
      return dataInventory
    }
    
    const fetchPlanTypes = async () => {
      try {
        console.log('Fetching plan types from API')
        const response = await api.planTypes.list()
        console.log('Plan types API Response:', response)
        
        // The response interceptor should have unwrapped the data
        planTypes.value = response.data?.plan_types || []
        console.log('Plan types loaded:', planTypes.value)
        
        // Don't auto-select - let user choose from dropdown
      } catch (error) {
        console.error('Error fetching plan types:', error)
        console.error('Error details:', error.message)
        planTypes.value = []
      }
    }

    const togglePlanTypeDropdown = () => {
      isPlanTypeDropdownOpen.value = !isPlanTypeDropdownOpen.value
    }

    const closePlanTypeDropdown = () => {
      setTimeout(() => {
        isPlanTypeDropdownOpen.value = false
      }, 200)
    }

    const selectPlanType = (value) => {
      currentDoc.planType = value
      isPlanTypeDropdownOpen.value = false
    }

    const toggleScopeDropdown = () => {
      isScopeDropdownOpen.value = !isScopeDropdownOpen.value
    }

    const closeScopeDropdown = () => {
      setTimeout(() => {
        isScopeDropdownOpen.value = false
      }, 200)
    }

    const selectScope = (value) => {
      currentDoc.scope = value
      isScopeDropdownOpen.value = false
    }

    const toggleCriticalityDropdown = () => {
      isCriticalityDropdownOpen.value = !isCriticalityDropdownOpen.value
    }

    const closeCriticalityDropdown = () => {
      setTimeout(() => {
        isCriticalityDropdownOpen.value = false
      }, 200)
    }

    const selectCriticality = (value) => {
      currentDoc.criticality = value
      isCriticalityDropdownOpen.value = false
    }

    const openAddPlanTypeModal = () => {
      showAddPlanTypeModal.value = true
      newPlanTypeValue.value = ''
      isPlanTypeDropdownOpen.value = false
      // Focus input after modal opens
      setTimeout(() => {
        if (newPlanTypeInput.value) {
          newPlanTypeInput.value.focus()
        }
      }, 100)
    }

    const closeAddPlanTypeModal = () => {
      showAddPlanTypeModal.value = false
      newPlanTypeValue.value = ''
    }

    const saveNewPlanType = async () => {
      const trimmedValue = newPlanTypeValue.value.trim()
      
      if (!trimmedValue) {
        PopupService.warning('Please enter a plan type name', 'Validation Error')
        return
      }

      // Check if plan type already exists
      if (planTypes.value.some(pt => pt.value.toUpperCase() === trimmedValue.toUpperCase())) {
        PopupService.warning(`Plan type "${trimmedValue}" already exists`, 'Duplicate Plan Type')
        return
      }

      isSavingPlanType.value = true
      try {
        const response = await api.planTypes.create({ value: trimmedValue })
        console.log('Plan type created:', response)
        
        // Refresh plan types list
        await fetchPlanTypes()
        
        // Select the newly created plan type
        currentDoc.planType = trimmedValue
        
        // Close modal
        closeAddPlanTypeModal()
        
        PopupService.success(`Plan type "${trimmedValue}" has been added successfully`, 'Plan Type Added')
        await notificationService.createBCPSuccessNotification('plan_type_added', {
          plan_type: trimmedValue
        })
      } catch (error) {
        console.error('Error creating plan type:', error)
        PopupService.error(
          error.response?.data?.message || `Failed to add plan type "${trimmedValue}"`,
          'Error'
        )
      } finally {
        isSavingPlanType.value = false
      }
    }

    const fetchScopeOptions = async () => {
      try {
        console.log('Fetching scope options from: http://localhost:8000/api/bcpdrp/dropdowns/?source=plan_scope')
        const response = await api.dropdowns({ source: 'plan_scope' })
        console.log('API Response:', response)
        console.log('Response data:', response.data)
        console.log('Response data type:', typeof response.data)
        console.log('Response data keys:', Object.keys(response.data || {}))
        
        // The response interceptor should have unwrapped the data
        // The dropdown options are in response.data.data
        scopeOptions.value = response.data?.data || []
        console.log('Scope options loaded:', scopeOptions.value)
        console.log('Scope options length:', scopeOptions.value.length)
      } catch (error) {
        console.error('Error fetching scope options:', error)
        console.error('Error details:', error.message)
        // No fallback - only show real data from database
        scopeOptions.value = []
      }
    }

    const triggerFileUpload = () => {
      fileInput.value.click()
    }

    const handleFileSelect = async (event) => {
      const file = event.target.files[0]
      if (file) {
        // Validate file type
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if (!allowedTypes.includes(file.type)) {
          PopupService.warning('Please select a valid file (PDF, DOC, or DOCX)', 'Invalid File Type')
          // Create notification
          await notificationService.createPlanUploadNotification('invalid_file', {})
          return
        }
        
        // Validate file size (max 10MB)
        const maxSize = 10 * 1024 * 1024 // 10MB
        if (file.size > maxSize) {
          PopupService.warning('File size must be less than 10MB', 'File Too Large')
          // Create notification
          await notificationService.createPlanUploadNotification('file_too_large', {})
          return
        }
        
        selectedFile.value = file
      }
    }


    const addDocument = () => {
      if (!currentDoc.planType || !currentDoc.planName || !currentDoc.criticality || !selectedFile.value) {
        PopupService.warning('Please fill in all required fields (Plan Type, Plan Name, Criticality) and select a file', 'Missing Information')
        return
      }

      console.log('Adding document with file:', {
        fileName: selectedFile.value.name,
        fileType: selectedFile.value.type,
        fileSize: selectedFile.value.size,
        fileObject: selectedFile.value,
        planType: currentDoc.planType
      })

      documents.value.push({
        ...currentDoc,
        file: selectedFile.value,
        fileName: selectedFile.value.name,
        fileSize: selectedFile.value.size
      })

      // Reset form
      currentDoc.planType = ''
      currentDoc.planName = ''
      currentDoc.criticality = ''
      currentDoc.scope = ''
      selectedFile.value = null
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const editDocument = (index) => {
      const doc = documents.value[index]
      currentDoc.planType = doc.planType || ''
      currentDoc.planName = doc.planName
      currentDoc.criticality = doc.criticality
      currentDoc.scope = doc.scope
      selectedFile.value = doc.file
      
      // Remove from documents list
      documents.value.splice(index, 1)
    }

    const removeDocument = (index) => {
      PopupService.confirm(
        'Are you sure you want to remove this document?',
        'Confirm Removal',
        () => {
          documents.value.splice(index, 1)
        }
      )
    }


    const submitDocuments = async () => {
      if (documents.value.length === 0) {
        PopupService.warning('Please add at least one document', 'No Documents')
        return
      }

      if (!strategyName.value.trim()) {
        PopupService.warning('Please enter a strategy name', 'Missing Strategy Name')
        return
      }

      try {
        // Create FormData for file upload
        const formData = new FormData()
        formData.append('strategyName', strategyName.value)
        
        // Add document metadata with data_inventory
        // Add document metadata with planType per document
        formData.append('documents', JSON.stringify(documents.value.map(doc => ({
          planType: doc.planType,
          planName: doc.planName,
          scope: doc.scope || '',
          criticality: doc.criticality,
          fileName: doc.fileName,
          data_inventory: buildPlanDataInventory()
        }))))
        
        // Add data_inventory for the strategy
        formData.append('data_inventory', JSON.stringify(buildPlanDataInventory()))
        
        // Add files
        console.log('Documents to upload:', documents.value)
        documents.value.forEach((doc, index) => {
          console.log(`Processing document ${index}:`, doc)
          if (doc.file) {
            formData.append(`file_${doc.fileName}`, doc.file)
            console.log(`Adding file: file_${doc.fileName} -> ${doc.file.name}`)
          } else {
            console.warn(`Document ${index} has no file:`, doc)
          }
        })

        console.log('Submitting documents to backend...')
        console.log('FormData contents:')
        for (let [key, value] of formData.entries()) {
          console.log(`${key}:`, value)
        }
        
        // Additional debugging for file objects
        console.log('Files in FormData:')
        documents.value.forEach((doc, index) => {
          console.log(`Document ${index}:`, {
            fileName: doc.fileName,
            hasFile: !!doc.file,
            fileType: doc.file?.type,
            fileSize: doc.file?.size,
            fileKey: `file_${doc.fileName}`
          })
        })
        
        const result = await api.vendorUpload(formData)
        console.log('Upload successful:', result)
        console.log('Result type:', typeof result)
        console.log('Result keys:', Object.keys(result || {}))
        
        // Handle different response structures
        let responseData = result
        
        // If we get the full Axios response object, extract the data
        if (result && result.data && typeof result.data === 'object') {
          responseData = result.data
          console.log('Extracted response data:', responseData)
        }
        
        console.log('Response data plans:', responseData.plans)
        console.log('Response data strategy_name:', responseData.strategy_name)
        
        if (responseData && responseData.plans && Array.isArray(responseData.plans)) {
          PopupService.success(`Documents submitted successfully! Created ${responseData.plans.length} plan(s) under strategy "${responseData.strategy_name}"`, 'Submission Successful')
          // Create notification
          await notificationService.createPlanUploadNotification('plan_uploaded', {
            plan_count: responseData.plans.length,
            strategy_name: responseData.strategy_name
          })
        } else {
          console.error('Unexpected response structure:', responseData)
          PopupService.success('Documents submitted successfully!', 'Submission Successful')
          // Create generic success notification
          await notificationService.createBCPSuccessNotification('plan_upload', {
            title: 'Plans Uploaded',
            message: 'Documents submitted successfully'
          })
        }
        
        // Reset everything
        strategyName.value = ''
        documents.value = []
        currentDoc.planType = ''
        currentDoc.planName = ''
        currentDoc.criticality = ''
        currentDoc.scope = ''
        selectedFile.value = null
        if (fileInput.value) {
          fileInput.value.value = ''
        }
      } catch (error) {
        console.error('Error submitting documents:', error)
        PopupService.error('Error submitting documents. Please try again.', 'Submission Failed')
        // Create error notification
        await notificationService.createPlanUploadNotification('plan_upload_failed', {
          error: error.message || 'Unknown error'
        })
      }
    }

    // Mock data functions
    const getBCPMockData = () => {
      return {
        strategyName: 'Financial Services Business Continuity Strategy',
        documents: [
          {
            planName: 'Core Banking Operations BCP',
            scope: 'Core banking systems, customer accounts, transaction processing',
            criticality: 'CRITICAL',
            fileName: 'Core_Banking_BCP_v2.1.pdf',
            file: createMockFile('Core_Banking_BCP_v2.1.pdf', 'application/pdf')
          },
          {
            planName: 'Customer Service Continuity BCP',
            scope: 'Call center operations, customer support systems, online banking',
            criticality: 'HIGH',
            fileName: 'Customer_Service_BCP_v1.8.pdf',
            file: createMockFile('Customer_Service_BCP_v1.8.pdf', 'application/pdf')
          },
          {
            planName: 'Regulatory Compliance BCP',
            scope: 'Regulatory reporting, compliance monitoring, audit trails',
            criticality: 'HIGH',
            fileName: 'Regulatory_Compliance_BCP_v3.0.pdf',
            file: createMockFile('Regulatory_Compliance_BCP_v3.0.pdf', 'application/pdf')
          }
        ]
      }
    }

    const getDRPMockData = () => {
      return {
        strategyName: 'IT Infrastructure Disaster Recovery Strategy',
        documents: [
          {
            planName: 'Primary Data Center DRP',
            scope: 'Main data center systems, servers, network infrastructure',
            criticality: 'CRITICAL',
            fileName: 'Primary_DC_DRP_v4.2.pdf',
            file: createMockFile('Primary_DC_DRP_v4.2.pdf', 'application/pdf')
          },
          {
            planName: 'Cloud Services Recovery DRP',
            scope: 'Cloud applications, SaaS services, cloud infrastructure',
            criticality: 'HIGH',
            fileName: 'Cloud_Recovery_DRP_v2.5.pdf',
            file: createMockFile('Cloud_Recovery_DRP_v2.5.pdf', 'application/pdf')
          },
          {
            planName: 'Network Infrastructure DRP',
            scope: 'Network connectivity, routers, switches, internet services',
            criticality: 'HIGH',
            fileName: 'Network_Infrastructure_DRP_v1.9.pdf',
            file: createMockFile('Network_Infrastructure_DRP_v1.9.pdf', 'application/pdf')
          }
        ]
      }
    }

    const createMockFile = (fileName, fileType) => {
      // Create a mock file object for testing
      const mockFile = new File(['Mock file content for ' + fileName], fileName, { type: fileType })
      return mockFile
    }

    const loadMockData = () => {
      if (documents.value.length > 0) {
        PopupService.confirm(
          'This will replace all existing documents. Continue?',
          'Replace Documents',
          () => {
            performLoadMockData()
          }
        )
      } else {
        performLoadMockData()
      }
    }

    const performLoadMockData = () => {
      // Use generic mock data structure with different plan types
      const availablePlanTypes = planTypes.value.length > 0 
        ? planTypes.value.map(pt => pt.value) 
        : ['BCP', 'DRP']
      
      let mockData
      // Create mock data with different plan types for variety
      mockData = {
        strategyName: 'Business Continuity Strategy',
        documents: [
          {
            planType: availablePlanTypes[0] || 'BCP',
            planName: `${availablePlanTypes[0] || 'BCP'} Plan 1`,
            scope: 'Core systems, operations, infrastructure',
            criticality: 'CRITICAL',
            fileName: `${availablePlanTypes[0] || 'BCP'}_Plan_1.pdf`,
            file: createMockFile(`${availablePlanTypes[0] || 'BCP'}_Plan_1.pdf`, 'application/pdf')
          },
          {
            planType: availablePlanTypes.length > 1 ? availablePlanTypes[1] : availablePlanTypes[0] || 'DRP',
            planName: `${availablePlanTypes.length > 1 ? availablePlanTypes[1] : availablePlanTypes[0] || 'DRP'} Plan 2`,
            scope: 'Supporting systems, services, applications',
            criticality: 'HIGH',
            fileName: `${availablePlanTypes.length > 1 ? availablePlanTypes[1] : availablePlanTypes[0] || 'DRP'}_Plan_2.pdf`,
            file: createMockFile(`${availablePlanTypes.length > 1 ? availablePlanTypes[1] : availablePlanTypes[0] || 'DRP'}_Plan_2.pdf`, 'application/pdf')
          }
        ]
      }

      // Load the mock data
      strategyName.value = mockData.strategyName
      documents.value = [...mockData.documents]
      
      PopupService.success(`Mock data loaded with ${mockData.documents.length} plans of different types. You can now review and modify the documents before submitting.`, 'Mock Data Loaded')
    }

    // Fetch plan types and scope options on component mount
    onMounted(async () => {
      await loggingService.logPageView('BCP', 'Vendor Upload')
      await fetchPlanTypes()
      await fetchScopeOptions()
    })

    return {
      planTypes,
      isPlanTypeDropdownOpen,
      isScopeDropdownOpen,
      isCriticalityDropdownOpen,
      showAddPlanTypeModal,
      newPlanTypeValue,
      isSavingPlanType,
      newPlanTypeInput,
      strategyName,
      currentDoc,
      documents,
      selectedFile,
      fileInput,
      scopeOptions,
      criticalityOptions,
      togglePlanTypeDropdown,
      closePlanTypeDropdown,
      selectPlanType,
      toggleScopeDropdown,
      closeScopeDropdown,
      selectScope,
      toggleCriticalityDropdown,
      closeCriticalityDropdown,
      selectCriticality,
      openAddPlanTypeModal,
      closeAddPlanTypeModal,
      saveNewPlanType,
      triggerFileUpload,
      handleFileSelect,
      addDocument,
      editDocument,
      removeDocument,
      submitDocuments,
      loadMockData,
      setPlanDataType,
      getPlanDataType,
      buildPlanDataInventory
    }
  }
}
</script>

<style scoped>
@import './VendorUpload.css';

/* Data Type Classification Toggle Styles */
.bcp-data-type-circle-toggle-wrapper {
  display: inline-flex !important;
  align-items: center !important;
  margin-left: 12px !important;
  padding: 4px 8px !important;
  background-color: white !important;
  border: 1px solid #e5e7eb !important;
  border-radius: 16px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
  visibility: visible !important;
  opacity: 1 !important;
  position: relative !important;
  z-index: 1 !important;
  flex-shrink: 0 !important;
}

.bcp-data-type-circle-toggle {
  display: flex !important;
  align-items: center !important;
  gap: 4px !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.bcp-circle-option {
  width: 14px !important;
  height: 14px !important;
  border-radius: 50% !important;
  border: 1.5px solid #d1d5db !important;
  background-color: white !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.3s ease !important;
  position: relative !important;
  visibility: visible !important;
  opacity: 1 !important;
  flex-shrink: 0 !important;
}

.bcp-circle-option:hover {
  transform: scale(1.2) !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12) !important;
}

.bcp-circle-inner {
  width: 0 !important;
  height: 0 !important;
  border-radius: 50% !important;
  transition: all 0.3s ease !important;
  background-color: transparent !important;
}

.bcp-circle-option.active .bcp-circle-inner {
  width: 9px !important;
  height: 9px !important;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.2) !important;
}

/* Personal Circle - Blue */
.bcp-circle-option.bcp-personal-circle {
  border: 1.5px solid #4f7cff !important;
}

.bcp-circle-option.bcp-personal-circle.active {
  border: 1.5px solid #4f7cff !important;
  background-color: rgba(79, 124, 255, 0.1) !important;
  box-shadow: 0 0 6px rgba(79, 124, 255, 0.2) !important;
}

.bcp-circle-option.bcp-personal-circle.active .bcp-circle-inner {
  background-color: #4f7cff !important;
  box-shadow: 0 0 4px rgba(79, 124, 255, 0.35) !important;
}

/* Confidential Circle - Red */
.bcp-circle-option.bcp-confidential-circle {
  border: 1.5px solid #e63946 !important;
}

.bcp-circle-option.bcp-confidential-circle.active {
  border: 1.5px solid #e63946 !important;
  background-color: rgba(230, 57, 70, 0.1) !important;
  box-shadow: 0 0 6px rgba(230, 57, 70, 0.2) !important;
}

.bcp-circle-option.bcp-confidential-circle.active .bcp-circle-inner {
  background-color: #e63946 !important;
  box-shadow: 0 0 4px rgba(230, 57, 70, 0.35) !important;
}

/* Regular Circle - Grey */
.bcp-circle-option.bcp-regular-circle {
  border: 1.5px solid #6c757d !important;
}

.bcp-circle-option.bcp-regular-circle.active {
  border: 1.5px solid #6c757d !important;
  background-color: rgba(108, 117, 125, 0.1) !important;
  box-shadow: 0 0 6px rgba(108, 117, 125, 0.2) !important;
}

.bcp-circle-option.bcp-regular-circle.active .bcp-circle-inner {
  background-color: #6c757d !important;
  box-shadow: 0 0 4px rgba(108, 117, 125, 0.35) !important;
}
</style>