<template>
  <div class="compliance-container">
    <div class="compliance-view-header">
      <h2 class="compliance-view-title">Control Management</h2>
      <div class="compliance-header-actions">
        <!-- View Toggle removed - only list view available -->

        <!-- Export controls - use global styles from main.css (custom dropdown + button) -->
        <div class="export-controls">
          <div class="export-controls-inner">
            <div
              class="export-select-wrapper"
              @click.stop="isExportDropdownOpen = !isExportDropdownOpen"
            >
              <button
                type="button"
                class="export-select-trigger"
              >
                <span class="export-select-text">{{ exportFormatLabel }}</span>
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
                    'is-selected': opt.value === exportFormat
                  }"
                  @click.stop="selectExportFormatOption(opt)"
                >
                  <span
                    v-if="opt.value === exportFormat"
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
              @click="exportCompliances"
              class="export-btn"
              :disabled="isExporting || !exportFormat"
            >
              <i v-if="!isExporting" class="fas fa-download"></i>
              <span v-if="isExporting">Exporting...</span>
              <span v-else>Export</span>
            </button>
          </div>
        </div>
      </div>
    </div>


    <!-- Loading State -->
    

    <!-- Breadcrumbs -->
    <div class="breadcrumbs" v-if="breadcrumbs.length > 0">
      <div v-for="(crumb, index) in breadcrumbs" :key="crumb.id" class="breadcrumb-chip">
        {{ crumb.name }}
        <span class="breadcrumb-close" @click="goToStep(index)">&times;</span>
      </div>
    </div>

    <div class="compliance-content-wrapper">
      <!-- Frameworks Section -->
      <template v-if="showFrameworks">
        <div class="compliance-section-header">Frameworks</div>
        
        <!-- List View for Frameworks -->
        <div class="compliance-list-view">
          <div class="compliance-dynamic-table-wrapper">
            <table class="compliance-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Description</th>
                  <th>Versions</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="fw in filteredFrameworks" :key="fw.id" @click="selectFramework(fw)" class="clickable-row">
                  <td class="compliance-name" data-label="Name">{{ fw.name }}</td>
                  <td data-label="Category">{{ fw.category }}</td>
                  <td data-label="Status">
                    <span class="compliance-card-status" :class="statusClass(fw.status)">{{ fw.status }}</span>
                  </td>
                  <td class="compliance-description" data-label="Description">{{ truncateDescription(fw.description) }}</td>
                  <td data-label="Versions">{{ fw.versions.length }}</td>
                  <td data-label="Actions">
                    <button class="compliance-action-btn" @click.stop="viewAllCompliances('framework', fw.id, fw.name)">
                      <i class="fas fa-list"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- Policies Section -->
      <template v-else-if="showPolicies">
        <div class="compliance-section-header">Policies in {{ selectedFramework.name }}</div>
        
        <!-- List View for Policies -->
        <div class="compliance-list-view">
          <div class="compliance-dynamic-table-wrapper">
            <table class="compliance-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Description</th>
                  <th>Versions</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="policy in policies" :key="policy.id" @click="selectPolicy(policy)" class="clickable-row">
                  <td class="compliance-name" data-label="Name">{{ policy.name }}</td>
                  <td data-label="Category">{{ policy.category }}</td>
                  <td data-label="Status">
                    <span class="compliance-card-status" :class="statusClass(policy.status)">{{ policy.status }}</span>
                  </td>
                  <td class="compliance-description" data-label="Description">{{ truncateDescription(policy.description) }}</td>
                  <td data-label="Versions">{{ policy.versions.length }}</td>
                  <td data-label="Actions">
                    <button class="compliance-action-btn" @click.stop="viewAllCompliances('policy', policy.id, policy.name)">
                      <i class="fas fa-list"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- Subpolicies Section -->
      <template v-else-if="showSubpolicies">
        <div class="compliance-section-header">Subpolicies in {{ selectedPolicy.name }}</div>
        
        <!-- List View for Subpolicies -->
        <div class="compliance-list-view">
          <div class="compliance-dynamic-table-wrapper">
            <table class="compliance-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Description</th>
                  <th>Control</th>
                  <th>Duration</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="subpolicy in subpolicies" :key="subpolicy.id" @click="selectSubpolicy(subpolicy)" class="clickable-row">
                  <td class="compliance-name" data-label="Name">{{ subpolicy.name }}</td>
                  <td data-label="Category">{{ subpolicy.category }}</td>
                  <td data-label="Status">
                    <span class="compliance-card-status" :class="statusClass(subpolicy.status)">{{ subpolicy.status }}</span>
                  </td>
                  <td class="compliance-description" data-label="Description">{{ truncateDescription(subpolicy.description) }}</td>
                  <td data-label="Control">{{ truncateDescription(subpolicy.control) }}</td>
                  <td data-label="Duration">{{ subpolicy.permanent_temporary }}</td>
                  <td data-label="Actions">
                    <button class="compliance-action-btn" @click.stop="viewAllCompliances('subpolicy', subpolicy.id, subpolicy.name)">
                      <i class="fas fa-list"></i>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>

      <!-- Compliances Section -->
      <template v-else-if="selectedSubpolicy">
        <div class="compliance-section-header">
          <span>Compliances in {{ selectedSubpolicy.name }}</span>
        </div>
        
        <div v-if="loading" class="compliance-loading-spinner">
          <i class="fas fa-circle-notch fa-spin"></i>
          <span>Loading controls...</span>
        </div>
        
        <div v-else-if="!hasCompliances" class="compliance-no-data">
          <i class="fas fa-inbox"></i>
          <p>No controls found for this subpolicy</p>
        </div>
        
        <!-- List View -->
        <div class="compliance-list-view">
          <div class="compliance-dynamic-table-wrapper">
            <DynamicTable
              :data="filteredCompliances"
              :columns="visibleColumns"
              uniqueKey="id"
              :showPagination="true"
              :showActions="true"
              @open-column-chooser="handleOpenColumnChooser"
            >
              <template #actions="{ row }">
                <button class="compliance-action-btn" @click="handleViewCompliance(row)"><i class="fas fa-eye"></i></button>
              </template>
            </DynamicTable>
          </div>
        </div>
      </template>
    </div>

    <!-- Versions Modal -->
    <div v-if="showVersionsModal" class="modal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ versionModalTitle }}</h3>
          <button class="close-btn" @click="closeVersionsModal">&times;</button>
        </div>
        <div class="modal-body">
          <div v-if="versions.length === 0" class="no-versions">
            No versions found.
          </div>
          <div v-else class="version-grid">
            <div v-for="version in versions" :key="version.id" class="version-card">
              <div class="version-header">
                <span class="version-number">Version {{ version.version }}</span>
                <div class="version-badges">
                  <span class="status-badge" :class="statusClass(version.status)">{{ version.status }}</span>
                  <span class="status-badge" :class="statusClass(version.activeInactive)">{{ version.activeInactive }}</span>
                </div>
              </div>
              <div class="version-details">
                <p class="version-desc">{{ version.description }}</p>
                <div class="version-info-grid">
                  <div class="info-group">
                    <span class="info-label">Maturity Level:</span>
                    <span class="info-value">{{ version.maturityLevel }}</span>
                  </div>
                  <div class="info-group">
                    <span class="info-label">Type:</span>
                    <span class="info-value">{{ version.mandatoryOptional }} | {{ version.manualAutomatic }}</span>
                  </div>
                  <div class="info-group">
                    <span class="info-label">Criticality:</span>
                    <span class="info-value" :class="'criticality-' + version.criticality.toLowerCase()">
                      {{ version.criticality }}
                    </span>
                  </div>
                  <div class="info-group" v-if="version.isRisk">
                    <span class="info-label">Risk Status:</span>
                    <span class="info-value risk">Risk Identified</span>
                  </div>
                </div>
                <div class="version-metadata">
                  <span>
                    <i class="fas fa-user"></i>
                    {{ version.createdBy }}
                  </span>
                  <span>
                    <i class="fas fa-calendar"></i>
                    {{ formatDate(version.createdDate) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Column Chooser Modal -->
    <div v-if="showColumnEditor" class="incident-column-editor-overlay" @click.self="toggleColumnEditor">
      <div class="incident-column-editor-modal">
        <div class="incident-column-editor-header">
          <h3>Choose Columns</h3>
          <button class="incident-column-editor-close" @click="toggleColumnEditor">&times;</button>
        </div>

        <div class="search-bar">
          <i class="fas fa-search search-bar__icon"></i>
          <input
            type="text"
            v-model="columnSearchQuery"
            placeholder="Search columns..."
            class="search-bar__input"
          />
        </div>

        <div class="incident-column-editor-actions">
          <button class="incident-column-select-btn" @click="selectAllColumns">Select All</button>
          <button class="incident-column-select-btn" @click="deselectAllColumns">Deselect All</button>
          <button class="incident-column-select-btn" @click="resetColumnSelection">Reset to Default</button>
        </div>

        <div class="incident-column-editor-list">
          <div
            v-for="column in filteredColumnDefinitions"
            :key="column.key"
            class="incident-column-editor-item"
          >
            <label class="incident-column-editor-label">
              <input
                type="checkbox"
                :checked="isColumnVisible(column.key)"
                @change="toggleColumnVisibility(column.key)"
                class="incident-column-editor-checkbox"
              />
              <span class="incident-column-editor-text">{{ column.label }}</span>
            </label>
          </div>
          <div v-if="filteredColumnDefinitions.length === 0" class="incident-column-editor-empty">
            No columns found matching your search.
          </div>
        </div>

        <div class="incident-column-editor-footer">
          <button class="incident-column-done-btn" @click="toggleColumnEditor">Done</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { PopupService } from '@/modules/popup'
import DynamicTable from '../DynamicTable.vue'
import AccessUtils from '@/utils/accessUtils'
import { useComplianceStore } from '@/stores/compliance'
import { useFrameworkStore } from '@/stores/framework'
import { assertSafeDownloadUrl, openUrlInNewTabSafe } from '@/utils/safeExternalNavigation'

const complianceStore = useComplianceStore()
const frameworkStore = useFrameworkStore()
const { frameworks: storeFrameworks } = storeToRefs(complianceStore)

// State
const frameworks = ref([])
const selectedFramework = ref(null)
const selectedPolicy = ref(null)
const selectedSubpolicy = ref(null)
const showVersionsModal = ref(false)
const versions = ref([])
const policies = ref([])
const subpolicies = ref([])
const loading = ref(false)
const error = ref(null)
const versionModalTitle = ref('')
// Removed viewMode - only list view is available
// const expandedCompliance = ref(null)
const router = useRouter()

// Framework session state — now sourced from frameworkStore (read-only local alias)
const sessionFrameworkId = computed(() => frameworkStore.selectedFrameworkId)

// Export state
const exportFormat = ref('')
const isExporting = ref(false)
const isExportDropdownOpen = ref(false)
const exportFormatOptions = [
  { value: '', label: 'Select format' },
  { value: 'xlsx', label: 'Excel (.xlsx)' },
  { value: 'csv', label: 'CSV (.csv)' },
  { value: 'pdf', label: 'PDF (.pdf)' },
  { value: 'json', label: 'JSON (.json)' },
  { value: 'xml', label: 'XML (.xml)' },
  { value: 'txt', label: 'Text (.txt)' }
]

const exportFormatLabel = computed(() => {
  const match = exportFormatOptions.find(opt => opt.value === exportFormat.value)
  return match ? match.label : 'Select format'
})

// Define columns for DynamicTable
const tableColumns = [
  { key: 'identifier', label: 'ID', sortable: true },
  { key: 'name', label: 'Control', sortable: true },
  { key: 'annex', label: 'Annex', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'category', label: 'Criticality', sortable: true },
  { key: 'maturityLevel', label: 'Maturity Level', sortable: true },
  { key: 'mandatoryOptional', label: 'Type', sortable: true },
  { key: 'version', label: 'Version', sortable: true },
  { key: 'createdBy', label: 'Created By', sortable: true },
  { key: 'createdDate', label: 'Created Date', sortable: true },
]

// Column chooser state
const showColumnEditor = ref(false)
const columnSearchQuery = ref('')
// Default visible columns - show all by default
const defaultVisibleColumns = tableColumns.map(col => col.key)
const visibleColumnKeys = ref([...defaultVisibleColumns])

// Column definitions for the chooser
const columnDefinitions = computed(() => tableColumns)

// Filtered columns based on search query
const filteredColumnDefinitions = computed(() => {
  if (!columnSearchQuery.value) {
    return columnDefinitions.value
  }
  const query = columnSearchQuery.value.toLowerCase()
  return columnDefinitions.value.filter(col =>
    col.label.toLowerCase().includes(query) ||
    col.key.toLowerCase().includes(query)
  )
})

// Visible columns based on selection
const visibleColumns = computed(() => {
  return tableColumns.filter(col => visibleColumnKeys.value.includes(col.key))
})

// Computed
const breadcrumbs = computed(() => {
  const arr = []
  if (selectedFramework.value) arr.push({ id: 0, name: selectedFramework.value.name })
  if (selectedPolicy.value) arr.push({ id: 1, name: selectedPolicy.value.name })
  if (selectedSubpolicy.value) arr.push({ id: 2, name: selectedSubpolicy.value.name })
  return arr
})

const showFrameworks = computed(() => !selectedFramework.value)
const showPolicies = computed(() => selectedFramework.value && !selectedPolicy.value)
const showSubpolicies = computed(() => selectedPolicy.value && !selectedSubpolicy.value)

// Filter frameworks based on session framework ID (from frameworkStore)
const filteredFrameworks = computed(() => {
  const fwId = sessionFrameworkId.value
  if (fwId && fwId !== 'all') {
    return frameworks.value.filter(fw => fw.id.toString() === fwId.toString())
  }
  return frameworks.value
})

// View toggle logic removed - only list view is available

const hasCompliances = computed(() => {
  return selectedSubpolicy.value && 
         selectedSubpolicy.value.compliances && 
         selectedSubpolicy.value.compliances.length > 0;
})

// Replace the filtered computed properties
const filteredCompliances = computed(() => {
  if (!selectedSubpolicy.value || !selectedSubpolicy.value.compliances) return [];
  return selectedSubpolicy.value.compliances; // Return all compliances without filtering
});

const mapFrameworkRows = (raw = []) =>
  (Array.isArray(raw) ? raw : []).map((fw) => ({
    id: fw.FrameworkId ?? fw.id,
    name: fw.FrameworkName ?? fw.name,
    category: fw.FrameworkCategory ?? fw.category ?? 'General',
    status: fw.Status ?? fw.status ?? fw.ActiveInactive ?? 'Active',
    description: fw.Description ?? fw.description ?? fw.FrameworkDescription ?? '',
    versions: fw.versions ?? [],
  }))

const hydrateFrameworksFromCache = () => {
  if (Array.isArray(complianceStore.frameworks) && complianceStore.frameworks.length) {
    frameworks.value = mapFrameworkRows(complianceStore.frameworks)
    return true
  }
  try {
    const raw = window?.sessionStorage?.getItem('pinia_compliance_frameworks_cache_v1')
    if (!raw) return false
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed?.data) || !parsed.data.length) return false
    frameworks.value = mapFrameworkRows(parsed.data)
    return true
  } catch {
    return false
  }
}

