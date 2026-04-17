<template>
  <div class="dashboard-container incident-performance-dashboard incident-dashboard-container">
    <div class="dashboard-header">
      <div class="dashboard-header-left">
        <button class="back-arrow-btn" @click="goBackToIncident" title="Back to Incident Management">
          <i class="fas fa-arrow-left"></i>
        </button>
        <div>
          <h1>Incident Dashboard</h1>
          <p v-if="dataSourceMessage" class="data-source-message">{{ dataSourceMessage }}</p>
        </div>
      </div>
      <div class="export-controls">
        <div class="export-controls-inner">
          <!-- Select format: custom dropdown from main.css (.export-select-*) -->
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
            :disabled="!exportFormat || isDownloading"
            @click="exportDashboard"
          >
            <i class="fas fa-download" aria-hidden="true"></i>
            <span class="export-btn-text">{{ isDownloading ? 'Exporting...' : 'Export' }}</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- Framework Filter -->
    <div class="framework-filter" style="margin-bottom: 4px;">
      <!-- Single Row: All Four Filters -->
      <div class="filter-row">
        <div class="filter-group">
          <label class="dropdown-external-label">Filter by Framework:</label>
          <CustomDropdown
            v-model="selectedFramework"
            :options="frameworkOptions"
            :showClearButton="true"
            @change="onFrameworkChange"
            :config="{ label: 'All Frameworks' }"
            :showLabel="false"
            :disabled="loadingFrameworks"
          />
        </div>
        <div class="filter-group">
          <label class="dropdown-external-label">Filter by Time Range:</label>
          <CustomDropdown
            v-model="selectedTimeRange"
            :options="timeRangeOptions"
            :showClearButton="true"
            @change="fetchDashboardData"
            :config="{ label: 'Time Range' }"
            :showLabel="false"
          />
        </div>
        <div class="filter-group">
          <label class="dropdown-external-label">Filter by Category:</label>
          <CustomDropdown
            v-model="selectedCategory"
            :options="categoryOptions"
            :showClearButton="true"
            @change="fetchDashboardData"
            :config="{ label: 'Category' }"
            :showLabel="false"
          />
        </div>
        <div class="filter-group">
          <label class="dropdown-external-label">Filter by Priority:</label>
          <CustomDropdown
            v-model="selectedPriority"
            :options="priorityOptions"
            :showClearButton="true"
            @change="fetchDashboardData"
            :config="{ label: 'Priority' }"
            :showLabel="false"
          />
        </div>
      </div>
    </div>
    
    <div class="kpi-grid">
      <div
        v-for="card in kpiCards"
        :key="card.id"
        class="kpi-card"
      >
        <div class="kpi-card-icon" :class="card.iconClass">
          <i :class="card.icon"></i>
        </div>
        <div class="kpi-card-body">
          <h3 class="kpi-card-title">{{ card.title }}</h3>
          <div class="kpi-card-value">
            {{ card.value }}
          </div>
          <div
            class="kpi-card-subtitle"
            :class="{
              'kpi-change-positive': card.trend === 'up',
              'kpi-change-negative': card.trend === 'down'
            }"
          >
            {{ card.subtitle }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- Charts Grid - 2x2 Layout -->
    <div class="global-dashboard-charts-grid">
      <!-- Chart 1: Incident vs Status (Donut Chart) -->
      <div class="global-dashboard-chart-card">
        <div class="global-dashboard-chart-header">
          <h3 class="global-dashboard-chart-title">Incident vs Status</h3>
          <div class="global-dashboard-chart-icon" style="color: #4f6cff;">
            <i class="fas fa-chart-pie"></i>
          </div>
        </div>
        <div class="global-dashboard-chart-container">
          <canvas id="statusChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 2: Incident vs Origin (Bar Chart) -->
      <div class="global-dashboard-chart-card">
        <div class="global-dashboard-chart-header">
          <h3 class="global-dashboard-chart-title">Incident vs Origin</h3>
          <div class="global-dashboard-chart-icon" style="color: #4f6cff;">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="global-dashboard-chart-container">
          <canvas id="originChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 3: Incident vs Risk Category (Line Chart) -->
      <div class="global-dashboard-chart-card">
        <div class="global-dashboard-chart-header">
          <h3 class="global-dashboard-chart-title">Incident vs Risk Category</h3>
          <div class="global-dashboard-chart-icon" style="color: #4f6cff;">
            <i class="fas fa-chart-line"></i>
          </div>
        </div>
        <div class="global-dashboard-chart-container">
          <canvas id="categoryChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 4: Incident vs Risk Priority (Bar Chart) -->
      <div class="global-dashboard-chart-card">
        <div class="global-dashboard-chart-header">
          <h3 class="global-dashboard-chart-title">Incident vs Risk Priority</h3>
          <div class="global-dashboard-chart-icon" style="color: #4f6cff;">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="global-dashboard-chart-container">
          <canvas id="priorityChart"></canvas>
        </div>
      </div>
    </div>
    
    <!-- Recent Incidents Section -->
    <div class="recent-section">
      <div class="recent-activity">
        <div class="activity-header">
          <h2>Recent Incidents</h2>
        </div>
        <div class="activity-list">
          <div v-for="(incident, index) in recentIncidents" :key="index" class="activity-item">
            <div class="icon-container" :class="getIncidentIconClass(incident)">
              <i :class="getIncidentIcon(incident)" class="icon-md"></i>
            </div>
            <div class="activity-details">
              <h4>{{ incident.IncidentTitle }}</h4>
              <p>{{ truncateDescription(incident.Description, 100) }}</p>
              <div class="activity-meta">
                <span class="activity-tag origin-tag">{{ incident.origin_text }}</span>
                <span v-if="incident.status_class" class="activity-tag status-tag" :class="incident.status_class">{{ incident.Status }}</span>
                <span class="activity-time">{{ formatDate(incident.CreatedAt) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import '@fortawesome/fontawesome-free/css/all.min.css'
import apiService from '@/services/apiService.js'
import { API_ENDPOINTS } from '@/config/api.js'
import { PopupModal } from '@/modules/popup'
import { AccessUtils } from '@/utils/accessUtils'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import incidentDataService from '../../services/incidentService.js' // Updated: Use consistent naming
import CustomDropdown from '@/components/CustomDropdown.vue'
import { convertColorForColorblind as convertColorFromUtil } from '@/utils/colorblindness'
import { getExplicitFrameworkId } from '@/utils/frameworkContextStorage.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend
)

export default {
  name: 'IncidentPerformanceDashboard',
  components: {
    PopupModal,
    CustomDropdown
  },
  data() {
    return {
      // Export controls (shared styles from main.css)
      exportFormat: '',
      exportFormatOptions: [
        { value: '', label: 'Select format' },
        { value: 'pdf', label: 'PDF (.pdf)' },
        { value: 'png', label: 'Image (.png)' }
      ],
      isExportDropdownOpen: false,
      selectedFramework: '',
      selectedTimeRange: 'Last 6 Months',
      selectedCategory: 'All Categories',
      selectedPriority: 'All Priorities',
      frameworks: [],
      loadingFrameworks: false,
      isDownloading: false,
      dataSourceMessage: '', // Data source indicator
      dashboardData: {
        status_counts: {
          scheduled: 0,
          approved: 0,
          resolved: 0,
          rejected: 0
        },
        total_count: 0,
        change_percentage: 0,
        resolution_rate: 0
      },
      charts: {
        statusChart: null,
        originChart: null,
        categoryChart: null,
        priorityChart: null
      },
      chartData: {
        status: null,
        origin: null,
        category: null,
        priority: null
      },
      recentIncidents: [],
      // Colorblindness support
      colorblindMode: null,
      colorblindObserver: null,
      isComponentAlive: false
    }
  },
  computed: {
    frameworkOptions() {
      return [
        { value: '', label: 'All Frameworks' },
        ...this.frameworks.map(fw => ({ value: fw.id, label: fw.name }))
      ];
    },
    timeRangeOptions() {
      return [
        { value: 'Last 6 Months', label: 'Last 6 Months' },
        { value: 'Last 3 Months', label: 'Last 3 Months' },
        { value: 'Last Month', label: 'Last Month' },
        { value: 'Last Week', label: 'Last Week' }
      ];
    },
    categoryOptions() {
      return [
        { value: 'All Categories', label: 'All Categories' },
        { value: 'Security', label: 'Security' },
        { value: 'Compliance', label: 'Compliance' },
        { value: 'Operational', label: 'Operational' }
      ];
    },
    priorityOptions() {
      return [
        { value: 'All Priorities', label: 'All Priorities' },
        { value: 'High', label: 'High' },
        { value: 'Medium', label: 'Medium' },
        { value: 'Low', label: 'Low' }
      ];
    },
    exportFormatLabel() {
      const match = this.exportFormatOptions.find(
        opt => opt.value === this.exportFormat
      )
      return match ? match.label : 'Select format'
    },
    kpiCards() {
      const total = this.dashboardData.total_count || 0
      const change = this.dashboardData.change_percentage || 0
      const scheduled = this.dashboardData.status_counts?.scheduled || 0
      const rejected = this.dashboardData.status_counts?.rejected || 0
      const approved = this.dashboardData.status_counts?.approved || 0

      return [
        {
          id: 'total',
          icon: 'fas fa-exclamation-circle',
          iconClass: 'kpi-icon-total',
          title: 'Total Incidents',
          value: total,
          trend: change > 0 ? 'up' : change < 0 ? 'down' : 'neutral',
          subtitle: `${change > 0 ? '+' : ''}${change}% from last period`
        },
        {
          id: 'open',
          icon: 'fas fa-clipboard-list',
          iconClass: 'kpi-icon-open',
          title: 'Open Incidents',
          value: scheduled,
          trend: 'neutral',
          subtitle: 'Awaiting resolution'
        },
        {
          id: 'rejected',
          icon: 'fas fa-ban',
          iconClass: 'kpi-icon-rejected',
          title: 'Rejected',
          value: rejected,
          trend: 'neutral',
          subtitle: 'Rejected incidents'
        },
        {
          id: 'approved',
          icon: 'fas fa-check-circle',
          iconClass: 'kpi-icon-approved',
          title: 'Approved',
          value: approved,
          trend: 'neutral',
          subtitle: 'Approved incidents'
        }
      ]
    }
  },
  async mounted() {
    console.log('🚀 [IncidentPerformanceDashboard] Component mounted');
    this.isComponentAlive = true

    // Initialize colorblindness tracking
    this.initColorblindnessTracking()

    // Close export dropdown when clicking outside (uses main.css export-select-wrapper)
    this._exportDropdownClickOutside = (e) => {
      if (this.$refs.exportSelectRef && !this.$refs.exportSelectRef.contains(e.target)) {
        this.isExportDropdownOpen = false
      }
    }
    document.addEventListener('click', this._exportDropdownClickOutside)

    // Recent incidents can load in parallel; resolve framework + selection first to avoid
    // duplicate dashboard/chart API bursts (previously: fetchDashboardData + fetchSelectedFramework both fetched).
    this.fetchRecentIncidents()
    try {
      await this.fetchFrameworks()
      await this.fetchSelectedFramework()
    } catch (e) {
      console.warn('[IncidentPerformanceDashboard] Framework load failed:', e)
    }
    await this.fetchDashboardData()
  },
  beforeUnmount() {
    this.isComponentAlive = false
    document.removeEventListener('click', this._exportDropdownClickOutside)
    this.destroyAllCharts()
    // Clean up colorblindness observer
    if (this.colorblindObserver) {
      this.colorblindObserver.disconnect()
    }
  },
  beforeRouteLeave(to, from, next) {
    this.destroyAllCharts()
    next()
  },
  methods: {
    // Colorblindness support methods
    initColorblindnessTracking() {
      // Get current colorblindness mode
      this.colorblindMode = this.getColorblindMode()
      console.log('🎨 [IncidentPerformanceDashboard] Initial colorblindness mode:', this.colorblindMode)
      
      // Watch for colorblindness mode changes
      this.colorblindObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'attributes' && mutation.attributeName === 'data-colorblind') {
            const newMode = this.getColorblindMode()
            if (newMode !== this.colorblindMode) {
              console.log('🎨 [IncidentPerformanceDashboard] Colorblindness mode changed:', newMode, 'Previous:', this.colorblindMode)
              this.colorblindMode = newMode
              // Re-render all charts with new colors
              this.$nextTick(() => {
                console.log('🎨 [IncidentPerformanceDashboard] Re-rendering charts with new colorblindness mode:', this.colorblindMode)
                this.safeUpdateAllCharts()
              })
            }
          }
        })
      })
      
      // Start observing
      this.colorblindObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-colorblind']
      })
      console.log('🎨 [IncidentPerformanceDashboard] Colorblindness observer initialized')
    },
    
    getColorblindMode() {
      const html = document.documentElement
      return html.getAttribute('data-colorblind') || null
    },
    
    // Convert rgba/rgb to hex (helper for color conversion)
    rgbaToHex(rgba) {
      if (!rgba) return rgba
      if (rgba.startsWith('#')) return rgba.toLowerCase()
      const match = rgba.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/i)
      if (!match) return rgba
      const r = parseInt(match[1])
      const g = parseInt(match[2])
      const b = parseInt(match[3])
      return '#' + [r, g, b].map(x => {
        const hex = x.toString(16)
        return hex.length === 1 ? '0' + hex : hex
      }).join('').toLowerCase()
    },
    
    // Convert hex to rgba with opacity
    hexToRgba(hex, opacity = 0.6) {
      if (!hex || !hex.startsWith('#')) return hex
      const r = parseInt(hex.slice(1, 3), 16)
      const g = parseInt(hex.slice(3, 5), 16)
      const b = parseInt(hex.slice(5, 7), 16)
      return `rgba(${r}, ${g}, ${b}, ${opacity})`
    },
    
    // Convert color based on colorblindness mode
    // Use the shared utility function - this ensures all colors come from Colourblindness.css CSS variables
    convertColorForColorblind(color, opacity = 0.6) {
      const converted = convertColorFromUtil(color);
      
      // Handle opacity for rgba colors
      if (opacity !== 1 && (color.startsWith('rgba') || (color.startsWith('rgb') && !color.startsWith('#')))) {
        if (converted.startsWith('#')) {
          return this.hexToRgba(converted, opacity);
        }
      }
      
      return converted;
    },
    
    destroyAllCharts() {
      Object.values(this.charts).forEach(chart => {
        if (chart) {
          chart.destroy()
        }
      })
      this.charts = {
        statusChart: null,
        originChart: null,
        categoryChart: null,
        priorityChart: null
      }
    },
    
    async fetchFrameworks() {
      try {
        this.loadingFrameworks = true
        console.log('🔍 Fetching frameworks...')
        let responseData
        try {
          responseData = await apiService.get('/api/compliance/frameworks/public/', {}, { timeout: 30000, skipCache: true })
        } catch (primaryError) {
          console.warn('⚠️ Primary frameworks endpoint failed, trying approved-active fallback...', primaryError?.message || primaryError)
          // Fallback endpoint used elsewhere in app and is more reliable under load.
          responseData = await apiService.get('/api/frameworks/approved-active/', {}, { timeout: 30000, skipCache: true })
        }
        console.log('✅ Frameworks API response:', responseData)
        
        // Handle the API response format
        let frameworksData = []
        if (responseData && responseData.success && responseData.frameworks) {
          frameworksData = responseData.frameworks
        } else if (responseData && responseData.success && Array.isArray(responseData.data)) {
          frameworksData = responseData.data
        } else if (responseData && responseData.success && Array.isArray(responseData.framework_data)) {
          frameworksData = responseData.framework_data
        } else if (responseData && Array.isArray(responseData)) {
          frameworksData = responseData
        } else if (responseData && responseData.frameworks) {
          frameworksData = responseData.frameworks
        } else {
          console.error('Unexpected frameworks response format:', responseData)
          this.frameworks = []
          this.loadingFrameworks = false
          return
        }
        
        // Filter to only show active frameworks
        const activeFrameworks = frameworksData.filter(fw => {
          if (!fw) return false
          const status = fw.ActiveInactive || fw.status || fw.activeInactive || '';
          return status.toLowerCase() === 'active';
        });
        
        this.frameworks = activeFrameworks.map(framework => ({
          id: framework.id || framework.FrameworkId,
          name: framework.name || framework.FrameworkName || 'Unknown Framework'
        }))
        
        console.log('✅ Processed frameworks:', this.frameworks)
        
        // After frameworks are loaded, try to set the selected framework
        await this.setSelectedFrameworkIfAvailable()
      } catch (error) {
        console.error('❌ Error fetching frameworks:', error)
        console.error('❌ Error details:', error.response?.data || error.message)
        this.frameworks = []
      } finally {
        this.loadingFrameworks = false
      }
    },

    async fetchSelectedFramework() {
      try {
        console.log('🔍 Fetching selected framework from home page...')
        const responseData = await apiService.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('✅ Selected framework API response:', responseData)
        
        if (responseData && responseData.frameworkId) {
          this.selectedFramework = responseData.frameworkId
          console.log('✅ Set selected framework ID:', this.selectedFramework)
          
          if (this.frameworks.length > 0) {
            await this.setSelectedFrameworkIfAvailable()
          } else {
            console.log('⚠️ Frameworks not loaded yet, will refresh data after frameworks are loaded')
          }
        } else {
          console.log('⚠️ No framework selected or frameworkId not found in response')
          // UX-only fallback; server must authorize and scope data by tenant/session (never trust this ID for authz).
          const storedFrameworkId = getExplicitFrameworkId()
          if (storedFrameworkId) {
            this.selectedFramework = storedFrameworkId
            console.log('✅ Using framework ID from localStorage:', this.selectedFramework)
            
            if (this.frameworks.length > 0) {
              await this.setSelectedFrameworkIfAvailable()
            }
          }
        }
      } catch (error) {
        console.warn('⚠️ Could not fetch selected framework:', error)
        // Try localStorage fallback
        const storedFrameworkId = getExplicitFrameworkId()
        if (storedFrameworkId) {
          this.selectedFramework = storedFrameworkId
          console.log('✅ Using framework ID from localStorage as fallback:', this.selectedFramework)
          
          if (this.frameworks.length > 0) {
            await this.setSelectedFrameworkIfAvailable()
          }
        }
      }
    },

    async setSelectedFrameworkIfAvailable() {
      // If we already have a selected framework, make sure it exists in the frameworks list
      if (this.selectedFramework && this.frameworks.length > 0) {
        const frameworkExists = this.frameworks.some(f => f.id == this.selectedFramework)
        if (!frameworkExists) {
          console.warn('⚠️ Selected framework not found in frameworks list, clearing selection')
          this.selectedFramework = ''
        } else {
          const selectedFrameworkName = this.frameworks.find(f => f.id == this.selectedFramework)?.name
          console.log('✅ Selected framework confirmed in frameworks list:', this.selectedFramework, '-', selectedFrameworkName)
        }
      } else if (!this.selectedFramework && this.frameworks.length > 0) {
        console.log('ℹ️ No framework selected, will load data for all frameworks')
      }
    },
    
    async fetchRecentIncidents() {
      try {
        console.log('🔍 [IncidentPerformanceDashboard] Checking for cached recent incidents...');

        // Check if prefetch is in progress or cache is available
        if (!window.incidentDataFetchPromise && !incidentDataService.hasValidIncidentsCache()) {
          console.log('🚀 [IncidentPerformanceDashboard] Starting incident prefetch (user navigated directly)...');
          window.incidentDataFetchPromise = incidentDataService.fetchAllIncidentData();
        }

        // Wait for prefetch if it's in progress
        if (window.incidentDataFetchPromise) {
          console.log('⏳ [IncidentPerformanceDashboard] Waiting for incident prefetch to complete...');
          try {
            await window.incidentDataFetchPromise;
            console.log('✅ [IncidentPerformanceDashboard] Incident prefetch completed');
          } catch (prefetchError) {
            console.warn('⚠️ [IncidentPerformanceDashboard] Incident prefetch failed, will fetch directly from API', prefetchError);
          }
        }

        // Use cached incidents if available - get most recent from cache
        if (incidentDataService.hasValidIncidentsCache()) {
          console.log('✅ [IncidentPerformanceDashboard] Using cached incidents for recent incidents');
          const cachedIncidents = incidentDataService.getData('incidents') || [];
          
          // Sort by date (most recent first) and take first 3
          const recentIncidents = cachedIncidents
            .sort((a, b) => {
              const dateA = new Date(a.CreatedAt || a.created_at || 0);
              const dateB = new Date(b.CreatedAt || b.created_at || 0);
              return dateB - dateA;
            })
            .slice(0, 3);
          
          this.recentIncidents = recentIncidents.map(incident => {
            // Add status class
            let statusClass = '';
            if (incident.Status) {
              const status = incident.Status.toLowerCase();
              if (status.includes('rejected')) {
                statusClass = 'rejected';
              } else if (status.includes('approved')) {
                statusClass = 'approved';
              } else if (status.includes('scheduled')) {
                statusClass = 'scheduled';
              }
            }
            
            // Add origin info
            let originText = incident.Origin || 'Unknown';
            
            return {
              ...incident,
              status_class: statusClass,
              origin_text: originText
            }
          });
          return;
        }
        
        // Fallback: Fetch directly from API
        console.log('⚠️ [IncidentPerformanceDashboard] No cached incidents, fetching recent incidents from API...');
        const recentBody = await apiService.get('/api/incidents/recent/', { limit: 3 })
        if (recentBody && recentBody.success) {
          this.recentIncidents = recentBody.incidents.map(incident => {
            // Add status class
            let statusClass = '';
            if (incident.Status) {
              const status = incident.Status.toLowerCase();
              if (status.includes('rejected')) {
                statusClass = 'rejected';
              } else if (status.includes('approved')) {
                statusClass = 'approved';
              } else if (status.includes('scheduled')) {
                statusClass = 'scheduled';
              }
            }
            
            // Add origin info
            let originText = incident.Origin || 'Unknown';
            
            return {
              ...incident,
              status_class: statusClass,
              origin_text: originText
            }
          })
        } else {
          console.error('Failed to fetch recent incidents')
          this.recentIncidents = []
        }
      } catch (error) {
        console.error('Error fetching recent incidents:', error)
        
        // Check for access denied first
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        this.recentIncidents = []
      }
    },
         async fetchDashboardData() {
      // Start timing
      const startTime = performance.now();
      
      // Helper function to format time taken (defined outside try/catch for scope access)
      const getTimeTaken = () => {
        const elapsed = performance.now() - startTime;
        if (elapsed < 100) {
          return `${elapsed.toFixed(0)}ms`;
        } else {
          return `${(elapsed / 1000).toFixed(2)}s`;
        }
      };
      
      try {
        console.log('🔄 [IncidentPerformanceDashboard] fetchDashboardData called')

        // Check which filters are active
        const hasFrameworkFilter = this.selectedFramework && this.selectedFramework !== '';
        const hasTimeRangeFilter = this.selectedTimeRange && this.selectedTimeRange !== 'Last 6 Months';
        const hasCategoryFilter = this.selectedCategory && this.selectedCategory !== 'All Categories';
        const hasPriorityFilter = this.selectedPriority && this.selectedPriority !== 'All Priorities';
        
        // Complex filters that require API calls (time range requires server-side date filtering)
        const hasComplexFilters = hasTimeRangeFilter;
        
        // Check if prefetch is in progress or cache is available
        if (!window.incidentDataFetchPromise && !incidentDataService.hasValidIncidentsCache()) {
          console.log('🚀 [IncidentPerformanceDashboard] Starting incident prefetch (user navigated directly)...');
          window.incidentDataFetchPromise = incidentDataService.fetchAllIncidentData();
        }

        // Wait for prefetch if it's in progress (but don't block too long)
        if (window.incidentDataFetchPromise) {
          console.log('⏳ [IncidentPerformanceDashboard] Waiting for incident prefetch to complete...');
          try {
            await Promise.race([
              window.incidentDataFetchPromise,
              new Promise(resolve => setTimeout(resolve, 2000)) // Max 2 seconds wait
            ]);
            console.log('✅ [IncidentPerformanceDashboard] Incident prefetch completed or timeout');
          } catch (prefetchError) {
            console.warn('⚠️ [IncidentPerformanceDashboard] Incident prefetch failed, will use cache or API', prefetchError);
          }
        }

        // PRIORITY 1: Try to load from prefetched dashboard cache (no filters or simple filters)
        if (!hasComplexFilters) {
          // Check if we have cached dashboard summary data
          const cachedDashboard = incidentDataService.getKPIData('dashboardSummary');
          const cachedStatusChart = incidentDataService.getKPIData('statusChart');
          const cachedOriginChart = incidentDataService.getKPIData('originChart');
          const cachedCategoryChart = incidentDataService.getKPIData('categoryChart');
          const cachedPriorityChart = incidentDataService.getKPIData('priorityChart');
          
          // If ALL dashboard and chart data is cached, use it immediately
          if (cachedDashboard && cachedStatusChart && cachedOriginChart && cachedCategoryChart && cachedPriorityChart) {
            console.log('⚡⚡⚡ [IncidentPerformanceDashboard] ALL dashboard & chart data in cache - INSTANT LOAD!');
            
            // Apply filters if needed
            const filters = {};
            if (hasFrameworkFilter) filters.frameworkId = this.selectedFramework;
            if (hasCategoryFilter) filters.category = this.selectedCategory;
            if (hasPriorityFilter) filters.priority = this.selectedPriority;
            
            // If filters are applied, filter the cached data
            let dashboardData = cachedDashboard;
            let statusChart = cachedStatusChart;
            let originChart = cachedOriginChart;
            let categoryChart = cachedCategoryChart;
            let priorityChart = cachedPriorityChart;
            
            if (hasFrameworkFilter || hasCategoryFilter || hasPriorityFilter) {
              console.log('🔍 Applying filters to cached data:', filters);
              // Recompute from cached incidents with filters
              const basicKPIs = incidentDataService.computeBasicKPIsFromCache(filters);
              dashboardData = {
                data: {
                  summary: {
                    status_counts: basicKPIs.statusCounts,
                    total_count: basicKPIs.totalCount,
                    change_percentage: basicKPIs.change_percentage,
                    resolution_rate: basicKPIs.resolution_rate
                  }
                },
                success: true
              };
              
              statusChart = { chartData: incidentDataService.computeChartDataFromCache('Status', filters), success: true };
              originChart = { chartData: incidentDataService.computeChartDataFromCache('Origin', filters), success: true };
              categoryChart = { chartData: incidentDataService.computeChartDataFromCache('RiskCategory', filters), success: true };
              priorityChart = { chartData: incidentDataService.computeChartDataFromCache('RiskPriority', filters), success: true };
            }
            
            // Set dashboard data
            const summary = dashboardData.data?.summary || {};
            this.dashboardData = {
              status_counts: summary.status_counts || {},
              total_count: summary.total_count || 0,
              change_percentage: summary.change_percentage || 0,
              resolution_rate: summary.resolution_rate || 0
            };
            
            // Set chart data
            this.chartData = {
              status: statusChart.chartData || statusChart,
              origin: originChart.chartData || originChart,
              category: categoryChart.chartData || categoryChart,
              priority: priorityChart.chartData || priorityChart
            };
            
            // Set data source message with timing
            const timeTaken = getTimeTaken();
            this.dataSourceMessage = `✅ Loaded ${this.dashboardData.total_count} incidents from cache (prefetched on Home page) - ${timeTaken}`;
            
            // Update charts
            await this.$nextTick();
            await this.safeUpdateAllCharts();
            
            console.log(`✅✅✅ [IncidentPerformanceDashboard] Dashboard loaded from cache - ${timeTaken}`);
            return;
          }
        }
        
        // PRIORITY 2: Check if we can compute dashboard data from cached incidents
        // We can use cache if: no complex filters (time range) AND we have cached incidents
        if (!hasComplexFilters && incidentDataService.hasValidIncidentsCache()) {
          console.log('⚡ [IncidentPerformanceDashboard] Computing dashboard data from cached incidents - INSTANT!');
          
          // Prepare filters for client-side filtering
          const filters = {};
          if (hasFrameworkFilter) {
            filters.frameworkId = this.selectedFramework;
            console.log('🔍 [IncidentPerformanceDashboard] Applying framework filter to cache:', this.selectedFramework);
          }
          if (hasCategoryFilter) {
            filters.category = this.selectedCategory;
            console.log('🔍 [IncidentPerformanceDashboard] Applying category filter to cache:', this.selectedCategory);
          }
          if (hasPriorityFilter) {
            filters.priority = this.selectedPriority;
            console.log('🔍 [IncidentPerformanceDashboard] Applying priority filter to cache:', this.selectedPriority);
          }
          
          // Compute dashboard metrics from cached incidents with filters
          const basicKPIs = incidentDataService.computeBasicKPIsFromCache(filters);
          
          this.dashboardData = {
            status_counts: basicKPIs.statusCounts,
            total_count: basicKPIs.totalCount,
            change_percentage: basicKPIs.change_percentage,
            resolution_rate: basicKPIs.resolution_rate
          };
          
          // Set data source message with timing
          const timeTaken = getTimeTaken();
          this.dataSourceMessage = `✅ Loaded ${basicKPIs.totalCount} incidents from cache (prefetched on Home page) - ${timeTaken}`;
          
          // Compute chart data from cache INSTANTLY with filters (no API calls needed!)
          console.log('⚡ [IncidentPerformanceDashboard] Computing chart data from cache with filters - INSTANT!');
          const statusData = incidentDataService.computeChartDataFromCache('Status', filters);
          const originData = incidentDataService.computeChartDataFromCache('Origin', filters);
          const categoryData = incidentDataService.computeChartDataFromCache('RiskCategory', filters);
          const priorityData = incidentDataService.computeChartDataFromCache('RiskPriority', filters);
          
          this.chartData = {
            status: statusData,
            origin: originData,
            category: categoryData,
            priority: priorityData
          };
          
          // Update charts immediately (no loading spinner!)
          await this.$nextTick();
          await this.safeUpdateAllCharts();
          
          const timeTaken2 = getTimeTaken();
          console.log(`✅ [IncidentPerformanceDashboard] Dashboard and charts loaded from cache - ${timeTaken2}`, {
            totalCount: basicKPIs.totalCount,
            filters: filters,
            chartData: {
              status: statusData.labels.length,
              origin: originData.labels.length,
              category: categoryData.labels.length,
              priority: priorityData.labels.length
            }
          });
          return;
        }
        
        // If complex filters (time range) or no cached data, fetch from API
        console.log(hasComplexFilters ? '🔍 [IncidentPerformanceDashboard] Complex filters (time range) active, fetching from API' : '⚠️ [IncidentPerformanceDashboard] No cached data, fetching from API');

        // Fetch dashboard summary data
        let dashboardResponse
        try {
          const dashboardRequest = {}
          
          // Add framework filter if selected
          if (this.selectedFramework) {
            dashboardRequest.framework_id = this.selectedFramework
            console.log('Applying framework filter to dashboard:', this.selectedFramework)
          }
          
          // Add other filters
          if (this.selectedTimeRange && this.selectedTimeRange !== 'Last 6 Months') {
            dashboardRequest.timeRange = this.selectedTimeRange
          }
          
          if (this.selectedCategory && this.selectedCategory !== 'All Categories') {
            dashboardRequest.category = this.selectedCategory
          }
          
          if (this.selectedPriority && this.selectedPriority !== 'All Priorities') {
            dashboardRequest.priority = this.selectedPriority
          }
          
          console.log('Dashboard request with filters:', dashboardRequest)
          dashboardResponse = await apiService.get('/api/incidents/dashboard/', dashboardRequest)
          console.log('Incident Dashboard API Response:', dashboardResponse)
        } catch (err) {
          console.error('Error fetching dashboard data:', err)
          if (AccessUtils.handleApiError(err)) {
            return
          }
          throw new Error(`Dashboard fetch failed: ${err.message}`)
        }

        // Fetch data for each chart
        const chartPromises = [
          this.fetchChartData('Status', 'doughnut'),
          this.fetchChartData('Origin', 'bar'),
          this.fetchChartData('RiskCategory', 'line'),
          this.fetchChartData('RiskPriority', 'bar')
        ]

        const [statusData, originData, categoryData, priorityData] = await Promise.all(chartPromises)

        if (dashboardResponse && dashboardResponse.success) {
          const summary = dashboardResponse.data?.summary || {}
          console.log('Dashboard summary data:', summary)
          
          this.dashboardData = {
            status_counts: summary.status_counts || {},
            total_count: summary.total_count || 0,
            change_percentage: summary.change_percentage || 0,
            resolution_rate: summary.resolution_rate || 0
          }
          
          // Set data source message for API fetch with timing
          const timeTaken = getTimeTaken();
          this.dataSourceMessage = `📊 Loaded ${this.dashboardData.total_count} incidents from API (cache unavailable or filters applied) - ${timeTaken}`;
          
          // Update chart data
          this.chartData = {
            status: statusData,
            origin: originData,
            category: categoryData,
            priority: priorityData
          }
          
          const timeTaken3 = getTimeTaken();
          console.log(`✅ [IncidentPerformanceDashboard] Dashboard loaded from API - ${timeTaken3}`)
          console.log('Updated chart data:', this.chartData)
          
          // Wait for the next tick to ensure DOM is updated
          await this.$nextTick()
          await this.safeUpdateAllCharts()
        } else {
          const errorMessage = dashboardResponse?.message || 'API request failed'
          const timeTakenError = getTimeTaken();
          console.error(`❌ API Error after ${timeTakenError}:`, errorMessage)
          throw new Error(errorMessage)
        }
      } catch (error) {
        const timeTakenError2 = getTimeTaken();
        console.error(`❌ Error in fetchDashboardData after ${timeTakenError2}:`, error)
        
        if (AccessUtils.handleApiError(error)) {
          return
        }
        
        // Set default values on error with timing message
        this.dashboardData = {
          status_counts: { scheduled: 0, approved: 0, rejected: 0 },
          total_count: 0,
          change_percentage: 0,
          resolution_rate: 0
        }
        
        const defaultChartData = {
          labels: ['No Data'],
          datasets: [{
            label: 'Error Loading Data',
            data: [0],
            backgroundColor: 'rgba(244, 67, 54, 0.6)',
            borderColor: '#F44336',
            borderWidth: 1
          }]
        }
        
        this.chartData = {
          status: defaultChartData,
          origin: defaultChartData,
          category: defaultChartData,
          priority: defaultChartData
        }
        
        // Set error message with timing
        this.dataSourceMessage = `❌ Error loading data - ${timeTakenError2}`;
        
        await this.$nextTick()
        await this.safeUpdateAllCharts()
      }
    },
    async fetchChartData(yAxis, chartType) {
      try {
        // Check which filters are active
        const hasTimeRangeFilter = this.selectedTimeRange && this.selectedTimeRange !== 'Last 6 Months';
        
        // If no time range filter and we have cached incidents, compute from cache
        // (framework, category, priority filters are applied in computeChartDataFromCache)
        if (!hasTimeRangeFilter && incidentDataService.hasValidIncidentsCache()) {
          // Prepare filters for client-side filtering
          const filters = {};
          if (this.selectedFramework) {
            filters.frameworkId = this.selectedFramework;
          }
          if (this.selectedCategory && this.selectedCategory !== 'All Categories') {
            filters.category = this.selectedCategory;
          }
          if (this.selectedPriority && this.selectedPriority !== 'All Priorities') {
            filters.priority = this.selectedPriority;
          }
          
          console.log(`⚡ [IncidentPerformanceDashboard] Computing ${yAxis} chart data from cache with filters - INSTANT!`, filters);
          return incidentDataService.computeChartDataFromCache(yAxis, filters);
        }
        
        // If time range filter is active or no cache, fetch from API
        const requestData = {
          xAxis: 'Time',
          yAxis: yAxis
        }
        
        // Add framework filter if selected
        if (this.selectedFramework) {
          requestData.frameworkId = this.selectedFramework
          console.log(`Applying framework filter for ${yAxis} chart:`, this.selectedFramework)
        }
        
        // Add other filters with proper time range mapping
        if (this.selectedTimeRange && this.selectedTimeRange !== 'Last 6 Months') {
          // Map frontend time range values to backend format
          const timeRangeMap = {
            'Last Week': '7days',
            'Last Month': '30days',
            'Last 3 Months': '90days',
            'Last 6 Months': 'all' // This shouldn't be sent but just in case
          }
          requestData.timeRange = timeRangeMap[this.selectedTimeRange] || this.selectedTimeRange
        }
        
        if (this.selectedCategory && this.selectedCategory !== 'All Categories') {
          requestData.category = this.selectedCategory
        }
        
        if (this.selectedPriority && this.selectedPriority !== 'All Priorities') {
          requestData.priority = this.selectedPriority
        }
        
        console.log(`🔍 [IncidentPerformanceDashboard] Fetching ${yAxis} chart data from API (time range filter active or no cache)...`)
        const payload = (await apiService.post('/api/incidents/dashboard/analytics/', requestData)) || {}
        const chartPayload = payload.chartData || payload.chart_data
        if (payload.success && chartPayload && (chartPayload.labels?.length || chartPayload.datasets?.length)) {
          return chartPayload
        }
        if (chartPayload && chartPayload.datasets) {
          return chartPayload
        }
        console.warn(`No chart payload for ${yAxis}`, payload)
        return this.getDefaultChartData(chartType)
      } catch (error) {
        console.error(`Error fetching ${yAxis} chart data:`, error)
        // Fallback to cache if API fails and we have cache
        if (incidentDataService.hasValidIncidentsCache()) {
          console.log(`⚠️ [IncidentPerformanceDashboard] API failed for ${yAxis}, falling back to cache...`);
          const filters = {};
          if (this.selectedFramework) filters.frameworkId = this.selectedFramework;
          if (this.selectedCategory && this.selectedCategory !== 'All Categories') filters.category = this.selectedCategory;
          if (this.selectedPriority && this.selectedPriority !== 'All Priorities') filters.priority = this.selectedPriority;
          return incidentDataService.computeChartDataFromCache(yAxis, filters);
        }
        return this.getDefaultChartData(chartType)
      }
    },
    getDefaultChartData(chartType) {
      const defaultData = {
        labels: ['No Data Available'],
        datasets: [{
          label: 'No Data',
          data: [1],
          backgroundColor: 'rgba(158, 158, 158, 0.6)',
          borderColor: '#9E9E9E',
          borderWidth: 1
        }]
      }
      
      if (chartType === 'line') {
        defaultData.datasets[0].tension = 0.1
        defaultData.datasets[0].fill = false
      }
      
      return defaultData
    },
    updateAllCharts() {
      this.updateChart('statusChart', 'doughnut', this.chartData.status, 'statusChart')
      this.updateChart('originChart', 'bar', this.chartData.origin, 'originChart')
      this.updateChart('categoryChart', 'line', this.chartData.category, 'categoryChart')
      this.updateChart('priorityChart', 'bar', this.chartData.priority, 'priorityChart')
    },
    async safeUpdateAllCharts(maxAttempts = 8, delayMs = 120) {
      if (!this.isComponentAlive) return
      const chartIds = ['statusChart', 'originChart', 'categoryChart', 'priorityChart']

      for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
        if (!this.isComponentAlive) return
        await this.$nextTick()
        const root = this.$el
        const allReady = chartIds.every((id) => (root && root.querySelector(`#${id}`)) || document.getElementById(id))
        if (allReady) {
          this.updateAllCharts()
          return
        }
        await new Promise((resolve) => setTimeout(resolve, delayMs))
      }

      // Final attempt even if some canvases are missing; updateChart has per-chart guards.
      if (this.isComponentAlive) this.updateAllCharts()
    },
    updateChart(chartId, chartType, chartData, chartIdForColors = '') {
      try {
        // Destroy existing chart if it exists
        if (this.charts[chartId]) {
          this.charts[chartId].destroy()
        }

        // Get the canvas element
        const root = this.$el
        const canvas = (root && root.querySelector(`#${chartId}`)) || document.getElementById(chartId)
        if (!canvas) {
          console.warn(`Chart canvas not found yet: ${chartId}`)
          return
        }

        // Create the chart configuration
        const config = this.createChartConfig(chartType, chartData, chartIdForColors)

        // Create new chart instance
        this.charts[chartId] = new ChartJS(canvas, config)
      } catch (error) {
        console.error(`Error in updateChart for ${chartId}:`, error)
        this.charts[chartId] = null
      }
    },
    createChartConfig(chartType, chartData, chartId = '') {
      if (!chartData) {
        return {
          type: chartType,
          data: {
            labels: ['No Data'],
            datasets: [{
              label: 'No Data',
              data: [0],
              backgroundColor: 'rgba(200, 200, 200, 0.5)',
              borderColor: '#ccc',
              borderWidth: 1
            }]
          },
          options: this.getChartOptions(chartType)
        }
      }

      // Check if we have multiple datasets
      const hasMultipleDatasets = Array.isArray(chartData.datasets) && chartData.datasets.length > 1;
      
      let datasets;
      
      if (hasMultipleDatasets) {
        // Use the datasets as provided by the backend
        datasets = chartData.datasets.map((dataset, index) => {
          const colors = this.getColorForIndex(index);
          return {
            ...dataset,
            backgroundColor: colors.backgroundColor,
            borderColor: colors.borderColor,
            borderWidth: 1,
            tension: chartType === 'line' ? 0.1 : undefined,
            fill: chartType === 'line' ? false : undefined
          };
        });
      } else {
        // Single dataset with custom colors
        const dataset = {
          ...chartData.datasets[0],
          backgroundColor: this.getBackgroundColors(chartType, chartData.labels, chartId),
          borderColor: this.getBorderColors(chartType, chartData.labels, chartId),
          borderWidth: 1
        };

        if (chartType === 'line') {
          dataset.tension = 0.1;
          dataset.fill = false;
        }
        
        datasets = [dataset];
      }

      return {
        type: chartType,
        data: {
          labels: chartData.labels,
          datasets: datasets
        },
        options: this.getChartOptions(chartType)
      }
    },
    
    // Helper method to get color for multiple datasets
    getColorForIndex(index) {
      const colors = [
        { backgroundColor: 'rgba(255, 99, 132, 0.6)', borderColor: 'rgb(255, 99, 132)' },
        { backgroundColor: 'rgba(54, 162, 235, 0.6)', borderColor: 'rgb(54, 162, 235)' },
        { backgroundColor: 'rgba(255, 206, 86, 0.6)', borderColor: 'rgb(255, 206, 86)' },
        { backgroundColor: 'rgba(75, 192, 192, 0.6)', borderColor: 'rgb(75, 192, 192)' },
        { backgroundColor: 'rgba(153, 102, 255, 0.6)', borderColor: 'rgb(153, 102, 255)' },
        { backgroundColor: 'rgba(255, 159, 64, 0.6)', borderColor: 'rgb(255, 159, 64)' },
        { backgroundColor: 'rgba(199, 199, 199, 0.6)', borderColor: 'rgb(199, 199, 199)' }
      ];
      
      // Use modulo to cycle through colors if we have more datasets than colors
      const originalColor = colors[index % colors.length];
      
      // Apply colorblindness conversion
      return {
        backgroundColor: this.convertColorForColorblind(originalColor.backgroundColor, 0.6),
        borderColor: this.convertColorForColorblind(originalColor.borderColor, 1.0)
      };
    },
    getChartOptions(chartType) {
      const options = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 500,
          easing: 'easeInOutQuad'
        },
        plugins: {
          legend: {
            display: true,
            position: 'bottom'
          },
          tooltip: {
            enabled: true,
            callbacks: {
              label: (context) => {
                if (['pie', 'doughnut'].includes(chartType)) {
                  const label = context.label || ''
                  const value = context.raw || 0
                  const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0)
                  const percentage = ((value / total) * 100).toFixed(1)
                  return `${label}: ${value} (${percentage}%)`
                }
                return `Count: ${context.raw}`
              }
            }
          }
        }
      }

      if (['bar', 'line'].includes(chartType)) {
        options.scales = {
          x: {
            // Reduce bar thickness for bar charts
            ...(chartType === 'bar' && {
              categoryPercentage: 0.6,
              barPercentage: 0.6
            })
          },
          y: {
            beginAtZero: true,
            ticks: {
              stepSize: 1,
              precision: 0
            }
          }
        }
        // Limit maximum bar thickness for bar charts
         if (chartType === 'bar') {
           options.maxBarThickness = 40
         }
       }

      // Special options for doughnut charts
      if (chartType === 'doughnut') {
        options.cutout = '70%'
      }

      return options
    },

    getBackgroundColors(chartType, labels, chartId = '') {
      const colorMaps = {
        Status: {
          'Scheduled': 'rgba(255, 152, 0, 0.6)',
          'Approved': 'rgba(76, 175, 80, 0.6)',
          'Rejected': 'rgba(244, 67, 54, 0.6)',
          'Resolved': 'rgba(33, 150, 243, 0.6)'
        },
        Origin: {
          'Manual': 'rgba(33, 150, 243, 0.6)',
          'SIEM': 'rgba(156, 39, 176, 0.6)',
          'Audit Finding': 'rgba(255, 193, 7, 0.6)',
          'Compliance Gap': 'rgba(255, 87, 34, 0.6)',
          'Other': 'rgba(121, 85, 72, 0.6)'
        },
        RiskCategory: {
          'Security': 'rgba(244, 67, 54, 0.6)',
          'Compliance': 'rgba(156, 39, 176, 0.6)',
          'Operational': 'rgba(255, 152, 0, 0.6)',
          'Financial': 'rgba(33, 150, 243, 0.6)',
          'Strategic': 'rgba(76, 175, 80, 0.6)',
          'Reputational': 'rgba(121, 85, 72, 0.6)'
        },
        RiskPriority: {
          'High': 'rgba(244, 67, 54, 0.6)',
          'Medium': 'rgba(255, 152, 0, 0.6)',
          'Low': 'rgba(76, 175, 80, 0.6)'
        }
      }

      // For doughnut charts, use a predefined color palette
      if (chartType === 'doughnut') {
        const doughnutColors = [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)',
          'rgba(153, 102, 255, 0.8)',
          'rgba(255, 159, 64, 0.8)'
        ]
        // Apply colorblindness conversion
        return doughnutColors.map(color => this.convertColorForColorblind(color, 0.8))
      }

      // For line charts, use a single color
      if (chartType === 'line') {
        return this.convertColorForColorblind('rgba(54, 162, 235, 0.6)', 0.6)
      }

      // For bar charts, map colors based on labels
      return labels?.map(label => {
        // Determine the category based on chartId
        let category = 'Origin'
        if (chartId.includes('priority')) {
          category = 'RiskPriority'
        } else if (chartId.includes('status')) {
          category = 'Status'
        } else if (chartId.includes('category')) {
          category = 'RiskCategory'
        } else if (chartId.includes('origin')) {
          category = 'Origin'
        }
        
        const originalColor = colorMaps[category]?.[label] || 'rgba(158, 158, 158, 0.6)'
        // Apply colorblindness conversion
        return this.convertColorForColorblind(originalColor, 0.6)
      }) || []
    },
    getBorderColors(chartType, labels, chartId = '') {
      const colorMaps = {
        Status: {
          'Scheduled': '#FF9800',
          'Approved': '#4CAF50',
          'Rejected': '#F44336',
          'Resolved': '#2196F3'
        },
        Origin: {
          'Manual': '#2196F3',
          'SIEM': '#9C27B0',
          'Audit Finding': '#FFC107',
          'Compliance Gap': '#FF5722',
          'Other': '#795548'
        },
        RiskCategory: {
          'Security': '#F44336',
          'Compliance': '#9C27B0',
          'Operational': '#FF9800',
          'Financial': '#2196F3',
          'Strategic': '#4CAF50',
          'Reputational': '#795548'
        },
        RiskPriority: {
          'High': '#F44336',
          'Medium': '#FF9800',
          'Low': '#4CAF50'
        }
      }

      // For doughnut charts, use a predefined color palette
      if (chartType === 'doughnut') {
        const doughnutColors = [
          'rgb(255, 99, 132)',
          'rgb(54, 162, 235)',
          'rgb(255, 206, 86)',
          'rgb(75, 192, 192)',
          'rgb(153, 102, 255)',
          'rgb(255, 159, 64)'
        ]
        // Apply colorblindness conversion (border colors are rgb format, convert to hex first)
        return doughnutColors.map(color => {
          const hex = this.rgbaToHex(color)
          const converted = this.convertColorForColorblind(hex, 1.0)
          // Convert back to rgb for border colors
          if (converted.startsWith('#')) {
            const r = parseInt(converted.slice(1, 3), 16)
            const g = parseInt(converted.slice(3, 5), 16)
            const b = parseInt(converted.slice(5, 7), 16)
            return `rgb(${r}, ${g}, ${b})`
          }
          return converted || color
        })
      }

      // For line charts, use a single color
      if (chartType === 'line') {
        const converted = this.convertColorForColorblind('rgb(54, 162, 235)', 1.0)
        // Convert back to rgb if needed
        if (converted.startsWith('#')) {
          const r = parseInt(converted.slice(1, 3), 16)
          const g = parseInt(converted.slice(3, 5), 16)
          const b = parseInt(converted.slice(5, 7), 16)
          return `rgb(${r}, ${g}, ${b})`
        }
        return converted
      }

      // For bar charts, map colors based on labels
      return labels?.map(label => {
        // Determine the category based on chartId
        let category = 'Origin'
        if (chartId.includes('priority')) {
          category = 'RiskPriority'
        } else if (chartId.includes('status')) {
          category = 'Status'
        } else if (chartId.includes('category')) {
          category = 'RiskCategory'
        } else if (chartId.includes('origin')) {
          category = 'Origin'
        }
        
        const originalColor = colorMaps[category]?.[label] || '#9E9E9E'
        // Apply colorblindness conversion
        const converted = this.convertColorForColorblind(originalColor, 1.0)
        // Convert back to rgb if needed
        if (converted.startsWith('#')) {
          const r = parseInt(converted.slice(1, 3), 16)
          const g = parseInt(converted.slice(3, 5), 16)
          const b = parseInt(converted.slice(5, 7), 16)
          return `rgb(${r}, ${g}, ${b})`
        }
        return converted || originalColor
      }) || []
    },
    onFrameworkChange() {
      console.log('🔄 Framework selection changed to:', this.selectedFramework || 'All Frameworks')
      
      if (this.selectedFramework) {
        const selectedFrameworkName = this.frameworks.find(f => f.id == this.selectedFramework)?.name
        console.log('Selected framework name:', selectedFrameworkName)
      } else {
        console.log('Loading data for all frameworks')
      }
      
      this.fetchDashboardData()
    },

    debugFramework() {
      console.log('=== FRAMEWORK DEBUG ===')
      console.log('Current selectedFramework:', this.selectedFramework)
      console.log('Available frameworks:', this.frameworks)
      console.log('localStorage selectedFrameworkId:', localStorage.getItem('selectedFrameworkId'))
      console.log('localStorage frameworkId:', localStorage.getItem('frameworkId'))
      console.log('sessionStorage selectedFrameworkId:', sessionStorage.getItem('selectedFrameworkId'))
      console.log('sessionStorage frameworkId:', sessionStorage.getItem('frameworkId'))
      
      // Test API call (same transport as rest of app: cookies + CSRF on mutating methods)
      apiService.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        .then((data) => {
          console.log('API Response:', data)
        })
        .catch(error => {
          console.error('API Error:', error)
        })
      
      // Test setting a framework manually
      if (this.frameworks.length > 0) {
        const firstFramework = this.frameworks[0]
        console.log('Testing with first framework:', firstFramework)
        this.selectedFramework = firstFramework.id
        this.fetchDashboardData()
      }
      
      alert('Framework debug info logged to console. Check browser console for details.')
    },

    refreshData() {
      this.fetchFrameworks()
      this.fetchDashboardData()
      this.fetchRecentIncidents()
    },
    
    clearFilters() {
      this.selectedFramework = ''
      this.selectedTimeRange = 'Last 6 Months'
      this.selectedCategory = 'All Categories'
      this.selectedPriority = 'All Priorities'
      this.fetchDashboardData()
    },
    
    // Download/export dashboard in selected format
    async downloadDashboardPDF() {
      this.isDownloading = true
      try {
        await this.$nextTick() // Ensure all components are rendered
        
        const dashboardElement = document.querySelector('.dashboard-container')
        if (!dashboardElement) {
          throw new Error('Dashboard element not found')
        }

        // Wait a bit to ensure all charts are fully rendered
        await new Promise(resolve => setTimeout(resolve, 500))

        // Capture the entire dashboard as it appears on the webpage
        const canvas = await html2canvas(dashboardElement, {
          scale: 2.5, // Higher quality for better chart visibility
          useCORS: true,
          allowTaint: true,
          logging: false,
          backgroundColor: '#ffffff', // White background for better visibility
          windowWidth: dashboardElement.scrollWidth,
          windowHeight: dashboardElement.scrollHeight,
          scrollY: -window.scrollY,
          scrollX: -window.scrollX,
          // Ensure canvas elements (charts) are captured
          onclone: (clonedDoc) => {
            const clonedDashboard = clonedDoc.querySelector('.dashboard-container')
            if (clonedDashboard) {
              clonedDashboard.style.transform = 'none'
              clonedDashboard.style.position = 'relative'
              clonedDashboard.style.left = '0'
              clonedDashboard.style.top = '0'
              clonedDashboard.style.marginLeft = '0'
              clonedDashboard.style.maxWidth = '100%'
              clonedDashboard.style.background = '#ffffff'
            }
            
            // Force all canvas elements to be visible with better rendering
            const canvases = clonedDoc.querySelectorAll('canvas')
            canvases.forEach(canvas => {
              canvas.style.display = 'block'
              canvas.style.visibility = 'visible'
              canvas.style.opacity = '1'
              canvas.style.imageRendering = 'crisp-edges'
              // Ensure canvas has proper dimensions
              if (canvas.width === 0 || canvas.height === 0) {
                canvas.width = canvas.offsetWidth * 2.5
                canvas.height = canvas.offsetHeight * 2.5
              }
            })

            // Ensure chart containers are visible with proper dimensions
            const chartContainers = clonedDoc.querySelectorAll('.global-dashboard-chart-container')
            chartContainers.forEach(container => {
              container.style.display = 'block'
              container.style.visibility = 'visible'
              container.style.opacity = '1'
              container.style.minHeight = '300px'
              container.style.background = '#ffffff'
            })

            // Ensure all chart cards are visible
            const chartCards = clonedDoc.querySelectorAll('.global-dashboard-chart-card')
            chartCards.forEach(card => {
              card.style.display = 'flex'
              card.style.visibility = 'visible'
              card.style.opacity = '1'
              card.style.background = '#ffffff'
            })
          }
        })

        const imgData = canvas.toDataURL('image/png', 1.0)

        // Generate filename with timestamp
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)

        if (this.exportFormat === 'png') {
          // Download as PNG image
          const link = document.createElement('a')
          link.href = imgData
          link.download = `Incident-Dashboard-${timestamp}.png`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          console.log('PNG downloaded successfully')
        } else {
          // Calculate PDF dimensions based on captured content
          const imgWidth = canvas.width
          const imgHeight = canvas.height
          
          // Create PDF with custom dimensions to fit the entire dashboard
          // Use landscape orientation and custom size to match dashboard width
          const pdfWidth = 297 // A4 width in mm (landscape)
          const pdfHeight = (imgHeight * pdfWidth) / imgWidth // Calculate proportional height
          
          const pdf = new jsPDF({
            orientation: pdfHeight > pdfWidth ? 'portrait' : 'landscape',
            unit: 'mm',
            format: [pdfWidth, pdfHeight]
          })

          // Add the entire dashboard as one image
          pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight, '', 'FAST')

          const filename = `Incident-Dashboard-${timestamp}.pdf`
          pdf.save(filename)
          console.log('PDF downloaded successfully')
        }
      } catch (error) {
        console.error('Error generating export:', error)
        alert('Failed to export dashboard. Please try again.')
      } finally {
        this.isDownloading = false
      }
    },

    exportDashboard() {
      if (!this.exportFormat) {
        alert('Please select an export format.');
        return;
      }
      this.downloadDashboardPDF();
    },

    selectExportFormatOption(opt) {
      this.exportFormat = opt.value
      this.isExportDropdownOpen = false
    },
    
    // Navigation function to go back to Incident Management
    goBackToIncident() {
      this.$router.push({ name: 'Incident' })
    },
    
    truncateDescription(text, maxLength) {
      if (!text) return '';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      
      // Check if it's today
      const today = new Date();
      if (date.toDateString() === today.toDateString()) {
        return 'Today, ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      }
      
      // Check if it's yesterday
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      if (date.toDateString() === yesterday.toDateString()) {
        return 'Yesterday, ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      }
      
      // Otherwise return relative time
      const diffTime = Math.abs(today - date);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays < 7) {
        return diffDays + ' days ago';
      } else {
        return date.toLocaleDateString();
      }
    },
    // Get icon class (Font Awesome icon) based on incident priority/status
    getIncidentIcon(incident) {
      const priority = (incident.RiskPriority || '').toLowerCase();
      const status = (incident.Status || '').toLowerCase();
      
      // Priority-based icons
      if (priority.includes('high')) {
        return 'fas fa-exclamation-triangle';
      } else if (priority.includes('low')) {
        return 'fas fa-info-circle';
      }
      
      // Status-based icons
      if (status.includes('rejected')) {
        return 'fas fa-ban';
      } else if (status.includes('approved')) {
        return 'fas fa-check-circle';
      } else if (status.includes('scheduled')) {
        return 'fas fa-clock';
      } else if (status.includes('resolved')) {
        return 'fas fa-check-double';
      }
      
      // Default icon for incidents
      return 'fas fa-exclamation-circle';
    },
    // Map incident to global icon color class from main.css
    // All icons use the same color for consistency
    // eslint-disable-next-line no-unused-vars
    getIncidentIconClass(incident) {
      // Use the same color class for all incident icons to maintain visual consistency
      return 'icon-primary';
    }
  }
}
</script>

<style>
@import './IncidentPerformanceDashboard.css';
@import '@/assets/css/dropdown.css';
@import '@/assets/css/main.css';
@import '@/assets/css/DashboardCards.css';
</style>

<style scoped>
.data-source-message {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #2563eb;
  font-weight: 500;
}
</style>