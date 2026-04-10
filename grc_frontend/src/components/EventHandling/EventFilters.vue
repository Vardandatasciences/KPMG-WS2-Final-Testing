<template>
  <div class="events-filters-container">
    <!-- All filters and export button in one horizontal row -->
    <div class="events-filters-row">
      <!-- Dropdowns -->
      <div class="events-dropdowns-row">
        <div class="events-dropdown-container">
          <label class="events-dropdown-label">Framework</label>
           <CustomDropdown
             :options="[
               { value: '', label: loadingFrameworks ? 'Loading frameworks...' : 'All Frameworks' },
               ...frameworks.map(fw => ({ value: fw.FrameworkName || fw.name, label: fw.FrameworkName || fw.name }))
             ]"
             v-model="selectedFramework"
             :disabled="loadingFrameworks"
             :showClearButton="true"
             :showLabel="false"
             :showSelectedCheckmark="true"
           />
          <div v-if="frameworksError" class="events-dropdown-error">
            {{ frameworksError }}
          </div>
        </div>

        <div class="events-dropdown-container">
          <label class="events-dropdown-label">Module</label>
           <CustomDropdown
             :options="[
               { value: '', label: loadingModules ? 'Loading modules...' : 'All Modules' },
               ...modules.map(mod => ({ value: mod.modulename || mod.name, label: mod.modulename || mod.name }))
             ]"
             v-model="selectedModule"
             :showClearButton="true"
             :disabled="loadingModules"
             :showLabel="false"
             :showSelectedCheckmark="true"
           />
          <div v-if="modulesError" class="events-dropdown-error">
            {{ modulesError }}
          </div>
        </div>

        <div class="events-dropdown-container">
          <label class="events-dropdown-label">Category</label>
          <CustomDropdown
            :options="[
              { value: '', label: loadingCategories ? 'Loading categories...' : 'All Categories' },
              ...categories.map(cat => ({ value: cat, label: cat }))
            ]"
            v-model="selectedCategory"
            :showClearButton="true"
            :disabled="loadingCategories"
            :showLabel="false"
            :showSelectedCheckmark="true"
          />
          <div v-if="categoriesError" class="events-dropdown-error">
            {{ categoriesError }}
          </div>
        </div>

        <div v-if="showAdvanced" class="events-dropdown-container">
          <label class="events-dropdown-label">Owner</label>
          <CustomDropdown
            :options="[
              { value: '', label: loadingOwners ? 'Loading owners...' : 'All Owners' },
              ...owners.map(owner => ({ value: owner, label: owner }))
            ]"
            v-model="selectedOwner"
            :showClearButton="true"
            :disabled="loadingOwners"
            :showLabel="false"
            :showSelectedCheckmark="true"
          />
          <div v-if="ownersError" class="events-dropdown-error">
            {{ ownersError }}
          </div>
        </div>
      </div>
      <!-- Export controls: format dropdown + Export button (hidden when showExport is false, e.g. on Events Dashboard which has its own header export) -->
      <div v-if="showExport" class="export-controls events-export-controls">
        <div class="export-controls-inner">
          <div class="export-select-wrapper" ref="exportSelectRef">
            <div
              class="export-select-trigger"
              :class="{ 'is-open': isExportDropdownOpen }"
              role="button"
              tabindex="0"
              aria-haspopup="listbox"
              :aria-expanded="isExportDropdownOpen"
              aria-label="Select export format"
              @click="isExportDropdownOpen = !isExportDropdownOpen"
              @keydown.enter.space.prevent="isExportDropdownOpen = !isExportDropdownOpen"
            >
              <span class="export-select-text">{{ exportFormatLabel }}</span>
              <span class="export-select-icon"><i class="fas fa-chevron-down"></i></span>
            </div>
            <div v-show="isExportDropdownOpen" class="export-select-menu" role="listbox">
              <div
                v-for="opt in exportFormatOptions"
                :key="opt.value"
                class="export-select-option"
                :class="{ 'is-placeholder': opt.value === '', 'is-selected': exportFormat === opt.value }"
                role="option"
                :aria-selected="exportFormat === opt.value"
                @click="selectExportFormatOption(opt)"
              >
                <span class="export-select-check" v-if="exportFormat === opt.value"><i class="fas fa-check"></i></span>
                <span class="export-select-option-label">{{ opt.label }}</span>
              </div>
            </div>
          </div>
          <button
            class="export-btn"
            type="button"
            :disabled="!exportFormat || isExporting"
            @click="handleExportClick"
          >
            <i class="fas fa-download" aria-hidden="true"></i>
            <span class="export-btn-text">{{ isExporting ? 'Exporting...' : 'Export' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { MODULES, CATEGORIES } from '../../utils/constants'
import { eventService } from '../../services/api'
import CustomDropdown from '@/components/CustomDropdown.vue'
import apiService from '@/services/apiService.js'
import './EventFilters.css'
import '@fortawesome/fontawesome-free/css/all.min.css'
import '@/assets/css/main.css'

export default {
  name: 'EventFilters',
  components: {
    CustomDropdown
  },
  props: {
    showAdvanced: {
      type: Boolean,
      default: true
    },
    showExport: {
      type: Boolean,
      default: true
    },
    selectedFrameworkFromSession: {
      type: String,
      default: null
    }
  },
  emits: ['filter-change', 'export'],
  setup(props, { emit }) {
    // Filter data
    const frameworks = ref([])
    const modules = ref([])
    const categories = ref([])
    const owners = ref([])
    
    // Selected values
    const selectedFramework = ref('')
    const selectedModule = ref('')
    const selectedCategory = ref('')
    const selectedOwner = ref('')
    
    // Loading states
    const loadingFrameworks = ref(false)
    const loadingModules = ref(false)
    const loadingCategories = ref(false)
    const loadingOwners = ref(false)
    
    // Error states
    const frameworksError = ref(null)
    const modulesError = ref(null)
    const categoriesError = ref(null)
    const ownersError = ref(null)

    // Export controls
    const exportFormat = ref('')
    const exportFormatOptions = [
      { value: '', label: 'Select format' },
      { value: 'csv', label: 'CSV' },
      { value: 'xlsx', label: 'Excel (XLSX)' },
      { value: 'pdf', label: 'PDF' }
    ]
    const isExportDropdownOpen = ref(false)
    const exportSelectRef = ref(null)
    const isExporting = ref(false)
    const exportFormatLabel = computed(() => {
      const match = exportFormatOptions.find(opt => opt.value === exportFormat.value)
      return match ? match.label : 'Select format'
    })
    const selectExportFormatOption = (opt) => {
      exportFormat.value = opt.value
      isExportDropdownOpen.value = false
    }
    const handleExportClick = () => {
      if (!exportFormat.value) return
      isExporting.value = true
      emit('export', exportFormat.value)
      setTimeout(() => { isExporting.value = false }, 800)
    }
    const exportDropdownClickOutside = (e) => {
      if (exportSelectRef.value && !exportSelectRef.value.contains(e.target)) {
        isExportDropdownOpen.value = false
      }
    }

    // Fetch frameworks from API (use same endpoint as Policy components)
    const fetchFrameworks = async () => {
      loadingFrameworks.value = true
      frameworksError.value = null
      
      try {
        console.log('🚀 DEBUG: EventFilters fetchFrameworks called - using /api/frameworks/ endpoint')
        
        // Use the same framework endpoint as Policy components to ensure consistency
        const response = await apiService.get('/api/frameworks/', {
          params: {
            _t: Date.now() // Cache busting parameter
          }
        })
        console.log('🔍 DEBUG: Frameworks response in EventFilters:', response)
        
        // Map the response to match the expected format
        frameworks.value = response.map(fw => ({
          FrameworkId: fw.FrameworkId,
          FrameworkName: fw.FrameworkName
        }))
        
        console.log('✅ DEBUG: Frameworks loaded in EventFilters:', frameworks.value.length)
        console.log('📝 DEBUG: Available frameworks:', frameworks.value.map(f => `${f.FrameworkName} (ID: ${f.FrameworkId})`))
        
      } catch (error) {
        console.error('Error fetching frameworks:', error)
        frameworksError.value = 'Error loading frameworks'
        // Fallback to hardcoded frameworks if API fails
        // Note: Must match backend fallback frameworks in get_events_list
        frameworks.value = [
          { FrameworkId: 1, FrameworkName: 'Basel III Framework' }, // Match backend default
          { FrameworkId: 2, FrameworkName: 'NIST' },
          { FrameworkId: 3, FrameworkName: 'ISO 27001' },
          { FrameworkId: 4, FrameworkName: 'COBIT' },
          { FrameworkId: 5, FrameworkName: 'PCI DSS' },
          { FrameworkId: 6, FrameworkName: 'HIPAA' },
          { FrameworkId: 7, FrameworkName: 'SOX' },
          { FrameworkId: 8, FrameworkName: 'GDPR' }
        ]
      } finally {
        loadingFrameworks.value = false
      }
    }

    // Fetch modules from API (same as EventCreation)
    const fetchModules = async () => {
      loadingModules.value = true
      modulesError.value = null
      
      try {
        const response = await eventService.getModules()
        if (response.data.success) {
          modules.value = response.data.modules
        } else {
          modulesError.value = 'Failed to fetch modules'
        }
      } catch (error) {
        console.error('Error fetching modules:', error)
        modulesError.value = 'Error loading modules'
        // Fallback to hardcoded modules if API fails
        modules.value = [
          { moduleid: 1, modulename: 'Policy Management' },
          { moduleid: 2, modulename: 'Compliance Management' },
          { moduleid: 3, modulename: 'Audit Management' },
          { moduleid: 4, modulename: 'Incident Management' },
          { moduleid: 5, modulename: 'Risk Management' }
        ]
      } finally {
        loadingModules.value = false
      }
    }

    // Use categories from constants (same as EventCreation)
    const fetchCategories = async () => {
      loadingCategories.value = true
      categoriesError.value = null
      
      try {
        // Use the same CATEGORIES constant as EventCreation
        categories.value = CATEGORIES
      } catch (error) {
        console.error('Error loading categories:', error)
        categoriesError.value = 'Error loading categories'
        categories.value = CATEGORIES // Fallback to constants
      } finally {
        loadingCategories.value = false
      }
    }

    // Fetch all users from database
    const fetchOwners = async () => {
      loadingOwners.value = true
      ownersError.value = null
      
      try {
        console.log('🔄 DEBUG: Fetching users for owner dropdown...')
        const response = await eventService.getUsers()
        console.log('🔍 DEBUG: Users API response:', response.data)
        
        if (response.data.success) {
          console.log('✅ DEBUG: Users fetched successfully:', response.data.users)

          // Support multiple backend user shapes safely.
          const formattedUsers = (response.data.users || []).map(user => {
            const fullName = (
              user.name ||
              `${user.first_name || user.FirstName || ''} ${user.last_name || user.LastName || ''}`
            ).trim()
            console.log('👤 DEBUG: Formatting user:', user, '-> Full name:', fullName)
            return fullName
          }).filter(Boolean)

          // Deduplicate and sort for stable dropdown UX.
          const uniqueUsers = [...new Set(formattedUsers)].sort((a, b) => a.localeCompare(b))
          
          console.log('📝 DEBUG: Formatted users for dropdown:', uniqueUsers)
          owners.value = uniqueUsers
        } else {
          console.error('❌ DEBUG: API returned success: false:', response.data)
          ownersError.value = response.data.error || 'Failed to fetch users'
        }
      } catch (error) {
        console.error('❌ DEBUG: Error fetching owners:', error)
        console.error('❌ DEBUG: Error response:', error.response?.data)
        ownersError.value = `Error loading owners: ${error.message}`
        // Fallback to hardcoded owners
        owners.value = ['John Mathews', 'Rahul Khanna', 'Priya Sinha']
      } finally {
        loadingOwners.value = false
      }
    }


    // Emit filter changes
    const emitFilterChange = () => {
      const filterData = {
        framework: selectedFramework.value,
        module: selectedModule.value,
        category: selectedCategory.value,
        owner: selectedOwner.value
      }
      emit('filter-change', filterData)
    }

    // Watch for filter changes and emit them
    watch([selectedFramework, selectedModule, selectedCategory, selectedOwner], () => {
      emitFilterChange()
    }, { immediate: true })

    // Watch for selected framework from session and update the dropdown
    watch(() => props.selectedFrameworkFromSession, (newFrameworkId) => {
      console.log('🔍 DEBUG: Framework watcher triggered with ID:', newFrameworkId)
      console.log('🔍 DEBUG: Available frameworks count:', frameworks.value.length)
      console.log('🔍 DEBUG: Available frameworks:', frameworks.value.map(f => `${f.FrameworkName} (ID: ${f.FrameworkId})`))
      
      if (newFrameworkId) {
        // Find the framework name from the frameworks list - try multiple matching approaches
        let framework = frameworks.value.find(fw => fw.FrameworkId == newFrameworkId)
        console.log('🔍 DEBUG: Looking for framework ID:', newFrameworkId, 'Type:', typeof newFrameworkId)
        console.log('🔍 DEBUG: Found framework (loose match):', framework)
        
        // If not found with loose match, try strict string comparison
        if (!framework) {
          framework = frameworks.value.find(fw => String(fw.FrameworkId) === String(newFrameworkId))
          console.log('🔍 DEBUG: Found framework (strict string match):', framework)
        }
        
        // If still not found, try number comparison
        if (!framework) {
          framework = frameworks.value.find(fw => Number(fw.FrameworkId) === Number(newFrameworkId))
          console.log('🔍 DEBUG: Found framework (number match):', framework)
        }
        
        if (framework) {
          selectedFramework.value = framework.FrameworkName
          console.log('✅ DEBUG: Updated framework dropdown to show selected framework:', framework.FrameworkName)
          console.log('✅ DEBUG: selectedFramework.value is now:', selectedFramework.value)
        } else {
          console.log('⚠️ DEBUG: Could not find framework with ID:', newFrameworkId)
          console.log('⚠️ DEBUG: Available framework IDs:', frameworks.value.map(fw => `${fw.FrameworkId} (type: ${typeof fw.FrameworkId})`))
          console.log('⚠️ DEBUG: Available framework names:', frameworks.value.map(fw => fw.FrameworkName))
          
          // If we can't find by ID, try to find by name (fallback)
          const frameworkByName = frameworks.value.find(fw => fw.FrameworkName === 'aaaaaaaaaaawerfg')
          if (frameworkByName) {
            console.log('🔄 DEBUG: Using fallback - found framework by name:', frameworkByName)
            selectedFramework.value = frameworkByName.FrameworkName
          }
        }
      } else {
        selectedFramework.value = ''
        console.log('ℹ️ DEBUG: Reset framework dropdown to "All Frameworks"')
      }
    }, { immediate: true })

    // Also watch for frameworks to be loaded and then set the selected framework
    watch(frameworks, (newFrameworks) => {
      console.log('🔍 DEBUG: Frameworks loaded, count:', newFrameworks.length)
      console.log('🔍 DEBUG: Available frameworks:', newFrameworks.map(f => `${f.FrameworkName} (ID: ${f.FrameworkId})`))
      console.log('🔍 DEBUG: Selected framework from session:', props.selectedFrameworkFromSession)
      
      if (newFrameworks.length > 0 && props.selectedFrameworkFromSession) {
        // Try multiple matching approaches
        let framework = newFrameworks.find(fw => fw.FrameworkId == props.selectedFrameworkFromSession)
        console.log('🔍 DEBUG: Looking for framework ID:', props.selectedFrameworkFromSession, 'in loaded frameworks')
        console.log('🔍 DEBUG: Found framework (loose match):', framework)
        
        // If not found with loose match, try strict string comparison
        if (!framework) {
          framework = newFrameworks.find(fw => String(fw.FrameworkId) === String(props.selectedFrameworkFromSession))
          console.log('🔍 DEBUG: Found framework (strict string match):', framework)
        }
        
        // If still not found, try number comparison
        if (!framework) {
          framework = newFrameworks.find(fw => Number(fw.FrameworkId) === Number(props.selectedFrameworkFromSession))
          console.log('🔍 DEBUG: Found framework (number match):', framework)
        }
        
        if (framework) {
          selectedFramework.value = framework.FrameworkName
          console.log('✅ DEBUG: Updated framework dropdown after frameworks loaded:', framework.FrameworkName)
          console.log('✅ DEBUG: selectedFramework.value is now:', selectedFramework.value)
        } else {
          console.log('⚠️ DEBUG: Could not find framework with ID:', props.selectedFrameworkFromSession)
          console.log('⚠️ DEBUG: Available framework IDs:', newFrameworks.map(fw => `${fw.FrameworkId} (type: ${typeof fw.FrameworkId})`))
          console.log('⚠️ DEBUG: Available framework names:', newFrameworks.map(fw => fw.FrameworkName))
          
          // If we can't find by ID, try to find by name (fallback)
          const frameworkByName = newFrameworks.find(fw => fw.FrameworkName === 'aaaaaaaaaaawerfg')
          if (frameworkByName) {
            console.log('🔄 DEBUG: Using fallback - found framework by name:', frameworkByName)
            selectedFramework.value = frameworkByName.FrameworkName
          }
        }
      }
    }, { immediate: true })

    // Fetch all filter data on component mount
    onMounted(async () => {
      await fetchFrameworks()
      fetchModules()
      fetchCategories()
      fetchOwners()
      
      // Force update the selected framework after frameworks are loaded
      if (props.selectedFrameworkFromSession) {
        console.log('🔄 DEBUG: Force updating framework selection on mount')
        const framework = frameworks.value.find(fw => fw.FrameworkId == props.selectedFrameworkFromSession)
        if (framework) {
          selectedFramework.value = framework.FrameworkName
          console.log('✅ DEBUG: Force updated framework dropdown on mount:', framework.FrameworkName)
        }
      }
      document.addEventListener('click', exportDropdownClickOutside)
    })

    onUnmounted(() => {
      document.removeEventListener('click', exportDropdownClickOutside)
    })

    return {
      frameworks,
      modules,
      categories,
      owners,
      selectedFramework,
      selectedModule,
      selectedCategory,
      selectedOwner,
      loadingFrameworks,
      loadingModules,
      loadingCategories,
      loadingOwners,
      frameworksError,
      modulesError,
      categoriesError,
      ownersError,
      MODULES,
      CATEGORIES,
      exportFormat,
      exportFormatOptions,
      exportFormatLabel,
      isExportDropdownOpen,
      exportSelectRef,
      isExporting,
      selectExportFormatOption,
      handleExportClick
    }
  }
}
</script>