const syncFrameworkRowsFromStore = () => {
  frameworks.value = mapFrameworkRows(complianceStore.frameworks)
}

// Apply the framework selection that is already in frameworkStore (no separate HTTP call needed).
const applySessionFramework = async () => {
  const fwId = frameworkStore.selectedFrameworkId
  if (!fwId || fwId === 'all') {
    selectedFramework.value = null
    selectedPolicy.value = null
    selectedSubpolicy.value = null
    return
  }
  const frameworkExists = frameworks.value.find(f => f.id.toString() === fwId.toString())
  if (frameworkExists) {
    await selectFramework(frameworkExists)
  }
}

// Lifecycle
// Check for pending/completed exports on component mount
const checkPendingExports = async () => {
  try {
    const exportStateStr = localStorage.getItem('compliance_export_state');
    if (!exportStateStr) return;
    
    const exportState = JSON.parse(exportStateStr);
    
    // If export is still processing and we have a task_id, check status
    if (exportState.status === 'processing' && exportState.taskId) {
      try {
        const statusData = await complianceStore.fetchComplianceRegisterExportStatus(exportState.taskId);
        
        if (statusData.success) {
          if (statusData.status === 'completed' && statusData.file_url) {
            // Export completed while user was away
            exportState.status = 'completed';
            exportState.fileUrl = statusData.file_url;
            exportState.fileName = statusData.file_name;
            exportState.completedAt = statusData.completed_at;
            localStorage.setItem('compliance_export_state', JSON.stringify(exportState));
            
            PopupService.success(
              `Your export completed! ${exportState.recordCount} records exported as ${exportState.format.toUpperCase()}. Click to download.`,
              'Export Completed',
              () => {
                try {
                  openUrlInNewTabSafe(statusData.file_url);
                } catch (e) {
                  console.error('Blocked unsafe export URL:', e)
                  PopupService.error('Export link is not safe to open automatically.')
                }
              }
            );
          } else if (statusData.status === 'failed') {
            exportState.status = 'failed';
            exportState.error = statusData.error;
            localStorage.setItem('compliance_export_state', JSON.stringify(exportState));
            PopupService.error(`Export failed: ${statusData.error || 'Unknown error'}`);
          }
        }
      } catch (statusErr) {
        console.error('Error checking export status:', statusErr);
        // Keep checking - export might still be processing
      }
    } else if (exportState.status === 'completed' && exportState.fileUrl) {
      // Show notification for completed export
      PopupService.success(
        `Your export is ready! ${exportState.recordCount} records exported as ${exportState.format.toUpperCase()}. Click to download.`,
        'Export Ready',
        () => {
          try {
            openUrlInNewTabSafe(exportState.fileUrl);
          } catch (e) {
            console.error('Blocked unsafe export URL:', e)
            PopupService.error('Export link is not safe to open automatically.')
            return
          }
          localStorage.removeItem('compliance_export_state');
        }
      );
    }
  } catch (err) {
    console.error('Error checking pending exports:', err);
  }
};

