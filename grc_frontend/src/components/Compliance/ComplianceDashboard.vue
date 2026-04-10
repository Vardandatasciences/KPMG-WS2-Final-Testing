<template>
  <div class="compliance-dashboard-container">
    <div class="compliance-dashboard-header">
      <div class="compliance-dashboard-header-left">
        <h1>Compliance Dashboard</h1>
      </div>
      <div class="header-actions">
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
              class="export-btn"
              @click="exportDashboardAsPDF()"
              :disabled="isExporting || !exportFormat"
              :class="{ 'exporting': isExporting, 'success': exportSuccess }"
              title="Export Dashboard as PDF"
            >
              <i v-if="!isExporting" class="fas fa-download"></i>
              <i v-else class="fas fa-spinner fa-spin"></i>
              <span class="export-btn-text">
                {{ isExporting ? 'Exporting...' : 'Export' }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Framework Filter -->
    <div class="compliance-dashboard-filter-section">
      <!-- Single Row: All Four Filters -->
      <div class="compliance-dashboard-filter-row">
        <div class="compliance-dashboard-filter-group">
          <label class="dropdown-external-label">Framework Selection</label>
          <CustomDropdown
            :options="frameworkOptions"
            :disabled="loadingFrameworks || loadingDashboard"
            v-model="selectedFramework"
            :showClearButton="true"
            @change="onFrameworkChange"
            :config="{ label: 'Framework Selection' }"
            :showLabel="false"
          />
        </div>
        <div class="compliance-dashboard-filter-group">
          <label class="dropdown-external-label">Time Range</label>
          <CustomDropdown
            :options="timeRangeOptions"
            v-model="selectedTimeRange"
            :showClearButton="true"
            @change="onTimeRangeChange"
            :config="{ label: 'Time Range' }"
            :showLabel="false"
          />
        </div>
        <div class="compliance-dashboard-filter-group">
          <label class="dropdown-external-label">Category</label>
          <CustomDropdown
            :options="categoryOptions"
            v-model="selectedCategory"
            :showClearButton="true"
            @change="onCategoryChange"
            :config="{ label: 'Category' }"
            :showLabel="false"
          />
        </div>
        <div class="compliance-dashboard-filter-group">
          <label class="dropdown-external-label">Priority</label>
          <CustomDropdown
            :options="priorityOptions"
            v-model="selectedPriority"
            :showClearButton="true"
            @change="onPriorityChange"
            :config="{ label: 'Priority' }"
            :showLabel="false"
          />
        </div>
      </div>
    </div>

    <!-- Filter Summary -->
    <div v-if="hasActiveFilters" class="filter-summary" style="background: transparent; color: #475569; padding: 16px 20px; border-radius: 12px; margin-bottom: 24px;">
      <div style="display: flex; align-items: center; gap: 12px;">
        <!-- <span style="font-weight: 600; font-size: 14px;">Active Filters:</span> -->
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <span v-if="selectedTimeRange !== 'Last 6 Months'" class="filter-tag" style="background: rgba(76, 175, 80, 0.1); color: #4CAF50; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 500;">
            Time: {{ selectedTimeRange }}
          </span>
          <span v-if="selectedCategory !== 'All Categories'" class="filter-tag" style="background: rgba(76, 175, 80, 0.1); color: #4CAF50; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 500;">
            Category: {{ selectedCategory }}
          </span>
          <span v-if="selectedPriority !== 'All Priorities'" class="filter-tag" style="background: rgba(76, 175, 80, 0.1); color: #4CAF50; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 500;">
            Priority: {{ selectedPriority }}
          </span>
        </div>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div class="dashboard-content">
      <!-- KPI Summary Cards using global styles from main.css -->
      <div class="kpi-grid">
        <!-- Approval Rate -->
        <div class="kpi-card">
          <div class="kpi-card-icon kpi-icon-approved">
            <i class="fas fa-check-circle"></i>
          </div>
          <div class="kpi-card-body">
            <p class="kpi-card-title">Approval Rate</p>
            <div class="kpi-card-value">
              {{ dashboardData.approval_rate }}%
            </div>
            <p class="kpi-card-subtitle">
              Based on {{ dashboardData.total_count }} compliances
            </p>
          </div>
        </div>

        <!-- Active Compliances -->
        <div class="kpi-card">
          <div class="kpi-card-icon kpi-icon-open">
            <i class="fas fa-file-alt"></i>
          </div>
          <div class="kpi-card-body">
            <p class="kpi-card-title">Active Compliances</p>
            <div class="kpi-card-value">
              {{ dashboardData.status_counts.active_compliance || 0 }}
            </div>
            <p class="kpi-card-subtitle">
              Active and approved items
            </p>
          </div>
        </div>

        <!-- Total Findings -->
        <div class="kpi-card">
          <div class="kpi-card-icon kpi-icon-total">
            <i class="fas fa-list"></i>
          </div>
          <div class="kpi-card-body">
            <p class="kpi-card-title">Total Findings</p>
            <div class="kpi-card-value">
              {{ dashboardData.total_findings }}
            </div>
            <p class="kpi-card-subtitle">
              Across all compliances
            </p>
          </div>
        </div>

        <!-- Under Review -->
        <div class="kpi-card">
          <div class="kpi-card-icon kpi-icon-rejected">
            <i class="fas fa-clock"></i>
          </div>
          <div class="kpi-card-body">
            <p class="kpi-card-title">Under Review</p>
            <div class="kpi-card-value">
              {{ dashboardData.status_counts.under_review }}
            </div>
            <p class="kpi-card-subtitle">
              Pending reviewer action
            </p>
          </div>
        </div>
      </div>

    <!-- Charts Grid - 2x2 Layout with 5th chart in new row -->
    <div class="global-dashboard-charts-grid">
      <!-- Chart 1: Compliance vs Criticality (Bar Chart) -->
      <div class="global-dashboard-chart-card">
        <div class="global-dashboard-chart-header">
          <h3 class="global-dashboard-chart-title">Compliance vs Criticality</h3>
          <div class="global-dashboard-chart-icon" style="color: #3B82F6;">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="global-dashboard-chart-container">
          <canvas id="criticalityChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 2: Compliance vs Status (Donut Chart) -->
      <div class="global-dashboard-chart-card">
        <div class="global-dashboard-chart-header">
          <h3 class="global-dashboard-chart-title">Compliance vs Status</h3>
          <div class="global-dashboard-chart-icon" style="color: #10B981;">
            <i class="fas fa-chart-pie"></i>
          </div>
        </div>
        <div class="global-dashboard-chart-container">
          <canvas id="statusChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 3: Compliance vs Active/Inactive (Bar Chart) -->
      <div class="global-dashboard-chart-card">
        <div class="global-dashboard-chart-header">
          <h3 class="global-dashboard-chart-title">Compliance vs Active/Inactive</h3>
          <div class="global-dashboard-chart-icon" style="color: #F59E0B;">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="global-dashboard-chart-container">
          <canvas id="activeInactiveChart"></canvas>
        </div>
      </div>
      
      <!-- Chart 4: Compliance vs Manual/Automatic (Donut Chart) -->
      <div class="global-dashboard-chart-card">
        <div class="global-dashboard-chart-header">
          <h3 class="global-dashboard-chart-title">Compliance vs Manual/Automatic</h3>
          <div class="global-dashboard-chart-icon" style="color: #8B5CF6;">
            <i class="fas fa-chart-pie"></i>
          </div>
        </div>
        <div class="global-dashboard-chart-container">
          <canvas id="manualAutomaticChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Chart 5: Compliance vs Maturity Level (Bar Chart) - Full Width -->
    <div class="global-dashboard-charts-grid" style="grid-template-columns: 1fr;">
      <div class="global-dashboard-chart-card">
        <div class="global-dashboard-chart-header">
          <h3 class="global-dashboard-chart-title">Compliance vs Maturity Level</h3>
          <div class="global-dashboard-chart-icon" style="color: #EF4444;">
            <i class="fas fa-chart-bar"></i>
          </div>
        </div>
        <div class="global-dashboard-chart-container">
          <canvas id="maturityLevelChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Recent Activity Section -->
    <div class="recent-section">
      <div class="recent-activity">
        <div class="activity-header">
          <h2>Recent Activity</h2>
          <button class="more-options" @click="refreshRecentActivities">
            <i class="fas fa-sync" :class="{ 'fa-spin': loadingActivities }"></i>
          </button>
        </div>
        <div class="activity-list">
          <div v-if="loadingActivities && recentActivities.length === 0" class="activity-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <span>Loading recent activities...</span>
          </div>
          <div v-else-if="!loadingActivities && recentActivities.length === 0" class="activity-empty">
            <i class="fas fa-inbox"></i>
            <span>No recent activities found</span>
          </div>
          <template v-else>
            <div v-for="(activity, index) in recentActivities" :key="index" class="activity-item">
              <div class="icon-container" :class="getActivityIconClass(activity.type)">
                <i :class="activity.icon" class="icon-md"></i>
              </div>
              <div class="activity-details">
                <h4>{{ activity.title }}</h4>
                <p>{{ activity.description }}</p>
                <span class="activity-time">{{ activity.time }}</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
    </div> <!-- Close dashboard-content div -->
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
import { mapState, mapActions } from 'vuex'
import '@fortawesome/fontawesome-free/css/all.min.css'
import { complianceService } from '@/services/api'
import complianceDataService from '@/services/complianceService' // NEW: Use cached compliance data
import apiService from '@/services/apiService.js'
import { API_ENDPOINTS } from '../../config/api.js'
import html2canvas from 'html2canvas'
import { convertColorForColorblind as convertColorFromUtil } from '@/utils/colorblindness'
import jsPDF from 'jspdf'
import CustomDropdown from '@/components/CustomDropdown.vue'
import '@/assets/css/DashboardCards.css'

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

const axios = {
  get: async (url, config = {}) => ({ data: await apiService.get(url, config.params || {}, { ...config, params: undefined }) }),
  post: async (url, data, config = {}) => ({ data: await apiService.post(url, data, config) }),
  put: async (url, data, config = {}) => ({ data: await apiService.put(url, data, config) }),
  patch: async (url, data, config = {}) => ({ data: await apiService.patch(url, data, config) }),
  delete: async (url, config = {}) => ({ data: await apiService.delete(url, config) })
}

export default {
  name: 'ComplianceDashboard',
  components: {
    CustomDropdown
  },
  data() {
    return {
      selectedFramework: '',
      exportFormat: '',
      exportFormatOptions: [
        { value: '', label: 'Select format' },
        // Compliance dashboard currently supports only PDF export
        { value: 'pdf', label: 'PDF (.pdf)' }
      ],
      isExportDropdownOpen: false,
      selectedTimeRange: 'Last 6 Months',
      selectedCategory: 'All Categories',
      selectedPriority: 'All Priorities',
      frameworks: [],
      loadingFrameworks: false,
      
      // Framework session filtering properties
      sessionFrameworkId: null,
      api: {
        complianceService
      },
      dashboardData: {
        status_counts: {
          approved: 0,
          active: 0,
          under_review: 0
        },
        total_count: 0,
        total_findings: 0,
        approval_rate: 0
      },
      charts: {
        criticalityChart: null,
        statusChart: null,
        activeInactiveChart: null,
        manualAutomaticChart: null,
        maturityLevelChart: null
      },
      chartData: {
        criticality: null,
        status: null,
        activeInactive: null,
        manualAutomatic: null,
        maturityLevel: null
      },
      recentActivities: [],
      loadingActivities: false,
      activityRefreshInterval: null,
      loadingDashboard: false, // Start without loading state
      isExporting: false,
      exportSuccess: false,
      colorblindMode: null, // Colorblindness mode tracking
      colorblindObserver: null
    }
  },
  computed: {
    // Vuex store computed properties
    ...mapState('framework', {
      storeFrameworkId: state => state.selectedFrameworkId,
      storeFrameworkName: state => state.selectedFrameworkName
    }),
    
    // Framework filtering computed properties
    filteredFrameworks() {
      if (this.sessionFrameworkId) {
        // If there's a session framework ID, show only that framework
        return this.frameworks.filter(fw => fw.id.toString() === this.sessionFrameworkId.toString())
      }
      // If no session framework ID, show all frameworks
      return this.frameworks
    },
    
    hasActiveFilters() {
      return this.selectedFramework || 
             this.selectedTimeRange !== 'Last 6 Months' || 
             this.selectedCategory !== 'All Categories' || 
             this.selectedPriority !== 'All Priorities'
    },
    
    // Dropdown options for CustomDropdown
    frameworkOptions() {
      return [
        { value: '', label: 'All Frameworks' },
        ...this.filteredFrameworks.map(fw => ({
          value: fw.id.toString(),
          label: fw.name
        }))
      ]
    },
    
    timeRangeOptions() {
      return [
        { value: 'Last 6 Months', label: 'Last 6 Months' },
        { value: 'Last 3 Months', label: 'Last 3 Months' },
        { value: 'Last Month', label: 'Last Month' },
        { value: 'Last Week', label: 'Last Week' }
      ]
    },
    
    categoryOptions() {
      return [
        { value: 'All Categories', label: 'All Categories' },
        { value: 'Security', label: 'Security' },
        { value: 'Compliance', label: 'Compliance' },
        { value: 'Operational', label: 'Operational' }
      ]
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
    }
  },
  async mounted() {
    console.log('🚀 ComplianceDashboard mounted - starting instant loading...')
    
    // Check if FontAwesome is loaded (non-blocking)
    this.checkFontAwesome()
    
    // Initialize colorblindness mode tracking
    this.initColorblindnessTracking()
    
    // Load framework from Vuex store
    if (this.storeFrameworkId && this.storeFrameworkId !== 'all') {
      this.selectedFramework = this.storeFrameworkId
      console.log('🔄 ComplianceDashboard: Loaded framework from Vuex store:', this.storeFrameworkId)
    }
    
    // Start all data loading immediately without waiting
    console.log('📊 Starting instant data loading...')
    
    // Load all data in parallel including recent activities
    Promise.all([
      this.fetchFrameworks(),
      this.fetchDashboardData(),
      this.fetchRecentActivities() // Load activities with charts
    ]).then(() => {
      // Check for selected framework from session after loading
      this.checkSelectedFrameworkFromSession()
    })
    
    // Auto-refresh activities every 5 minutes
    this.activityRefreshInterval = setInterval(() => {
      this.fetchRecentActivities()
    }, 300000) // 5 minutes
    
    console.log('✅ ComplianceDashboard initialization started instantly!')
  },
  beforeUnmount() {
    this.destroyAllCharts()
    if (this.activityRefreshInterval) {
      clearInterval(this.activityRefreshInterval)
    }
    // Clean up colorblindness observer
    if (this.colorblindObserver) {
      this.colorblindObserver.disconnect()
      this.colorblindObserver = null
    }
  },
  beforeRouteLeave(to, from, next) {
    this.destroyAllCharts()
    if (this.activityRefreshInterval) {
      clearInterval(this.activityRefreshInterval)
    }
    next()
  },
  watch: {
    // Watch for Vuex store framework changes
    storeFrameworkId(newFrameworkId, oldFrameworkId) {
      // Only update if value actually changed
      if (newFrameworkId === oldFrameworkId) return
      
      console.log('🔄 ComplianceDashboard: Vuex store framework changed to:', newFrameworkId)
      console.log('🔄 ComplianceDashboard: Old framework was:', oldFrameworkId)
      
      // Update local selectedFramework to match store
      if (newFrameworkId === 'all' || !newFrameworkId) {
        this.selectedFramework = ''
      } else {
        this.selectedFramework = newFrameworkId
      }
      
      // Reload dashboard data with new framework
      console.log('🔄 ComplianceDashboard: Fetching data for framework:', this.selectedFramework)
      this.fetchDashboardData()
    }
  },
  methods: {
    ...mapActions('framework', ['setFramework']),
    
    // Colorblindness support methods
    initColorblindnessTracking() {
      // Get current colorblindness mode
      this.colorblindMode = this.getColorblindMode()
      console.log('🎨 Initial colorblindness mode:', this.colorblindMode)
      
      // Watch for colorblindness mode changes
      this.colorblindObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'attributes' && mutation.attributeName === 'data-colorblind') {
            const newMode = this.getColorblindMode()
            console.log('🎨 MutationObserver detected change:', {
              oldMode: this.colorblindMode,
              newMode: newMode,
              attributeValue: document.documentElement.getAttribute('data-colorblind')
            })
            if (newMode !== this.colorblindMode) {
              console.log('🎨 Colorblindness mode changed:', newMode, 'Previous:', this.colorblindMode)
              this.colorblindMode = newMode
              // Re-render all charts with new colors
              this.$nextTick(() => {
                console.log('🎨 Re-rendering charts with new colorblindness mode:', this.colorblindMode)
                this.updateAllCharts()
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
      console.log('🎨 Colorblindness observer initialized')
    },
    
    getColorblindMode() {
      const html = document.documentElement
      return html.getAttribute('data-colorblind') || null
    },
    
    // Convert rgba/rgb to hex (helper for color conversion)
    rgbaToHex(rgba) {
      if (!rgba) return rgba
      // If it's already a hex color, return it (normalize to lowercase)
      if (rgba.startsWith('#')) return rgba.toLowerCase()
      // Handle both rgba and rgb formats (case insensitive)
      const matches = rgba.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/i)
      if (!matches) return rgba
      const r = parseInt(matches[1])
      const g = parseInt(matches[2])
      const b = parseInt(matches[3])
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
    
    // FontAwesome check method
    checkFontAwesome() {
      // Add FontAwesome class immediately to prevent blocking
      document.body.classList.add('fontawesome-loaded')
      console.log('✅ FontAwesome class added immediately')
      
      try {
        // Check if FontAwesome is loaded by testing if a FontAwesome icon is rendered
        const testElement = document.createElement('i')
        testElement.className = 'fas fa-check'
        testElement.style.position = 'absolute'
        testElement.style.left = '-9999px'
        testElement.style.visibility = 'hidden'
        document.body.appendChild(testElement)
        
        // Check if the FontAwesome CSS is applied (the icon should have a font-family)
        const computedStyle = window.getComputedStyle(testElement)
        const fontFamily = computedStyle.getPropertyValue('font-family')
        
        // Clean up test element
        document.body.removeChild(testElement)
        
        // If FontAwesome is loaded, confirm it's working
        if (fontFamily && fontFamily.includes('Font Awesome')) {
          console.log('✅ FontAwesome is loaded and working')
        } else {
          console.warn('⚠️ FontAwesome may not be loaded properly, but continuing anyway')
          // Don't try to load fallback since we already added the class
        }
      } catch (error) {
        console.error('Error checking FontAwesome:', error)
        // Continue anyway since we already added the class
      }
    },
    
    loadFontAwesomeFallback() {
      // Check if FontAwesome is already loaded via CDN
      if (!document.querySelector('link[href*="font-awesome"]')) {
        console.log('Loading FontAwesome from CDN as fallback...')
        const link = document.createElement('link')
        link.rel = 'stylesheet'
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css'
        link.onload = () => {
          console.log('✅ FontAwesome loaded from CDN')
          document.body.classList.add('fontawesome-loaded')
        }
        link.onerror = () => {
          console.error('❌ Failed to load FontAwesome from CDN')
          // Add class anyway to prevent blocking
          document.body.classList.add('fontawesome-loaded')
        }
        document.head.appendChild(link)
      } else {
        // FontAwesome link exists, add the class immediately
        document.body.classList.add('fontawesome-loaded')
      }
    },
    
    // Map activity types to global icon color classes from main.css
    getActivityIconClass(activityType) {
      switch (activityType) {
        case 'approved':
          return 'icon-success';
        case 'rejected':
          return 'icon-error';
        case 'created':
          return 'icon-primary';
        case 'updated':
          return 'icon-info';
        case 'deactivation':
          return 'icon-warning';
        case 'review':
          return 'icon-info';
        case 'version':
          return 'icon-primary';
        case 'submitted':
          return 'icon-info';
        default:
          return 'icon-primary';
      }
    },
    
    // Framework session management methods
    async checkSelectedFrameworkFromSession() {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in ComplianceDashboard...')
        const response = await axios.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED)
        console.log('📊 DEBUG: Selected framework response:', response.data)
        
        if (response.data && response.data.success && response.data.frameworkId) {
          const frameworkIdFromSession = response.data.frameworkId
          console.log('✅ DEBUG: Found selected framework in session:', frameworkIdFromSession)
          
          // Store the session framework ID for filtering
          this.sessionFrameworkId = frameworkIdFromSession
          
          // Check if this framework exists in our loaded frameworks
          const frameworkExists = this.frameworks.find(f => f.id.toString() === frameworkIdFromSession.toString())
          
          if (frameworkExists) {
            console.log('✅ DEBUG: Framework exists in loaded frameworks:', frameworkExists.name)
            // Automatically select the framework from session
            this.selectedFramework = frameworkExists.id.toString()
            console.log('✅ DEBUG: Auto-selected framework from session:', this.selectedFramework)
            // Refresh dashboard data with the selected framework
            await this.fetchDashboardData()
          } else {
            console.log('⚠️ DEBUG: Framework from session (ID:', frameworkIdFromSession, ') not found in loaded frameworks')
            console.log('📋 DEBUG: Available frameworks:', this.frameworks.map(f => ({ id: f.id, name: f.name })))
            // Clear the session framework ID since it doesn't exist
            this.sessionFrameworkId = null
          }
        } else {
          console.log('ℹ️ DEBUG: No framework found in session - All Frameworks selected')
          this.sessionFrameworkId = null
          // Ensure selectedFramework is empty for "All Frameworks"
          this.selectedFramework = ''
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework from session:', error)
        this.sessionFrameworkId = null
      }
    },
    
    async saveFrameworkToSession(frameworkId) {
      try {
        console.log('💾 DEBUG: Saving framework to session:', frameworkId)
        const userId = localStorage.getItem('user_id') || 'default_user'
        await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, { 
          frameworkId,
          userId
        })
        console.log('✅ DEBUG: Framework saved to session successfully')
      } catch (error) {
        console.error('❌ DEBUG: Error saving framework to session:', error)
      }
    },
    
    async clearFrameworkFromSession() {
      try {
        console.log('🧹 DEBUG: Clearing framework from session')
        const userId = localStorage.getItem('user_id') || 'default_user'
        await axios.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, { 
          frameworkId: null,
          userId
        })
        console.log('✅ DEBUG: Framework cleared from session successfully')
      } catch (error) {
        console.error('❌ DEBUG: Error clearing framework from session:', error)
      }
    },
    
    onFrameworkChange(option) {
      // CustomDropdown emits option object with value and label
      const value = option && option.value !== undefined ? option.value : option
      this.selectedFramework = value || ''
      this.handleFrameworkChange()
    },
    
    onTimeRangeChange(option) {
      const value = option && option.value !== undefined ? option.value : option
      this.selectedTimeRange = value || 'Last 6 Months'
      this.fetchDashboardData()
    },
    
    onCategoryChange(option) {
      const value = option && option.value !== undefined ? option.value : option
      this.selectedCategory = value || 'All Categories'
      this.fetchDashboardData()
    },
    
    onPriorityChange(option) {
      const value = option && option.value !== undefined ? option.value : option
      this.selectedPriority = value || 'All Priorities'
      this.fetchDashboardData()
    },
    
    async handleFrameworkChange() {
      console.log('🔍 DEBUG: handleFrameworkChange called with:', this.selectedFramework)
      
      // Find the framework name from the frameworks list
      const frameworkName = this.frameworks.find(f => f.id === this.selectedFramework)?.name || 'All Frameworks'
      
      // Update Vuex store (this will also save to backend session)
      await this.setFramework({
        id: this.selectedFramework || 'all',
        name: frameworkName
      })
      
      console.log('✅ DEBUG: Framework saved to Vuex store:', this.selectedFramework)
      
      // Note: Data refresh will be triggered by the watcher
    },
    
    destroyAllCharts() {
      Object.values(this.charts).forEach(chart => {
        if (chart) {
          chart.destroy()
        }
      })
      this.charts = {
        criticalityChart: null,
        statusChart: null,
        activeInactiveChart: null,
        manualAutomaticChart: null,
        maturityLevelChart: null
      }
    },
    
    async fetchFrameworks() {
      try {
        this.loadingFrameworks = true
        console.log('🔍 [ComplianceDashboard] Checking for cached framework data...')
        
        // Check if prefetch was never started (user came directly to this page)
        if (!window.complianceDataFetchPromise && !complianceDataService.hasFrameworksCache()) {
          console.log('🚀 [ComplianceDashboard] Starting prefetch now (user came directly to this page)...')
          window.complianceDataFetchPromise = complianceDataService.fetchAllComplianceData()
        }
        
        // Wait for prefetch if it's running
        if (window.complianceDataFetchPromise) {
          console.log('⏳ [ComplianceDashboard] Waiting for prefetch to complete...')
          try {
            await window.complianceDataFetchPromise
            console.log('✅ [ComplianceDashboard] Prefetch completed')
          } catch (error) {
            console.warn('⚠️ [ComplianceDashboard] Prefetch failed, will fetch directly')
          }
        }
        
        // FIRST: Try to get data from cache
        if (complianceDataService.hasFrameworksCache()) {
          console.log('✅ [ComplianceDashboard] Using cached framework data')
          const cachedFrameworks = complianceDataService.getData('frameworks') || []
          
          // Filter to only show active frameworks
          const activeFrameworks = cachedFrameworks.filter(fw => {
            const status = fw.ActiveInactive || fw.status || '';
            return status.toLowerCase() === 'active';
          });
          
          this.frameworks = activeFrameworks.map(framework => ({
            id: framework.FrameworkId || framework.id,
            name: framework.FrameworkName || framework.name || 'Unknown Framework'
          }))
          console.log(`[ComplianceDashboard] Loaded ${this.frameworks.length} frameworks from cache (prefetched on Home page)`)
        } else {
          // FALLBACK: Fetch from API if cache is empty
          console.log('⚠️ [ComplianceDashboard] No cached data found, fetching from API...')
          const response = await this.api.complianceService.getComplianceFrameworks()
          console.log('Frameworks API response:', response.data)
          
          // Handle the API response format
          let frameworksData = []
          if (response.data.success && response.data.frameworks) {
            frameworksData = response.data.frameworks
          } else if (response.data.success && Array.isArray(response.data.data)) {
            frameworksData = response.data.data
          } else if (Array.isArray(response.data)) {
            frameworksData = response.data
          } else {
            console.error('Unexpected frameworks response format:', response.data)
            this.frameworks = []
            return
          }
          
          // Filter to only show active frameworks
          const activeFrameworks = frameworksData.filter(fw => {
            const status = fw.ActiveInactive || fw.status || '';
            return status.toLowerCase() === 'active';
          });
          
          this.frameworks = activeFrameworks.map(framework => ({
            id: framework.id || framework.FrameworkId,
            name: framework.name || framework.FrameworkName || 'Unknown Framework'
          }))
          
          console.log(`[ComplianceDashboard] Loaded ${this.frameworks.length} frameworks directly from API (cache unavailable)`)
          
          // Update cache so subsequent pages benefit
          complianceDataService.setData('frameworks', frameworksData)
          console.log('ℹ️ [ComplianceDashboard] Cache updated after direct API fetch')
        }
        
        console.log('Processed frameworks:', this.frameworks)
      } catch (error) {
        console.error('Error fetching frameworks:', error)
        this.frameworks = []
      } finally {
        this.loadingFrameworks = false
      }
    },
    
    async fetchRecentActivities() {
      try {
        // Only show loading if we don't have any activities yet
        if (this.recentActivities.length === 0) {
          this.loadingActivities = true
        }
        console.log('Fetching recent activities...')
        
        // Get current user ID for reviewer
        const currentUserId = localStorage.getItem('user_id') || sessionStorage.getItem('userId') || 2
        const reviewerId = parseInt(currentUserId) || 2
        
        // Fetch activities with timeout to prevent hanging
        // Only fetch approvals - frameworks fetch is not needed for activities
        let approvalsResponse = null
        try {
          approvalsResponse = await Promise.race([
            this.api.complianceService.getCompliancePolicyApprovals({ reviewer_id: reviewerId }),
            new Promise((_, reject) => setTimeout(() => reject(new Error('Approvals API timeout')), 10000))
          ])
        } catch (error) {
          console.warn('Error fetching approvals for activities (non-critical):', error)
          // Continue without approvals data - activities will be empty but page won't hang
        }
        
        let activities = []
        
        // Process policy approvals for recent activities
        if (approvalsResponse && approvalsResponse.data && approvalsResponse.data.success && approvalsResponse.data.data) {
          const approvals = approvalsResponse.data.data
          
          // Sort approvals by most recent first
          const sortedApprovals = approvals.sort((a, b) => {
            const dateA = new Date(a.ApprovedDate || a.ExtractedData?.CreatedByDate || '1970-01-01')
            const dateB = new Date(b.ApprovedDate || b.ExtractedData?.CreatedByDate || '1970-01-01')
            return dateB - dateA
          })
          
          // Process different types of activities
          sortedApprovals.slice(0, 10).forEach(approval => {
            const extractedData = approval.ExtractedData || {}
            const complianceTitle = extractedData.ComplianceTitle || extractedData.ComplianceItemDescription || 'Unknown Compliance'
            const createdBy = extractedData.CreatedByName || 'Unknown User'
            const version = extractedData.ComplianceVersion || '1.0'
            
            // Determine activity type based on approval status and data
            if (approval.ApprovedNot === true) {
              // Approved compliance
              activities.push({
                type: 'approved',
                icon: 'fas fa-check-circle',
                title: 'Compliance Approved',
                description: `"${this.truncateText(complianceTitle, 50)}" approved by reviewer`,
                time: this.formatRelativeTime(approval.ApprovedDate),
                metadata: {
                  complianceId: extractedData.compliance_id,
                  version: version,
                  approver: 'Reviewer'
                }
              })
            } else if (approval.ApprovedNot === false) {
              // Rejected compliance
              activities.push({
                type: 'rejected',
                icon: 'fas fa-times-circle',
                title: 'Compliance Rejected',
                description: `"${this.truncateText(complianceTitle, 50)}" needs revision`,
                time: this.formatRelativeTime(approval.ApprovedDate),
                metadata: {
                  complianceId: extractedData.compliance_id,
                  version: version,
                  reviewer: 'Reviewer'
                }
              })
            } else if (approval.ApprovedNot === null) {
              // Check if it's a deactivation request
              if (extractedData.type === 'compliance_deactivation' || extractedData.RequestType === 'Change Status to Inactive') {
                activities.push({
                  type: 'deactivation',
                  icon: 'fas fa-power-off',
                  title: 'Deactivation Request',
                  description: `Deactivation requested for compliance ID ${extractedData.compliance_id}`,
                  time: this.formatRelativeTime(extractedData.CreatedByDate),
                  metadata: {
                    complianceId: extractedData.compliance_id,
                    reason: extractedData.reason || 'No reason provided'
                  }
                })
              } else {
                // Check if it's a new version (higher version number)
                if (parseFloat(version) > 1.0) {
                  activities.push({
                    type: 'version',
                    icon: 'fas fa-code-branch',
                    title: 'New Version Created',
                    description: `Version ${version} of "${this.truncateText(complianceTitle, 40)}" by ${createdBy}`,
                    time: this.formatRelativeTime(extractedData.CreatedByDate),
                    metadata: {
                      complianceId: extractedData.compliance_id,
                      version: version,
                      creator: createdBy
                    }
                  })
                } else {
                  // New compliance under review
                  activities.push({
                    type: 'created',
                    icon: 'fas fa-plus-circle',
                    title: 'New Compliance Created',
                    description: `"${this.truncateText(complianceTitle, 50)}" created by ${createdBy}`,
                    time: this.formatRelativeTime(extractedData.CreatedByDate),
                    metadata: {
                      complianceId: extractedData.compliance_id,
                      version: version,
                      creator: createdBy
                    }
                  })
                }
              }
            }
          })
        }
        
        // Skip the slow nested API calls - they're too slow and not essential
        // The approvals data should be sufficient for recent activities
        // If we need more data, we can add a dedicated API endpoint later
        
        // Sort all activities by time (most recent first) and limit to top 10
        activities.sort((a, b) => {
          const timeA = this.parseRelativeTime(a.time)
          const timeB = this.parseRelativeTime(b.time)
          return timeA - timeB // Sort by actual time difference (smaller = more recent)
        })
        
        // Remove duplicates based on description and limit to latest 3 items
        const uniqueActivities = activities.filter((activity, index, self) => 
          index === self.findIndex(a => a.description === activity.description)
        ).slice(0, 3)
        
        this.recentActivities = uniqueActivities
        console.log(`Loaded ${this.recentActivities.length} recent activities`)
        
        // If no activities found, log a warning but don't show error message
        if (this.recentActivities.length === 0) {
          console.warn('⚠️ No recent compliance activities found. This is normal if there are no recent compliance actions.')
        }
        
      } catch (error) {
        console.error('Error fetching recent activities:', error)
        // Don't set error activity - just leave empty array
        // This prevents showing error message when there are simply no activities
        this.recentActivities = []
      } finally {
        this.loadingActivities = false
      }
    },
    
    truncateText(text, maxLength) {
      if (!text) return 'Unknown'
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
    },
    
    formatRelativeTime(dateString) {
      if (!dateString) return 'Unknown time'
      
      try {
        const date = new Date(dateString)
        const now = new Date()
        const diffInSeconds = Math.floor((now - date) / 1000)
        
        if (diffInSeconds < 60) {
          return 'Just now'
        } else if (diffInSeconds < 3600) {
          const minutes = Math.floor(diffInSeconds / 60)
          return `${minutes} minute${minutes === 1 ? '' : 's'} ago`
        } else if (diffInSeconds < 86400) {
          const hours = Math.floor(diffInSeconds / 3600)
          return `${hours} hour${hours === 1 ? '' : 's'} ago`
        } else if (diffInSeconds < 604800) {
          const days = Math.floor(diffInSeconds / 86400)
          return `${days} day${days === 1 ? '' : 's'} ago`
        } else {
          const weeks = Math.floor(diffInSeconds / 604800)
          return `${weeks} week${weeks === 1 ? '' : 's'} ago`
        }
      } catch (error) {
        console.error('Error formatting date:', error)
        return 'Unknown time'
      }
    },
    
    parseRelativeTime(timeString) {
      // Convert relative time back to seconds for sorting
      if (timeString === 'Just now') return 0
      
      const match = timeString.match(/(\d+)\s+(minute|hour|day|week)s?\s+ago/)
      if (match) {
        const value = parseInt(match[1])
        const unit = match[2]
        
        switch (unit) {
          case 'minute': return value * 60
          case 'hour': return value * 3600
          case 'day': return value * 86400
          case 'week': return value * 604800
          default: return 999999
        }
      }
      
      return 999999 // Unknown time goes to end
    },
    
    refreshRecentActivities() {
      // Don't set loadingActivities = true here to allow background refresh
      // Existing activities will remain visible while new data loads
      this.fetchRecentActivities()
    },

    async fetchDashboardData() {
      try {
        console.log('Starting fetchDashboardData for compliance...')
        console.log('Current filters - Framework:', this.selectedFramework, 'Time:', this.selectedTimeRange, 'Category:', this.selectedCategory, 'Priority:', this.selectedPriority)

        // Fetch dashboard summary data
        let dashboardResponse
        try {
          const dashboardRequest = {}
          
          // Add framework filter if selected
          if (this.selectedFramework && this.selectedFramework !== '') {
            dashboardRequest.framework_id = this.selectedFramework
            console.log('Applying framework filter to dashboard:', this.selectedFramework)
          } else {
            console.log('No framework filter applied')
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
          console.log('Making API call to:', this.api.complianceService.getComplianceDashboard.toString())
          dashboardResponse = await this.api.complianceService.getComplianceDashboard(dashboardRequest)
          console.log('Compliance Dashboard API Response:', dashboardResponse.data)
        } catch (err) {
          console.error('Error fetching dashboard data:', err)
          console.error('Error details:', err.response?.data || err.message)
          throw new Error(`Dashboard fetch failed: ${err.message}`)
        }

        // Fetch data for each chart
        const chartPromises = [
          this.fetchChartData('Criticality', 'bar'),
          this.fetchChartData('Status', 'doughnut'),
          this.fetchChartData('ActiveInactive', 'bar'),
          this.fetchChartData('ManualAutomatic', 'doughnut'),
          this.fetchChartData('MaturityLevel', 'bar')
        ]

        const [criticalityData, statusData, activeInactiveData, manualAutomaticData, maturityLevelData] = await Promise.all(chartPromises)

        if (dashboardResponse.data && dashboardResponse.data.success) {
          const summary = dashboardResponse.data.data?.summary || {}
          console.log('Dashboard summary data:', summary)
          
          this.dashboardData = {
            status_counts: summary.status_counts || {},
            total_count: summary.total_count || 0,
            total_findings: summary.total_findings || 0,
            approval_rate: summary.approval_rate || 0
          }
          
          // Update chart data
          this.chartData = {
            criticality: criticalityData,
            status: statusData,
            activeInactive: activeInactiveData,
            manualAutomatic: manualAutomaticData,
            maturityLevel: maturityLevelData
          }
          
          console.log('Updated chart data:', this.chartData)
          
          // Render charts immediately after data is loaded
          await this.renderChartsAfterDataLoad()
        } else {
          const errorMessage = dashboardResponse.data?.message || 'API request failed'
          console.error('API Error:', errorMessage)
          throw new Error(errorMessage)
        }
      } catch (error) {
        console.error('Error in fetchDashboardData:', error)
        
        // Set default values on error
        this.dashboardData = {
          status_counts: { approved: 0, active: 0, under_review: 0 },
          total_count: 0,
          total_findings: 0,
          approval_rate: 0
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
          criticality: defaultChartData,
          status: defaultChartData,
          activeInactive: defaultChartData,
          manualAutomatic: defaultChartData,
          maturityLevel: defaultChartData
        }
        
        await this.renderChartsAfterDataLoad()
      }
    },
    async fetchChartData(yAxis, chartType) {
      try {
        const requestData = {
          xAxis: 'Compliance',
          yAxis: yAxis
        }
        
        // Add framework filter if selected
        if (this.selectedFramework && this.selectedFramework !== '') {
          requestData.frameworkId = this.selectedFramework
          console.log(`Applying framework filter for ${yAxis} chart:`, this.selectedFramework)
        } else {
          console.log(`No framework filter applied for ${yAxis} chart`)
        }
        
        // Add other filters
        if (this.selectedTimeRange && this.selectedTimeRange !== 'Last 6 Months') {
          requestData.timeRange = this.selectedTimeRange
        }
        
        if (this.selectedCategory && this.selectedCategory !== 'All Categories') {
          requestData.category = this.selectedCategory
        }
        
        if (this.selectedPriority && this.selectedPriority !== 'All Priorities') {
          requestData.priority = this.selectedPriority
        }
        
        console.log(`Fetching ${yAxis} chart data with request:`, requestData)
        console.log('Making analytics API call to:', this.api.complianceService.getComplianceAnalytics.toString())
        const response = await this.api.complianceService.getComplianceAnalytics(requestData)
        
        console.log(`${yAxis} chart response:`, response.data)
        
        if (response.data && response.data.success && response.data.chartData) {
          return response.data.chartData
        } else {
          console.warn(`No data received for ${yAxis} chart`)
          return this.getDefaultChartData(chartType)
        }
      } catch (error) {
        console.error(`Error fetching ${yAxis} chart data:`, error)
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
      
      if (chartType === 'doughnut') {
        defaultData.datasets[0].backgroundColor = [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)'
        ]
        defaultData.datasets[0].borderColor = [
          'rgb(255, 99, 132)',
          'rgb(54, 162, 235)',
          'rgb(255, 206, 86)'
        ]
      }
      
      return defaultData
    },
    
    async renderChartsAfterDataLoad() {
      console.log('🎨 Rendering charts instantly...')
      
      // Ensure all canvas elements exist
      const chartIds = ['criticalityChart', 'statusChart', 'activeInactiveChart', 'manualAutomaticChart', 'maturityLevelChart']
      const existingCanvases = chartIds.filter(id => document.getElementById(id))
      
      if (existingCanvases.length === chartIds.length) {
        console.log('✅ All canvas elements found, rendering charts instantly...')
        await this.updateAllCharts()
      } else {
        console.log('⏳ Canvas elements not ready, retrying instantly...')
        // Retry immediately without delay
        this.$nextTick(() => {
          this.renderChartsAfterDataLoad()
        })
      }
    },
    
    async updateAllCharts() {
      console.log('🔄 DEBUG: Updating all charts instantly...')
      console.log('📊 DEBUG: Chart data available:', {
        criticality: !!this.chartData.criticality,
        status: !!this.chartData.status,
        activeInactive: !!this.chartData.activeInactive,
        manualAutomatic: !!this.chartData.manualAutomatic,
        maturityLevel: !!this.chartData.maturityLevel
      })
      
      // Check if all canvas elements exist
      const chartIds = ['criticalityChart', 'statusChart', 'activeInactiveChart', 'manualAutomaticChart', 'maturityLevelChart']
      const missingCanvases = chartIds.filter(id => !document.getElementById(id))
      
      if (missingCanvases.length > 0) {
        console.warn('⚠️ DEBUG: Some canvas elements not found:', missingCanvases)
        console.log('🔄 DEBUG: Retrying chart update instantly...')
        // Retry immediately without delay
        this.$nextTick(() => {
          this.updateAllCharts()
        })
        return
      }
      
      console.log('✅ DEBUG: All canvas elements found, proceeding with instant chart updates')
      console.log('🎨 DEBUG: Current colorblindness mode:', this.colorblindMode)
      
      // Update charts with error handling
      try {
        this.updateChart('criticalityChart', 'bar', this.chartData.criticality)
        this.updateChart('statusChart', 'doughnut', this.chartData.status)
        this.updateChart('activeInactiveChart', 'bar', this.chartData.activeInactive)
        this.updateChart('manualAutomaticChart', 'doughnut', this.chartData.manualAutomatic)
        this.updateChart('maturityLevelChart', 'bar', this.chartData.maturityLevel)
        console.log('✅ DEBUG: All charts updated instantly')
      } catch (error) {
        console.error('❌ DEBUG: Error updating charts:', error)
      }
    },
    updateChart(chartId, chartType, chartData) {
      try {
        console.log(`🔄 DEBUG: Updating chart ${chartId} with type ${chartType}, colorblind mode: ${this.colorblindMode}`)
        
        // Destroy existing chart if it exists
        if (this.charts[chartId]) {
          console.log(`🗑️ Destroying existing chart: ${chartId}`)
          this.charts[chartId].destroy()
          this.charts[chartId] = null
        }

        // Get the canvas element
        const canvas = document.getElementById(chartId)
        if (!canvas) {
          console.error(`❌ DEBUG: Chart canvas not found: ${chartId}`)
          return
        }
        
        console.log(`✅ DEBUG: Canvas found for ${chartId}:`, canvas)
        
        // Clear the canvas to ensure fresh rendering
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height)
        }

        // Create the chart configuration with chartId for proper color mapping
        const config = this.createChartConfig(chartType, chartData, chartId)
        
        // Debug: Log the colors being used (especially for orange colors)
        if (config.data && config.data.datasets && config.data.datasets[0]) {
          const bgColors = config.data.datasets[0].backgroundColor
          const borderColors = config.data.datasets[0].borderColor
          
          // Check if orange colors are present
          const hasOrange = Array.isArray(bgColors) 
            ? bgColors.some(c => c && (c.includes('255, 152, 0') || c.includes('ff9800') || c.includes('FF9800')))
            : (bgColors && (bgColors.includes('255, 152, 0') || bgColors.includes('ff9800') || bgColors.includes('FF9800')))
          
          if (hasOrange) {
            console.log(`🔶 DEBUG: Chart ${chartId} has ORANGE colors (mode: ${this.colorblindMode}):`, {
              backgroundColor: bgColors,
              borderColor: borderColors,
              shouldConvert: this.colorblindMode === 'protanopia' || this.colorblindMode === 'deuteranopia'
            })
          } else {
            console.log(`🎨 DEBUG: Chart ${chartId} colors (mode: ${this.colorblindMode}):`, {
              backgroundColor: bgColors,
              borderColor: borderColors
            })
          }
        }

        // Create new chart instance
        this.charts[chartId] = new ChartJS(canvas, config)
        console.log(`✅ DEBUG: Chart ${chartId} created successfully`)
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

      // Create dataset with proper colors
      const dataset = {
        label: chartData.datasets[0]?.label || `Compliance Data`,
        data: chartData.datasets[0]?.data || [],
        backgroundColor: this.getBackgroundColors(chartType, chartData.labels, chartId),
        borderColor: this.getBorderColors(chartType, chartData.labels, chartId),
        borderWidth: 1
      }

      // Add pie/doughnut specific properties
      if (['pie', 'doughnut'].includes(chartType)) {
        dataset.backgroundColor = this.getBackgroundColors(chartType, chartData.labels, chartId).map(color => 
          color.replace('0.6', '0.8') // Make pie/doughnut colors more opaque
        )
      }

      return {
        type: chartType,
        data: {
          labels: chartData.labels,
          datasets: [dataset]
        },
        options: this.getChartOptions(chartType)
      }
    },
    getChartOptions(chartType) {
      const options = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 800,
          easing: 'easeInOutQuad'
        },
        plugins: {
          legend: {
            display: ['pie', 'doughnut'].includes(chartType),
            position: ['pie', 'doughnut'].includes(chartType) ? 'right' : 'top',
            labels: {
              padding: 20,
              usePointStyle: false,
              font: {
                size: 12
              }
            }
          },
          tooltip: {
            enabled: true,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: 'white',
            bodyColor: 'white',
            borderColor: 'rgba(255, 255, 255, 0.1)',
            borderWidth: 1,
            cornerRadius: 6,
            displayColors: true,
            callbacks: {
              label: (context) => {
                if (['pie', 'doughnut'].includes(chartType)) {
                  const label = context.label || ''
                  const value = context.raw || 0
                  const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0)
                  const percentage = ((value / total) * 100).toFixed(1)
                  return `${label}: ${value} (${percentage}%)`
                }
                return `${context.dataset.label}: ${context.raw}`
              }
            }
          }
        },
        layout: {
          padding: {
            top: 10,
            bottom: 10,
            left: 10,
            right: 10
          }
        }
      }

      // Add scales for bar and line charts
      if (['bar', 'line'].includes(chartType)) {
        options.scales = {
          x: {
            grid: {
              display: false
            },
            ticks: {
              font: {
                size: 11
              }
            },
            // Reduce bar thickness for bar charts
            ...(chartType === 'bar' && {
              categoryPercentage: 0.6,
              barPercentage: 0.6
            })
          },
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.1)'
            },
            ticks: {
              stepSize: 1,
              precision: 0,
              font: {
                size: 11
              }
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
        Criticality: {
          'High': 'rgba(244, 67, 54, 0.6)',      // Red
          'Medium': 'rgba(255, 152, 0, 0.6)',     // Orange
          'Low': 'rgba(76, 175, 80, 0.6)'        // Green
        },
        Status: {
          'Approved': 'rgba(76, 175, 80, 0.6)',   // Green
          'Under Review': 'rgba(255, 152, 0, 0.6)', // Orange
          'Rejected': 'rgba(244, 67, 54, 0.6)',   // Red
          'Active': 'rgba(33, 150, 243, 0.6)'     // Blue
        },
        ActiveInactive: {
          'Active': 'rgba(76, 175, 80, 0.6)',     // Green
          'Inactive': 'rgba(244, 67, 54, 0.6)'   // Red
        },
        ManualAutomatic: {
          'Manual': 'rgba(33, 150, 243, 0.6)',   // Blue
          'Automatic': 'rgba(156, 39, 176, 0.6)' // Purple
        },
        MaturityLevel: {
          'Initial': 'rgba(244, 67, 54, 0.6)',    // Red
          'Developing': 'rgba(255, 152, 0, 0.6)', // Orange
          'Defined': 'rgba(255, 235, 59, 0.6)',  // Yellow
          'Managed': 'rgba(76, 175, 80, 0.6)',   // Green
          'Optimizing': 'rgba(33, 150, 243, 0.6)' // Blue
        }
      }

      // For doughnut charts, use a predefined color palette
      if (chartType === 'doughnut') {
        const doughnutColors = [
          'rgba(255, 99, 132, 0.8)',  // Red/Pink
          'rgba(54, 162, 235, 0.8)',  // Blue
          'rgba(255, 206, 86, 0.8)',  // Yellow
          'rgba(75, 192, 192, 0.8)',  // Teal (green-blue)
          'rgba(153, 102, 255, 0.8)', // Purple
          'rgba(255, 159, 64, 0.8)'   // Orange
        ]
        // Apply colorblindness conversion
        return doughnutColors.map(color => this.convertColorForColorblind(color, 0.8))
      }

      // Determine the category based on chartId
      let category = 'Criticality'
      if (chartId.includes('status')) {
        category = 'Status'
      } else if (chartId.includes('activeInactive')) {
        category = 'ActiveInactive'
      } else if (chartId.includes('manualAutomatic')) {
        category = 'ManualAutomatic'
      } else if (chartId.includes('maturityLevel')) {
        category = 'MaturityLevel'
      }

      // For bar charts, map colors based on labels and apply colorblindness conversion
      return labels?.map(label => {
        const originalColor = colorMaps[category]?.[label] || 'rgba(158, 158, 158, 0.6)'
        const convertedColor = this.convertColorForColorblind(originalColor, 0.6)
        
        // Debug: Log orange and yellow color conversion
        if (originalColor.includes('255, 152, 0') || originalColor.includes('ff9800') || 
            originalColor.includes('255, 235, 59') || originalColor.includes('ffeb3b')) {
          console.log(`🔶 getBackgroundColors: Converting color for label "${label}":`, {
            original: originalColor,
            converted: convertedColor,
            mode: this.colorblindMode,
            category: category,
            hexValue: this.rgbaToHex(originalColor)
          })
        }
        
        return convertedColor
      }) || []
    },
    getBorderColors(chartType, labels, chartId = '') {
      const colorMaps = {
        Criticality: {
          'High': '#F44336',      // Red
          'Medium': '#FF9800',    // Orange
          'Low': '#4CAF50'        // Green
        },
        Status: {
          'Approved': '#4CAF50',   // Green
          'Under Review': '#FF9800', // Orange
          'Rejected': '#F44336',   // Red
          'Active': '#2196F3'      // Blue
        },
        ActiveInactive: {
          'Active': '#4CAF50',     // Green
          'Inactive': '#F44336'    // Red
        },
        ManualAutomatic: {
          'Manual': '#2196F3',     // Blue
          'Automatic': '#9C27B0'   // Purple
        },
        MaturityLevel: {
          'Initial': '#F44336',    // Red
          'Developing': '#FF9800', // Orange
          'Defined': '#FFEB3B',    // Yellow
          'Managed': '#4CAF50',    // Green
          'Optimizing': '#2196F3'  // Blue
        }
      }

      // For doughnut charts, use a predefined color palette
      if (chartType === 'doughnut') {
        const doughnutColors = [
          'rgb(255, 99, 132)',  // Red/Pink
          'rgb(54, 162, 235)',  // Blue
          'rgb(255, 206, 86)',  // Yellow
          'rgb(75, 192, 192)',  // Teal (green-blue)
          'rgb(153, 102, 255)', // Purple
          'rgb(255, 159, 64)'   // Orange
        ]
        // Apply colorblindness conversion (border colors are rgb format, convert to hex first)
        return doughnutColors.map(color => {
          const hex = this.rgbaToHex(color)
          // For border colors, we want hex output, so pass opacity 1.0 but check if we need to return hex
          const converted = this.convertColorForColorblind(hex, 1.0)
          // If conversion returned hex, use it; otherwise convert back to rgb
          if (converted.startsWith('#')) {
            // Convert hex back to rgb for border colors
            const r = parseInt(converted.slice(1, 3), 16)
            const g = parseInt(converted.slice(3, 5), 16)
            const b = parseInt(converted.slice(5, 7), 16)
            return `rgb(${r}, ${g}, ${b})`
          }
          return converted || color
        })
      }

      // Determine the category based on chartId
      let category = 'Criticality'
      if (chartId.includes('status')) {
        category = 'Status'
      } else if (chartId.includes('activeInactive')) {
        category = 'ActiveInactive'
      } else if (chartId.includes('manualAutomatic')) {
        category = 'ManualAutomatic'
      } else if (chartId.includes('maturityLevel')) {
        category = 'MaturityLevel'
      }

      // For bar charts, map colors based on labels
      return labels?.map(label => {
        return colorMaps[category]?.[label] || '#9E9E9E'
      }) || []
    },
    async refreshData() {
      console.log('🔄 Manual refresh triggered')
      try {
        // Fetch fresh data in parallel for faster loading
        await Promise.all([
          this.fetchFrameworks(),
          this.fetchDashboardData()
        ])
        this.fetchRecentActivities()
        
        console.log('✅ Manual refresh completed successfully')
      } catch (error) {
        console.error('❌ Error during manual refresh:', error)
      }
    },
    
    async clearFilters() {
      this.selectedFramework = ''
      this.selectedTimeRange = 'Last 6 Months'
      this.selectedCategory = 'All Categories'
      this.selectedPriority = 'All Priorities'
      
      // Clear session framework ID when clearing filters
      this.sessionFrameworkId = null
      await this.clearFrameworkFromSession()
      
      this.fetchDashboardData()
    },
    
    // Navigation function to go back to AuditManagementView
    goBackToAuditManagement() {
      this.$router.push({ name: 'AuditManagement' })
    },
    
    // Helper method to get framework name by ID
    getFrameworkName(frameworkId) {
      const framework = this.frameworks.find(f => f.id == frameworkId)
      return framework ? framework.name : 'Unknown Framework'
    },

    // Handle export format selection from custom dropdown
    selectExportFormatOption(option) {
      // Options come as objects { value, label }
      const value = option && option.value !== undefined ? option.value : option
      this.exportFormat = value || ''
      // Close the export dropdown after selection
      this.isExportDropdownOpen = false
    },

    // Export dashboard as PDF
    async exportDashboardAsPDF() {
      this.isExporting = true
      try {
        await this.$nextTick() // Ensure all components are rendered
        
        const dashboardElement = document.querySelector('.compliance-dashboard-container')
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
            const clonedDashboard = clonedDoc.querySelector('.compliance-dashboard-container')
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
            const chartContainers = clonedDoc.querySelectorAll('.chart-container')
            chartContainers.forEach(container => {
              container.style.display = 'block'
              container.style.visibility = 'visible'
              container.style.opacity = '1'
              container.style.minHeight = '300px'
              container.style.background = '#ffffff'
            })

            // Ensure all chart cards are visible
            const chartCards = clonedDoc.querySelectorAll('.chart-card')
            chartCards.forEach(card => {
              card.style.display = 'flex'
              card.style.visibility = 'visible'
              card.style.opacity = '1'
              card.style.background = '#ffffff'
            })
          }
        })

        const imgData = canvas.toDataURL('image/png', 1.0)
        
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

        // Generate filename with timestamp
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
        const filename = `Compliance-Dashboard-${timestamp}.pdf`

        // Download the PDF
        pdf.save(filename)

        console.log('PDF downloaded successfully')
        
        // Show success feedback
        this.exportSuccess = true
        setTimeout(() => {
          this.exportSuccess = false
        }, 2000)
      } catch (error) {
        console.error('Error generating PDF:', error)
        alert('Failed to generate PDF. Please try again.')
      } finally {
        this.isExporting = false
      }
    }
  }
}
</script>

<style>
@import './ComplianceDashboard.css';
@import '@/assets/css/dropdown.css';
@import '@/assets/css/main.css';
</style> 