onMounted(async () => {
  await checkPendingExports()

  try {
    // Paint instantly from Pinia/session cache if available.
    const hasWarmFrameworks = hydrateFrameworksFromCache()
    loading.value = !hasWarmFrameworks

    // Ensure frameworkStore session is loaded (no-op if already done by HomeView/shell)
    if (!frameworkStore.selectedFrameworkId) {
      await frameworkStore.loadFrameworkFromSession()
    }

    // Background refresh for cache revalidation; don't block initial render.
    const prefetchPromise = complianceStore.prefetchComplianceDomain().then(() => {
      syncFrameworkRowsFromStore()
    })

    // Auto-select framework if one is persisted in frameworkStore session
    await applySessionFramework()

    if (hasWarmFrameworks) {
      void prefetchPromise
    } else {
      await prefetchPromise
    }
  } catch (err) {
    if (err?.response && [401, 403].includes(err.response.status)) {
      AccessUtils.showViewAllComplianceDenied()
      return
    }
    error.value = 'Failed to load frameworks'
    console.error('[AllCompliance] Error loading frameworks:', err?.response?.data ?? err.message)
    frameworks.value = []
    PopupService.error('Failed to load frameworks. Please refresh the page and try again.', 'Loading Error')
  } finally {
    loading.value = false
  }

  // Re-sync frameworks whenever the store updates (background refresh)
  watch(storeFrameworks, (raw) => {
    if (!raw?.length) return
    syncFrameworkRowsFromStore()
  })
})

watch(
  () => frameworkStore.selectedFrameworkId,
  async (newFrameworkId, oldFrameworkId) => {
    if (newFrameworkId === oldFrameworkId) return
    if (!frameworks.value.length) return
    await applySessionFramework()
  }
)

// Methods
// setViewMode method removed - only list view is available

async function selectFramework(fw) {
  try {
    loading.value = true
    selectedFramework.value = fw
    selectedPolicy.value = null
    selectedSubpolicy.value = null

    // Persist selection via frameworkStore (single source of truth — no direct FRAMEWORK_SET_SELECTED call)
    await frameworkStore.setFramework({ id: fw.id, name: fw.name })

    // Sync selection into complianceStore so hierarchy fetches use the right frameworkId
    complianceStore.setSelectedFramework(fw.id)

    // Fetch policies using store action (cache-first)
    await complianceStore.fetchPoliciesByFramework(fw.id)
    const storePolicies = complianceStore.policiesForFramework(fw.id)

    policies.value = storePolicies.map(p => ({ ...p, versions: p.versions ?? [] }))
  } catch (err) {
    if (err?.response && [401, 403].includes(err.response.status)) {
      AccessUtils.showViewAllComplianceDenied()
      return
    }
    error.value = 'Failed to load policies'
    console.error('[AllCompliance] Error fetching policies:', err)
    policies.value = []
    PopupService.error('Failed to load policies. Please try selecting a different framework.', 'Loading Error')
  } finally {
    loading.value = false
  }
}

async function selectPolicy(policy) {
  try {
    loading.value = true
    selectedPolicy.value = policy
    selectedSubpolicy.value = null
    complianceStore.setSelectedPolicy(policy.id)

    // Fetch subpolicies via store (cache-first)
    await complianceStore.fetchSubpoliciesByPolicy(policy.id)
    const storeSubs = complianceStore.subpoliciesForPolicy(policy.id)

    subpolicies.value = storeSubs
  } catch (err) {
    error.value = 'Failed to load subpolicies'
    console.error('[AllCompliance] Error fetching subpolicies:', err)
    subpolicies.value = []
    PopupService.error('Failed to load subpolicies. Please try selecting a different policy.', 'Loading Error')
  } finally {
    loading.value = false
  }
}

async function selectSubpolicy(subpolicy) {
  try {
    loading.value = true;
    selectedSubpolicy.value = subpolicy;
    complianceStore.setSelectedSubpolicy(subpolicy.id);
    
    // Force-refresh compliances when entering controls to avoid stale cache
    // right after approve/review transitions.
    await complianceStore.fetchCompliancesBySubpolicy(subpolicy.id, { force: true });
    const responseCompliances = complianceStore.compliancesBySubpolicyId[subpolicy.id] || [];
    console.log('Subpolicy compliances response:', responseCompliances);
    
    if (Array.isArray(responseCompliances)) {
      // Enhanced logging for debugging
      if (responseCompliances.length > 0) {
        const firstCompliance = responseCompliances[0];
        console.log('DETAILED COMPLIANCE OBJECT:', JSON.stringify(firstCompliance, null, 2));
        
        // Display all field names and values for better debugging
        console.log('COMPLIANCE FIELD VALUES:');
        Object.keys(firstCompliance).forEach(key => {
          console.log(`- ${key}: ${JSON.stringify(firstCompliance[key])}`);
        });
      }
      
      // Store the original compliance objects as they come from the API
      selectedSubpolicy.value = {
        ...subpolicy,
        compliances: responseCompliances.map(compliance => {
          return {
            // IMPORTANT: Use the exact PascalCase field names from the API
            id: compliance.ComplianceId,
            name: compliance.ComplianceItemDescription,
            description: compliance.ComplianceItemDescription,
            status: compliance.Status,
            category: compliance.Criticality,
            maturityLevel: compliance.MaturityLevel,
            mandatoryOptional: compliance.MandatoryOptional,
            manualAutomatic: compliance.ManualAutomatic,
            createdBy: compliance.CreatedByName,
            createdDate: compliance.CreatedByDate,
            identifier: compliance.Identifier,
            
            annex: compliance.Annex || compliance.SubPolicyIdentifier || null,  // Add Annex from SubPolicy Identifier
            version: compliance.ComplianceVersion,
            isRisk: compliance.IsRisk,
            
            // Keep the original Pascal case names for these fields
            PossibleDamage: compliance.PossibleDamage,
            mitigation: compliance.mitigation,
            SeverityRating: compliance.Impact,
            Probability: compliance.Probability,
            PermanentTemporary: compliance.PermanentTemporary,
            ActiveInactive: compliance.ActiveInactive,
            
            // Store the original object to access all fields in the expanded view
            originalData: compliance
          };
        })
      };
    } else {
      selectedSubpolicy.value.compliances = [];
    }
  } catch (err) {
    // Check if it's an access control error
    if (err.response && [401, 403].includes(err.response.status)) {
      AccessUtils.showViewAllComplianceDenied();
      return;
    }
    
    console.error('Error fetching subpolicy compliances:', err);
    error.value = 'Failed to load compliances';
    selectedSubpolicy.value.compliances = [];
  } finally {
    loading.value = false;
  }
}

function closeVersionsModal() {
  showVersionsModal.value = false
  versions.value = []
  versionModalTitle.value = ''
}

// Column chooser functions
const handleOpenColumnChooser = () => {
  console.log('🔍 handleOpenColumnChooser called - event received from DynamicTable')
  toggleColumnEditor()
}

const toggleColumnEditor = () => {
  console.log('🔍 toggleColumnEditor called, current state:', showColumnEditor.value)
  showColumnEditor.value = !showColumnEditor.value
  console.log('✅ showColumnEditor set to:', showColumnEditor.value)
  if (!showColumnEditor.value) {
    columnSearchQuery.value = ''
  }
}

const toggleColumnVisibility = (columnKey) => {
  const index = visibleColumnKeys.value.indexOf(columnKey)
  if (index > -1) {
    visibleColumnKeys.value.splice(index, 1)
  } else {
    visibleColumnKeys.value.push(columnKey)
  }
}

const isColumnVisible = (columnKey) => {
  return visibleColumnKeys.value.includes(columnKey)
}

const selectAllColumns = () => {
  visibleColumnKeys.value = columnDefinitions.value.map(col => col.key)
}

const deselectAllColumns = () => {
  visibleColumnKeys.value = []
}

const resetColumnSelection = () => {
  visibleColumnKeys.value = [...defaultVisibleColumns]
}

function goToStep(idx) {
  if (idx <= 0) {
    selectedFramework.value = null
    selectedPolicy.value = null
    selectedSubpolicy.value = null
    complianceStore.resetSelection()
  } else if (idx === 1) {
    selectedPolicy.value = null
    selectedSubpolicy.value = null
    complianceStore.setSelectedPolicy(null)
    complianceStore.setSelectedSubpolicy(null)
  } else if (idx === 2) {
    selectedSubpolicy.value = null
    complianceStore.setSelectedSubpolicy(null)
  }
}

function formatDate(date) {
  if (!date) return 'N/A'
  return new Date(date).toLocaleDateString()
}

// function categoryIcon(category) {
//   switch ((category || '').toLowerCase()) {
//     case 'governance': return 'fas fa-shield-alt'
//     case 'access control': return 'fas fa-user-shield'
//     case 'asset management': return 'fas fa-boxes'
//     case 'cryptography': return 'fas fa-key'
//     case 'data management': return 'fas fa-database'
//     case 'device management': return 'fas fa-mobile-alt'
//     case 'risk management': return 'fas fa-exclamation-triangle'
//     case 'supplier management': return 'fas fa-handshake'
//     case 'business continuity': return 'fas fa-business-time'
//     case 'privacy': return 'fas fa-user-secret'
//     case 'system protection': return 'fas fa-shield-virus'
//     case 'incident response': return 'fas fa-ambulance'
//     default: return 'fas fa-file-alt'
//   }
// }

function statusClass(status) {
  if (!status) return ''
  const s = status.toLowerCase()
  // Check inactive FIRST because "INACTIVE" contains "ACTIVE"
  if (s.includes('inactive')) return 'inactive'
  if (s.includes('active')) return 'active'
  if (s.includes('scheduled')) return 'scheduled'
  if (s.includes('pending')) return 'pending'
  if (s.includes('under') && s.includes('review')) return 'under-review'
  return ''
}

const viewAllCompliances = (type, id, name) => {
  router.push({
    name: 'ComplianceView',
    params: {
      type: type,
      id: id,
      name: encodeURIComponent(name)
    }
  });
};



const selectExportFormatOption = (opt) => {
  exportFormat.value = opt.value
  isExportDropdownOpen.value = false
}

const exportCompliances = async () => {
  console.log('Exporting compliances (single server-side aggregation)...');
  if (!exportFormat.value) {
    PopupService.error('Please select an export format first.');
    return;
  }

  isExporting.value = true;
  
  try {
    // Determine file name based on what's being exported
    let fileName = 'compliance_export';
    if (selectedSubpolicy.value) {
      fileName = `compliance_export_${selectedSubpolicy.value.name.replace(/[^a-z0-9]/gi, '_')}`;
    } else if (selectedPolicy.value) {
      fileName = `compliance_export_${selectedPolicy.value.name.replace(/[^a-z0-9]/gi, '_')}`;
    } else if (selectedFramework.value) {
      fileName = `compliance_export_${selectedFramework.value.name.replace(/[^a-z0-9]/gi, '_')}`;
    } else {
      fileName = 'compliance_export_all_frameworks';
    }

    const userId = localStorage.getItem('user_id') || 'default_user';

    // Scope for server-side aggregation
    const scope = {
      framework_id: selectedFramework.value?.id || null,
      policy_id: selectedPolicy.value?.id || null,
      subpolicy_id: selectedSubpolicy.value?.id || null,
    };

    // Save export state to localStorage so it can continue even if user navigates away
    const exportState = {
      taskId: null,
      status: 'processing',
      format: exportFormat.value,
      recordCount: null,
      startedAt: new Date().toISOString(),
      exportScope: selectedFramework.value ? `Framework: ${selectedFramework.value.name}` : 
                   selectedPolicy.value ? `Policy: ${selectedPolicy.value.name}` :
                   selectedSubpolicy.value ? `SubPolicy: ${selectedSubpolicy.value.name}` :
                   'All Frameworks'
    };
    localStorage.setItem('compliance_export_state', JSON.stringify(exportState));

    // Single backend call: server fetches all relevant compliances and exports
    const result = await complianceStore.exportComplianceManagement({
      export_format: exportFormat.value,
      user_id: userId,
      file_name: fileName,
      framework_id: scope.framework_id,
      policy_id: scope.policy_id,
      subpolicy_id: scope.subpolicy_id,
      scope
    });

    console.log('Export successful:', result);
    console.log('Response structure:', Object.keys(result));
    
    // Save task ID and record count if provided
    if (result.task_id) {
      exportState.taskId = result.task_id;
    }
    if (result.metadata && typeof result.metadata.record_count === 'number') {
      exportState.recordCount = result.metadata.record_count;
    }
    localStorage.setItem('compliance_export_state', JSON.stringify(exportState));
    
    if (result.success && result.file_url && result.file_name) {
      console.log('File URL found:', result.file_url);
      console.log('File name:', result.file_name);

      const rawFileUrl = String(result.file_url || '').trim();
      const exportMethod = String(result?.metadata?.method || '').toLowerCase();
      const isWindowsLocalPath = /^[a-zA-Z]:[\\/]/.test(rawFileUrl);
      const isLikelyLocalFallback =
        rawFileUrl.toLowerCase().startsWith('file://') ||
        isWindowsLocalPath ||
        exportMethod === 'local_fallback';

      // Local fallback export already writes file to Downloads; browser cannot open local paths safely.
      if (isLikelyLocalFallback) {
        exportState.status = 'completed';
        exportState.fileUrl = result.file_url;
        exportState.fileName = result.file_name;
        exportState.completedAt = new Date().toISOString();
        localStorage.setItem('compliance_export_state', JSON.stringify(exportState));
        PopupService.success('Export completed successfully. File is saved to your Downloads folder.');
        localStorage.removeItem('compliance_export_state');
        isExporting.value = false;
        return;
      }

      const safeFileUrl = result.file_url;
      try {
        const isSafe = assertSafeDownloadUrl(result.file_url);
        if (!isSafe) {
          throw new Error('Unsafe export URL');
        }
      } catch (urlErr) {
        console.error('Unsafe export URL from server:', urlErr);
        exportState.status = 'failed';
        exportState.error = 'Unsafe file URL received from server';
        localStorage.setItem('compliance_export_state', JSON.stringify(exportState));
        PopupService.error('Export failed: unsafe download URL received.');
        isExporting.value = false;
        return;
      }
      
      // Update export state
      exportState.status = 'completed';
      exportState.fileUrl = result.file_url;
      exportState.fileName = result.file_name;
      exportState.completedAt = new Date().toISOString();
      localStorage.setItem('compliance_export_state', JSON.stringify(exportState));

      // SECURITY: sanitize download filename to avoid control chars / path injection in download attribute.
      const safeFileName =
        String(result.file_name || 'download')
          .replace(/[\r\n]/g, '')
          .split('\0').join('')
          .split(/[\\/]/)
          .pop() || 'download';
      
      // Try to open the file URL in a new tab, fallback to download if it fails
      try {
        console.log('Attempting to open file in new tab...');
        const newWindow = openUrlInNewTabSafe(safeFileUrl);
        console.log('Window result:', newWindow);
        if (newWindow) {
          console.log('File opened successfully in new tab');
          PopupService.success('Export completed successfully! File opened in new tab.');
        } else {
          console.log('Popup blocked, falling back to download');
          // Fallback to download if popup is blocked
          const fileRes = await fetch(safeFileUrl);
          const blob = await fileRes.blob();
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', safeFileName);
          document.body.appendChild(link);
          link.click();
          link.remove();
          window.URL.revokeObjectURL(url);
          PopupService.success('Export completed successfully! File downloaded.');
        }
      } catch (downloadErr) {
        console.error('Download error:', downloadErr);
        // Fallback to download if window.open fails
        try {
          console.log('Attempting final download fallback...');
          const fileRes = await fetch(safeFileUrl);
          const blob = await fileRes.blob();
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', safeFileName);
          document.body.appendChild(link);
          link.click();
          link.remove();
          window.URL.revokeObjectURL(url);
          PopupService.success('Export completed successfully! File downloaded.');
        } catch (finalErr) {
          console.error('Final download fallback failed:', finalErr);
          PopupService.error('Export completed but failed to open/download file. Please check the file URL manually.');
        }
      }
      
      // Clear export state after successful completion
      localStorage.removeItem('compliance_export_state');
    } else {
      console.error('Export failed or incomplete response:', result);
      exportState.status = 'failed';
      exportState.error = result.error || 'No file URL received from server';
      localStorage.setItem('compliance_export_state', JSON.stringify(exportState));
      PopupService.error('Export failed: ' + (result.error || 'No file URL received from server'));
    }
    
    isExporting.value = false;
  } catch (error) {
    console.error('Export failed:', error);
    console.error('Error response:', error.response?.data);
    
    // Check if this is an access control error first
    if (!AccessUtils.handleApiError(error, 'export compliances')) {
      // Only show generic error if it's not an access denied error
      PopupService.error('Export failed: ' + (error.response?.data?.error || error.message || 'Unknown error'));
    }
    
    isExporting.value = false;
  }
}

// const handleComplianceExpand = (compliance) => {
//   if (expandedCompliance.value === compliance.id) {
//     expandedCompliance.value = null;
//   } else {
//     expandedCompliance.value = compliance.id;
//   }
// };

// Add method to format mitigation display
// const formatMitigation = (mitigation) => {
//   if (!mitigation) {
//     return 'Not specified';
//   }
//   
//   // Check if it's JSON format
//   if (typeof mitigation === 'string' && (mitigation.startsWith('[') || mitigation.startsWith('{'))) {
//     try {
//       const parsed = JSON.parse(mitigation);
//       
//       // If it's an array of steps
//       if (Array.isArray(parsed)) {
//         return parsed.map((step, index) => `${index + 1}. ${step}`).join('\n');
//       }
//       
//       // If it's an object, extract meaningful values
//       if (typeof parsed === 'object') {
//         if (parsed.steps && Array.isArray(parsed.steps)) {
//           return parsed.steps.map((step, index) => `${index + 1}. ${step}`).join('\n');
//         }
//         if (parsed.description) {
//           return parsed.description;
//         }
//         // Convert object to readable format
//         return Object.entries(parsed)
//           .map(([key, value]) => `${key}: ${value}`)
//           .join('\n');
//       }
//       
//       return String(parsed);
//     } catch (e) {
//       // If JSON parsing fails, treat as plain text
//       return mitigation;
//     }
//   }
//   
//   // Return as plain text
//   return mitigation;
// };

// Add this utility function for truncating descriptions
function truncateDescription(desc) {
  if (!desc) return '';
  const maxLen = 80;
  return desc.length > maxLen ? desc.slice(0, maxLen) + '...' : desc;
}

// Add methods for actions
function handleViewCompliance(row) {
  // Show control details modal
  void showControlDetailsModal(row);
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function safeClassToken(value, fallback = 'default') {
  const token = String(value ?? '')
    .toLowerCase()
    .replace(/[^a-z0-9_-]/g, '');
  return token || fallback;
}

async function showControlDetailsModal(compliance) {
  let latest = { ...(compliance?.originalData || {}) };
  try {
    if (compliance?.id) {
      // Force refresh so modal always shows latest values after approvals/resubmissions.
      await complianceStore.fetchComplianceDetails(compliance.id, { force: true });
      const cachedLatest = complianceStore.complianceDetailsById[compliance.id];
      if (cachedLatest && typeof cachedLatest === 'object') {
        latest = { ...latest, ...cachedLatest };
      }
    }
  } catch (e) {
    console.warn('[AllCompliance] Unable to fetch latest compliance details for modal:', e);
  }

  const mitigationValue = latest.mitigation ?? compliance.mitigation;
  const safeMitigation = escapeHtml(
    typeof mitigationValue === 'object'
      ? JSON.stringify(mitigationValue)
      : (mitigationValue || 'Not specified')
  );
  const safeName = escapeHtml(latest.ComplianceTitle || latest.ComplianceItemDescription || compliance.name || 'Not specified');
  const safeIdentifier = escapeHtml(latest.Identifier || compliance.identifier || 'Not specified');
  const statusValue = latest.Status || compliance.status || 'Not specified';
  const safeStatus = escapeHtml(statusValue);
  const safeStatusClass = safeClassToken(statusValue, 'default');
  const categoryValue = latest.Criticality || compliance.category || 'Not specified';
  const safeCategory = escapeHtml(categoryValue);
  const safeCategoryClass = safeClassToken(categoryValue, 'default');
  const safeDescription = escapeHtml(latest.ComplianceItemDescription || compliance.description || 'No description available');
  const safeMandatoryOptional = escapeHtml(latest.MandatoryOptional || compliance.mandatoryOptional || 'Not specified');
  const safeManualAutomatic = escapeHtml(latest.ManualAutomatic || compliance.manualAutomatic || 'Not specified');
  const safeMaturityLevel = escapeHtml(latest.MaturityLevel || compliance.maturityLevel || 'Not specified');
  const safePossibleDamage = escapeHtml(latest.PossibleDamage || compliance.PossibleDamage || 'Not specified');
  const safeFramework = escapeHtml(latest.FrameworkName || selectedFramework.value?.name || 'Not specified');
  const safePolicy = escapeHtml(latest.PolicyName || selectedPolicy.value?.name || 'Not specified');
  const safeSubPolicy = escapeHtml(latest.SubPolicyName || selectedSubpolicy.value?.name || 'Not specified');

  const modalContent = `
    <div class="control-details-modal">
      <div class="modal-header">
        <h3>Control Details</h3>
        <button class="modal-close" onclick="this.closest('.control-details-modal').remove()">&times;</button>
      </div>
      <div class="modal-body">
        <div class="detail-section">
          <h4>Basic Information</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <label>Title:</label>
              <span>${safeName}</span>
            </div>
            <div class="detail-item">
              <label>ID:</label>
              <span>${safeIdentifier}</span>
            </div>
            <div class="detail-item">
              <label>Status:</label>
              <span class="status-badge ${safeStatusClass}">${safeStatus}</span>
            </div>
            <div class="detail-item">
              <label>Criticality:</label>
              <span class="criticality-badge ${safeCategoryClass}">${safeCategory}</span>
            </div>
          </div>
        </div>

        <div class="detail-section">
          <h4>Description</h4>
          <p>${safeDescription}</p>
        </div>

        <div class="detail-section">
          <h4>Implementation Details</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <label>Type:</label>
              <span>${safeMandatoryOptional}</span>
            </div>
            <div class="detail-item">
              <label>Implementation:</label>
              <span>${safeManualAutomatic}</span>
            </div>
            <div class="detail-item">
              <label>Maturity Level:</label>
              <span>${safeMaturityLevel}</span>
            </div>
          </div>
        </div>

        ${(latest.IsRisk ?? compliance.isRisk) ? `
        <div class="detail-section risk-section">
          <h4>Risk Information</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <label>Possible Damage:</label>
              <p>${safePossibleDamage}</p>
            </div>
            <div class="detail-item">
              <label>Mitigation:</label>
              <p>${safeMitigation}</p>
            </div>
          </div>
        </div>
        ` : ''}

        <div class="detail-section">
          <h4>Hierarchy</h4>
          <div class="detail-grid">
            <div class="detail-item">
              <label>Framework:</label>
              <span>${safeFramework}</span>
            </div>
            <div class="detail-item">
              <label>Policy:</label>
              <span>${safePolicy}</span>
            </div>
            <div class="detail-item">
              <label>SubPolicy:</label>
              <span>${safeSubPolicy}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Create modal overlay
  const modalOverlay = document.createElement('div');
  modalOverlay.className = 'modal-overlay';
  modalOverlay.innerHTML = modalContent;
  
  // Add click handler to close modal
  modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) {
      modalOverlay.remove();
    }
  });

  // Add modal styles
  const modalStyles = document.createElement('style');
  modalStyles.textContent = `
    .modal-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.95);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
      padding: 30px;
      backdrop-filter: blur(3px);
    }
    
    .control-details-modal {
      background: #ffffff;
      border-radius: 12px;
      width: 70% !important;
      max-width: 1000px !important;
      min-width: 700px !important;
      max-height: 85vh;
      min-height: 400px;
      overflow: hidden;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
      border: 1px solid #e5e7eb;
      margin: 30px !important;
      position: relative;
      z-index: 1001;
      box-sizing: border-box;
      flex-shrink: 0;
      display: flex;
      flex-direction: column;
    }
    
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px 24px;
      border-bottom: 1px solid #e5e7eb;
      background: #ffffff;
      border-radius: 12px 12px 0 0;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    
    .modal-header h3 {
      margin: 0;
      color: #1f2937;
      font-size: 1.25rem;
      font-weight: 700;
    }
    
    .modal-close {
      background: rgba(107, 114, 128, 0.1);
      border: none;
      font-size: 1.5rem;
      cursor: pointer;
      color: #6b7280;
      padding: 8px;
      border-radius: 8px;
      transition: all 0.2s ease;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 300;
    }
    
    .modal-close:hover {
      color: #374151;
      background: rgba(107, 114, 128, 0.2);
      transform: scale(1.1);
    }
    
    .modal-body {
      padding: 20px;
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
      background: #ffffff;
    }
    
    .detail-section {
      margin-bottom: 0;
      background: #ffffff;
      border-radius: 10px;
      padding: 16px;
      border: 1px solid #f1f5f9;
      box-shadow: none;
      transition: all 0.2s ease;
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    
    .detail-section h4 {
      margin: 0 0 16px 0;
      color: #1f2937;
      font-size: 1.25rem;
      font-weight: 700;
      padding-bottom: 12px;
      border-bottom: 2px solid #e5e7eb;
      position: relative;
    }
    
    .detail-section h4::after {
      content: '';
      position: absolute;
      bottom: -2px;
      left: 0;
      width: 60px;
      height: 3px;
      background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
      border-radius: 2px;
    }
    
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      flex: 1;
    }
    
    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding: 12px;
      background: #ffffff;
      border-radius: 8px;
      border-left: 3px solid #3b82f6;
      transition: all 0.2s ease;
      min-height: 50px;
      justify-content: center;
    }
    
    .detail-item label {
      font-weight: 700;
      color: #4b5563;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 4px;
    }
    
    .detail-item span,
    .detail-item p {
      color: #1f2937;
      font-weight: 500;
      line-height: 1.5;
      font-size: 0.9rem;
    }
    
    .detail-item span {
      font-weight: 600;
    }
    
    .status-badge,
    .criticality-badge {
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.025em;
      display: inline-block;
    }
    
    .status-badge.active { 
      background-color: #dcfce7; 
      color: #166534; 
      border: 1px solid #22c55e;
    }
    
    .status-badge.scheduled { 
      background-color: #dcfce7; 
      color: #166534; 
      border: 1px solid #22c55e;
    }
    
    .status-badge.inactive { 
      background-color: #fee2e2; 
      color: #991b1b; 
      border: 1px solid #ef4444;
    }
    
    .status-badge.pending { 
      background-color: #fef3c7; 
      color: #92400e; 
      border: 1px solid #f59e0b;
    }
    
    .status-badge.under-review { 
      background-color: #fef3c7; 
      color: #92400e; 
      border: 1px solid #f59e0b;
    }
    
    .criticality-badge.high { 
      background-color: #fee2e2; 
      color: #991b1b; 
      border: 1px solid #ef4444;
    }
    
    .criticality-badge.medium { 
      background-color: #fef3c7; 
      color: #92400e; 
      border: 1px solid #f59e0b;
    }
    
    .criticality-badge.low { 
      background-color: #dcfce7; 
      color: #166534; 
      border: 1px solid #22c55e;
    }
    
    .risk-section {
      background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
      padding: 16px;
      border-radius: 10px;
      border-left: 4px solid #ef4444;
      box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
    }
    
    .risk-section h4::after {
      background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
    }
  `;
  
  document.head.appendChild(modalStyles);
  document.body.appendChild(modalOverlay);
}
</script>

<style src="./AllCompliance.css"></style>

<style>
/* Framework Explorer inspired styling */
.compliance-view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  margin-bottom: 30px;
  padding-top: 20px;
  padding-bottom: 10px;
  border-bottom:none!important;
  flex-wrap: wrap;
  gap: 15px;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.compliance-view-title {
  margin: 0;
  color: #344054;
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  word-wrap: break-word;
  overflow-wrap: break-word;
  flex: 1;
  min-width: 0;
}

.compliance-header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

/* View toggle button styles removed - only list view is available */

/* Section header styling */
.compliance-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  font-size: 1.2rem!important;
  font-weight: 600;
  color: #344054;
  padding-bottom: 0;
  margin-bottom: -10px!important;
  border-bottom: none!important;
}

/* Export controls for this view use global .export-controls / .export-dropdown / .export-btn from main.css */

/* Enhanced Table Styling - Framework Explorer Style */
.compliance-list-view {
  background-color: transparent;
  border-radius: 0;
  border: none;
  overflow: hidden;
  box-shadow: none;
  margin-top: 0;
}

.compliance-table {
  width: 100%;
  border-collapse: collapse;
  background-color: transparent;
  margin: 0;
  border: none;
}

.compliance-table th {
  background: #f8f9fa !important;
  padding: 16px 12px;
  text-align: left;
  font-weight: 600;
  color: #495057 !important;
  border-bottom: 2px solid #dee2e6;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 10;
}

/* Force table header to light ash color */
table.compliance-table thead th,
.compliance-table thead th {
  background: #f8f9fa !important;
  color: #495057 !important;
}

.compliance-table td {
  padding: 16px 12px;
  border-bottom: 1px solid #f1f3f4;
  color: #495057;
  vertical-align: middle;
  font-size: 0.9rem;
}

.compliance-table tr {
  transition: all 0.2s ease;
}

.compliance-table tr:hover {
  background: transparent;
  transform: translateY(-1px);
  box-shadow: none;
}

.compliance-table tr.clickable-row {
  cursor: pointer;
}

.compliance-table tr:last-child td {
  border-bottom: none;
}

/* Status Text with Dots */
.compliance-card-status {
  display: inline-flex;
  align-items: center;
  font-size: 0.9rem;
  font-weight: 500;
  text-transform: capitalize;
  gap: 6px;
  background: none !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  box-shadow: none !important;
}

.compliance-card-status::before {
  content: '●';
  font-size: 0.8rem;
  font-weight: bold;
}

.compliance-card-status.active {
  color: #22c55e;
}

.compliance-card-status.active::before {
  color: #22c55e;
}

.compliance-card-status.scheduled {
  color: #22c55e;
}

.compliance-card-status.scheduled::before {
  color: #22c55e;
}

.compliance-card-status.inactive {
  color: #ef4444 !important;
}

.compliance-card-status.inactive::before {
  color: #ef4444 !important;
}

/* Force inactive to be red regardless of any other styles */
.compliance-card-status[class*="inactive"] {
  color: #ef4444 !important;
}

.compliance-card-status[class*="inactive"]::before {
  color: #ef4444 !important;
}

.compliance-card-status.pending {
  color: #f59e0b;
}

.compliance-card-status.pending::before {
  color: #f59e0b;
}

.compliance-card-status.under-review {
  color: #f59e0b;
}

.compliance-card-status.under-review::before {
  color: #f59e0b;
}

/* Criticality Badges */
.compliance-criticality-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  border: 2px solid transparent;
}

.compliance-criticality-high {
  background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
  color: #c62828;
  border-color: #ffcdd2;
}

.compliance-criticality-medium {
  background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
  color: #ef6c00;
  border-color: #ffecb3;
}

.compliance-criticality-low {
  background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
  color: #2e7d32;
  border-color: #c8e6c9;
}

/* Action Buttons - Framework Explorer Style */
.compliance-action-btn {
  padding: 8px 12px;
  font-size: 0.85rem;
  margin-right: 6px;
  border-radius: 8px;
  background: transparent;
  color: #495057;
  border: 1px solid #dee2e6;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.compliance-action-btn:hover {
  background: rgba(79, 140, 255, 0.1);
  color: #212529;
  transform: translateY(-2px);
  box-shadow: none;
  border-color: #4f8cff;
}

.compliance-action-btn.primary {
  background: linear-gradient(135deg, #4f8cff 0%, #3d7aff 100%);
  color: white;
  border-color: #4f8cff;
}

.compliance-action-btn.primary:hover {
  background: linear-gradient(135deg, #3d7aff 0%, #2b68ff 100%);
  border-color: #3d7aff;
}

.compliance-action-btn i {
  font-size: 0.9rem;
}

/* Card view styles removed - only list view is available */

/* Breadcrumbs - Framework Explorer Style */
.breadcrumbs {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.breadcrumb-chip {
  background: transparent;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  color: #495057;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #dee2e6;
  font-weight: 500;
}

.breadcrumb-close {
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
  color: #6c757d;
  transition: color 0.2s ease;
  padding: 2px;
  border-radius: 50%;
}

.breadcrumb-close:hover {
  color: #dc3545;
  background: rgba(220, 53, 69, 0.1);
}

/* Loading State */
.compliance-loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #495057;
  margin: 48px 0;
  font-size: 1.1rem;
  font-weight: 500;
}

.compliance-loading-spinner i {
  font-size: 1.5rem;
  color: #4f8cff;
}

/* No Data State */
.compliance-no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #6c757d;
  text-align: center;
}

.compliance-no-data i {
  font-size: 4rem;
  margin-bottom: 20px;
  color: #dee2e6;
}

.compliance-no-data p {
  font-size: 1.2rem;
  margin: 0;
  font-weight: 500;
}

/* Additional card-specific overrides can go here if needed */

/* Mobile responsive styles are now in AllCompliance.css */

/* Animation for smooth transitions */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.compliance-card,
.compliance-table tr {
  animation: slideIn 0.3s ease-out;
}

/* Focus states for accessibility */
.compliance-action-btn:focus {
  outline: 2px solid #4f8cff;
  outline-offset: 2px;
}

/* Expanded details styles are now in AllCompliance.css */

/* Compliances Grid */
.compliance-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.compliance-card {
  border: none;
  border-radius: 0;
  overflow: hidden;
  background-color: transparent;
  box-shadow: none;
}

.compliance-header {
  padding: 10px;
  display: flex;
  justify-content: space-between;
  background-color: transparent;
}

/* Status badges removed - using dot styling instead */

.criticality-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: 500;
}

.criticality-high { background-color: #ffebee; color: #d32f2f; }
.criticality-medium { background-color: #fff3e0; color: #f57c00; }
.criticality-low { background-color: #e8f5e9; color: #388e3c; }

.compliance-body {
  padding: 0;
  background-color: transparent;
}

.compliance-body h3 {
  margin: 0 0 15px 0;
  font-size: 1.1em;
  color: #333;
}

.compliance-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.compliance-detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.9em;
}

.compliance-detail-row .compliance-label {
  color: #666;
}

.compliance-detail-row .compliance-value {
  font-weight: 500;
  color: #333;
}

.compliance-footer {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
  font-size: 0.85em;
  color: #666;
}

.created-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.identifier {
  font-family: monospace;
  color: #888;
}

/* Loading State */
.loading {
  text-align: center;
  padding: 40px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* No Data State */
.no-data {
  text-align: center;
  padding: 40px;
  color: #666;
}

.no-data i {
  font-size: 48px;
  margin-bottom: 20px;
  color: #ddd;
}

.export-buttons {
  margin: 16px 0;
  text-align: right;
}

.export-controls .el-alert {
  margin-top: 10px;
  text-align: left;
}

/* Styles for expanded details view */
.expanded-details {
  margin-top: 16px;
  padding: 16px;
  background-color: transparent;
  border-radius: 0;
  border: none;
}

.expanded-details h4 {
  margin-top: 0;
  margin-bottom: 16px;
  color: #1f2937;
  font-size: 1.1rem;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}

.expanded-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.expanded-section-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background-color: transparent;
  border: none;
  border-radius: 0;
  overflow: hidden;
}

.expanded-section-box h5 {
  margin: 0;
  padding: 10px 15px;
  background-color: transparent;
  color: #374151;
  font-size: 0.9rem;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
}

.expanded-content-box {
  padding: 15px;
  min-height: 40px;
  color: #1f2937;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.95rem;
  line-height: 1.5;
}

/* Add field category headings */
.expanded-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.expanded-details h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 0;
  margin-bottom: 16px;
  color: #1f2937;
  font-size: 1.1rem;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 12px;
}

.expanded-details h4:before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 20px;
  background-color: #4f46e5;
  border-radius: 2px;
}

/* Add "empty value" styling */
.empty-value {
  color: #d1d5db;
  font-style: italic;
  display: inline-block;
  padding: 4px 8px;
  border-radius: 0;
  background-color: transparent;
  border: none;
}

.compliance-expanded-row {
  background-color: transparent !important;
}

.details-row {
  background-color: transparent;
}

.details-row td {
  padding: 20px !important;
  border-bottom: 1px solid #e2e8f0;
}

/* Make expanded boxes slightly larger in list view */
.details-row .expanded-content-box {
  padding: 15px;
  min-height: 50px;
  font-size: 1rem;
}

/* Override grid layout for list view for better readability */
.details-row .expanded-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

/* Add a subtle animation for expanding rows */
.details-row {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Mitigation text formatting */
.mitigation-text {
  font-family: inherit;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
  padding: 0;
  background: none;
  border: none;
  color: inherit;
  font-size: inherit;
  line-height: 1.5;
}

/* Responsive design */
@media (max-width: 768px) {
  .compliance-view-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .compliance-header-actions {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  /* Make table responsive on mobile */
  .compliance-table,
  .compliance-table thead,
  .compliance-table tbody,
  .compliance-table th,
  .compliance-table td,
  .compliance-table tr {
    display: block;
  }
  
  .compliance-table thead tr {
    position: absolute;
    top: -9999px;
    left: -9999px;
  }
  
  .compliance-table tr {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    margin-bottom: 10px;
    padding: 10px;
    background-color: transparent;
  }
  
  .compliance-table td {
    border: none;
    position: relative;
    padding: 8px 10px 8px 40%;
    border-bottom: 1px solid #f3f4f6;
  }
  
  .compliance-table td:before {
    content: attr(data-label) ": ";
    position: absolute;
    left: 6px;
    width: 35%;
    padding-right: 10px;
    white-space: nowrap;
    font-weight: 600;
    color: #4b5563;
  }
  
  .compliance-table td:last-child {
    border-bottom: none;
  }
}

/* Loading and empty states */
.compliance-loading-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #4b5563;
  margin: 40px 0;
  font-size: 1.1rem;
}

.compliance-no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #6b7280;
  text-align: center;
}

.compliance-no-data i {
  font-size: 3rem;
  margin-bottom: 16px;
  color: #d1d5db;
}

.compliance-no-data p {
  font-size: 1.1rem;
  margin: 0;
}

/* Action buttons styling */
.compliance-action-btn {
  padding: 6px 8px;
  font-size: 0.85rem;
  margin-right: 4px;
  border-radius: 4px;
  background: transparent;
  color: #4b5563;
  border: 1px solid #d1d5db;
  cursor: pointer;
  transition: all 0.2s ease;
}

.compliance-action-btn:hover {
  background: rgba(79, 140, 255, 0.1);
  color: #1f2937;
  transform: translateY(-1px);
  border-color: #4f8cff;
}

.compliance-action-btn.primary {
  background-color: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

.compliance-action-btn.primary:hover {
  background-color: #2563eb;
  border-color: #2563eb;
}

.compliance-action-btn i {
  font-size: 0.9rem;
}

/* Enhanced status badges - removed duplicate, using main styling above */

/* Risk and severity indicators */
.compliance-risk-identified {
  color: #dc2626;
  font-weight: 600;
}

.compliance-no-risk {
  color: #059669;
  font-weight: 600;
}

.compliance-severity-high {
  color: #dc2626;
  font-weight: 600;
}

.compliance-severity-medium {
  color: #d97706;
  font-weight: 600;
}

.compliance-severity-low {
  color: #059669;
  font-weight: 600;
}

.risk-identified {
  color: #dc2626;
  font-weight: 600;
}

.no-risk {
  color: #059669;
  font-weight: 600;
}

.severity-high {
  color: #dc2626;
  font-weight: 600;
}

.severity-medium {
  color: #d97706;
  font-weight: 600;
}

.severity-low {
  color: #059669;
  font-weight: 600;
}

/* Breadcrumbs styling */
.breadcrumbs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.breadcrumb-chip {
  background: transparent;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 0.9rem;
  color: #4b5563;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #d1d5db;
}

.breadcrumb-close {
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  color: #6b7280;
  transition: color 0.2s ease;
}

.breadcrumb-close:hover {
  color: #ef4444;
}

/* Modal styles */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: transparent;
  border-radius: 0;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  border: none;
}

.modal-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}

.close-btn:hover {
  color: #ef4444;
}

.modal-body {
  padding: 24px;
}

.no-versions {
  text-align: center;
  color: #6b7280;
  padding: 40px 0;
}

.version-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.version-number {
  font-weight: 600;
  color: #1f2937;
}

.version-badges {
  display: flex;
  gap: 8px;
}

.version-details {
  color: #4b5563;
  font-size: 0.95rem;
}

.version-details p {
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.version-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 0.85rem;
  color: #6b7280;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.version-metadata span {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Column Chooser Styles */
.incident-column-editor-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10000;
  backdrop-filter: blur(4px);
}

.incident-column-editor-modal {
  background: var(--card-bg, white);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
}

.incident-column-editor-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--header-bg, #f9fafb);
}

.incident-column-editor-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #1f2937);
}

.incident-column-editor-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary, #6b7280);
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  line-height: 1;
}

.incident-column-editor-close:hover {
  background: var(--hover-bg, #f3f4f6);
  color: var(--text-primary, #1f2937);
}

.incident-column-editor-modal .search-bar {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  width: 100%;
  box-sizing: border-box;
}

.incident-column-editor-modal .search-bar__icon {
  left: calc(24px + 0.875rem) !important;
}

.incident-column-editor-modal .search-bar__input {
  width: 100%;
  box-sizing: border-box;
}

.incident-column-editor-actions {
  padding: 12px 24px;
  display: flex;
  gap: 12px;
  border-bottom: 1px solid var(--border-color, #e5e7eb);
  background: var(--secondary-bg, #f9fafb);
}

.incident-column-select-btn {
  padding: 6px 12px;
  border: 1px solid var(--border-color, #d1d5db);
  background: var(--btn-bg, white);
  color: var(--text-primary, #1f2937);
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.incident-column-select-btn:hover {
  background: var(--hover-bg, #f3f4f6);
  border-color: var(--primary-color, #4f7cff);
}

.incident-column-editor-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 24px;
  max-height: 400px;
}

.incident-column-editor-item {
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color, #f3f4f6);
}

.incident-column-editor-item:last-child {
  border-bottom: none;
}

.incident-column-editor-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.incident-column-editor-label:hover {
  background: var(--hover-bg, #f9fafb);
}

.incident-column-editor-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--primary-color, #4f7cff);
}

.incident-column-editor-text {
  font-size: 14px;
  color: var(--text-primary, #1f2937);
  font-weight: 500;
}

.incident-column-editor-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--border-color, #e5e7eb);
  display: flex;
  justify-content: flex-end;
  background: var(--footer-bg, #f9fafb);
}

.incident-column-done-btn {
  padding: 10px 24px;
  background: var(--primary-color, #4f7cff);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(79, 124, 255, 0.2);
}

.incident-column-done-btn:hover {
  background: var(--primary-hover, #3b5bdb);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(79, 124, 255, 0.3);
}

.incident-column-editor-empty {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary, #6b7280);
  font-size: 14px;
}
</style>