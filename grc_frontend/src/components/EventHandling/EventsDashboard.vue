<template>
  <div class="events-dashboard-container">
    <!-- Header Section: title + export controls (styles from main.css) -->
    <div class="events-dashboard-header">
      <h1 class="events-dashboard-title">Events Dashboard</h1>
      <div class="export-controls">
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

    <!-- Filters Section -->
    <div class="events-dashboard-filters">
      <EventFilters @filter-change="handleFilterChange" :show-advanced="false" :show-export="false" />
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="events-dashboard-loading">
      <div class="events-dashboard-loading-content">
        <div class="events-dashboard-loading-spinner"></div>
        <p class="events-dashboard-loading-text">Loading dashboard data...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="events-dashboard-error">
      <div class="events-dashboard-error-content">
        <div class="events-dashboard-error-icon">
          <svg class="events-dashboard-error-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <div class="events-dashboard-error-details">
          <h3 class="events-dashboard-error-title">Error loading dashboard</h3>
          <p class="events-dashboard-error-message">{{ error }}</p>
          <button @click="fetchDashboardData" class="events-dashboard-error-retry">
            Try Again
          </button>
        </div>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div v-else-if="dashboardData" class="events-dashboard-content">
      <!-- KPI Cards (using global KPI styles from main.css) -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-card-icon kpi-icon-total">
            <i class="fas fa-calendar-check"></i>
          </div>
          <div class="kpi-card-body">
            <p class="kpi-card-title">Total Events</p>
            <p class="kpi-card-value">{{ dashboardData.kpis.total_events }}</p>
            <p class="kpi-card-subtitle">
              <span class="kpi-change-positive">
                {{ dashboardData.kpis.trend_percentage }}%
              </span>
              &nbsp;vs last month
            </p>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-card-icon kpi-icon-open">
            <i class="fas fa-calendar-alt"></i>
          </div>
          <div class="kpi-card-body">
            <p class="kpi-card-title">Upcoming Events</p>
            <p class="kpi-card-value">{{ dashboardData.kpis.upcoming_events }}</p>
            <p class="kpi-card-subtitle">
              <span class="kpi-change-negative">
                2%
              </span>
              &nbsp;vs last month
            </p>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-card-icon kpi-icon-rejected">
            <i class="fas fa-exclamation-circle"></i>
          </div>
          <div class="kpi-card-body">
            <p class="kpi-card-title">Overdue Events</p>
            <p class="kpi-card-value">{{ dashboardData.kpis.overdue_events }}</p>
            <p class="kpi-card-subtitle">
              <span class="kpi-change-negative">
                1%
              </span>
              &nbsp;vs last month
            </p>
          </div>
        </div>

        <div class="kpi-card">
          <div class="kpi-card-icon kpi-icon-approved">
            <i class="fas fa-hourglass-half"></i>
          </div>
          <div class="kpi-card-body">
            <p class="kpi-card-title">Pending Approvals</p>
            <p class="kpi-card-value">{{ dashboardData.kpis.pending_approvals }}</p>
            <p class="kpi-card-subtitle">
              <span class="kpi-change-positive">
                3%
              </span>
              &nbsp;vs last month
            </p>
          </div>
        </div>
      </div>

      <!-- Charts Row 1 -->
      <div class="global-dashboard-charts-grid">
        <!-- Events by Category -->
        <div class="global-dashboard-chart-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">
              Events by Category
            </h3>
            <button class="global-dashboard-chart-icon" style="color: #60A5FA;">
              <i class="fas fa-stream"></i>
            </button>
          </div>
          <div class="global-dashboard-chart-container">
            <canvas ref="eventsByCategoryChart" width="400" height="300"></canvas>
          </div>
        </div>

        <!-- Events by Framework -->
        <div class="global-dashboard-chart-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">
              Events by Framework
            </h3>
            <button class="global-dashboard-chart-icon" style="color: #A78BFA;">
              <i class="fas fa-project-diagram"></i>
            </button>
          </div>
          <div class="global-dashboard-chart-container">
            <canvas ref="eventsByFrameworkChart" width="400" height="300"></canvas>
          </div>
        </div>
      </div>

      <!-- Charts Row 2 -->
      <div class="global-dashboard-charts-grid">
        <!-- Events by Status -->
        <div class="global-dashboard-chart-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">
              Events by Status
            </h3>
            <button class="global-dashboard-chart-icon" style="color: #34D399;">
              <i class="fas fa-tasks"></i>
            </button>
          </div>
          <div class="global-dashboard-chart-container">
            <canvas ref="eventsByStatusChart" width="400" height="300"></canvas>
          </div>
        </div>

        <!-- Events by Priority -->
        <div class="global-dashboard-chart-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">
              Events by Priority
            </h3>
            <button class="global-dashboard-chart-icon" style="color: #F87171;">
              <i class="fas fa-exclamation-circle"></i>
            </button>
          </div>
          <div class="global-dashboard-chart-container">
            <canvas ref="eventsByPriorityChart" width="400" height="300"></canvas>
          </div>
        </div>
      </div>

      <!-- Trend Charts Row -->
      <div class="global-dashboard-charts-grid">
        <!-- Event Trend Over Time -->
        <div class="global-dashboard-chart-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">
              Event Trend Over Time
            </h3>
            <button class="global-dashboard-chart-icon" style="color: #60A5FA;">
              <i class="fas fa-chart-line"></i>
            </button>
          </div>
          <div class="global-dashboard-chart-container">
            <canvas ref="trendOverTimeChart" width="400" height="300"></canvas>
          </div>
        </div>

        <!-- Completion Rate Trend -->
        <div class="global-dashboard-chart-card">
          <div class="global-dashboard-chart-header">
            <h3 class="global-dashboard-chart-title">
              Completion Rate Trend
            </h3>
            <button class="global-dashboard-chart-icon" style="color: #34D399;">
              <i class="fas fa-percentage"></i>
            </button>
          </div>
          <div class="global-dashboard-chart-container">
            <canvas ref="completionRateChart" width="400" height="300"></canvas>
          </div>
        </div>
      </div>

      <!-- Recent Events -->
      <div class="events-dashboard-recent-events">
        <div class="events-dashboard-recent-events-header">
          <h3 class="events-dashboard-recent-events-title">
            <i class="fas fa-history events-dashboard-chart-title-icon"></i>
            Recent Events
          </h3>
          <span class="events-dashboard-recent-events-subtitle">Last 3 events</span>
        </div>
        <div v-if="dashboardData.recent_events.length > 0" class="events-dashboard-recent-events-list">
          <div v-for="event in dashboardData.recent_events" :key="event.id" class="events-dashboard-recent-event-item">
            <p class="events-dashboard-recent-event-title">{{ event.title }}</p>
            <p class="events-dashboard-recent-event-meta">{{ event.event_id }} • {{ event.category }}</p>
            <div class="events-dashboard-recent-event-footer">
              <span class="events-dashboard-recent-event-date">{{ event.created_at }}</span>
              <div class="events-dashboard-recent-event-status">
                <span :class="`events-dashboard-status-dot ${getStatusColorClass(event.status)}`"></span>
                <span :class="`events-dashboard-status-text ${getStatusColorClass(event.status)}`">
                  {{ event.status }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="events-dashboard-recent-events-empty">
          <div class="events-dashboard-recent-events-empty-icon">
            <svg class="events-dashboard-recent-events-empty-svg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
            </svg>
          </div>
          <p class="events-dashboard-recent-events-empty-title">No recent events found</p>
          <p class="events-dashboard-recent-events-empty-subtitle">Events from the last 7 days will appear here</p>
        </div>
      </div>
    </div>

    <!-- Popup Modal -->
    <PopupModal />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, onActivated, onDeactivated, nextTick, computed, watch } from 'vue'
import { eventService } from '../../services/api'
import EventFilters from './EventFilters.vue'
import { Chart, registerables } from 'chart.js'
import PopupModal from '../../modules/popus/PopupModal.vue'
import AccessUtils from '../../utils/accessUtils'
import apiService from '@/services/apiService.js'
import eventDataService from '../../services/eventService' // NEW: Centralized event data service
import { convertColorForColorblind, getColorblindMode } from '../../utils/colorblindness'
import { useDashboardsStore } from '@/stores/dashboards'

const sanitizeCSVCell = (value) => {
  const text = String(value ?? '')
  return /^\s*[=+\-@]/.test(text) ? `'${text}` : text
}

// Ensure Chart.js is properly loaded
if (typeof Chart === 'undefined') {
  console.error('Chart.js is not loaded properly')
}

export default {
  name: 'EventsDashboard',
  components: {
    EventFilters,
    PopupModal
  },
  setup() {
    const dashboardsStore = useDashboardsStore()
    const dashboardData = ref(null)
    const loading = ref(false)
    const error = ref(null)
    
    // Filter state
    const currentFilters = ref({
      framework: '',
      module: '',
      category: '',
      owner: ''
    })
    
    // Framework selection from session
    const selectedFrameworkFromSession = ref(null)
    
    // Colorblindness mode tracking
    const colorblindMode = ref(null)
    let colorblindObserver = null
    
    // Initialize colorblindness tracking
    const initColorblindnessTracking = () => {
      colorblindMode.value = getColorblindMode()
      
      colorblindObserver = new MutationObserver(() => {
        const newMode = getColorblindMode()
        if (newMode !== colorblindMode.value) {
          colorblindMode.value = newMode
          // Recreate charts when colorblindness mode changes
          if (dashboardData.value) {
            setTimeout(() => {
              createCharts()
            }, 100)
          }
        }
      })
      
      colorblindObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-colorblind']
      })
    }
    
    // Dark theme detection
    const isDarkTheme = computed(() => {
      if (typeof document !== 'undefined') {
        return document.documentElement.getAttribute('data-theme') === 'dark' || 
               document.body.getAttribute('data-theme') === 'dark'
      }
      return false
    })
    
    // Chart colors based on theme
    const getChartColors = () => {
      const dark = isDarkTheme.value
      return {
        textColor: dark ? '#f9fafb' : '#374151',
        gridColor: dark ? 'rgba(75, 85, 99, 0.3)' : 'rgba(0, 0, 0, 0.05)',
        borderColor: dark ? '#4b5563' : '#e5e7eb',
        tooltipBg: dark ? 'rgba(31, 41, 55, 0.95)' : 'rgba(255, 255, 255, 0.9)',
        tooltipText: dark ? '#f9fafb' : '#374151',
        axisColor: dark ? '#9ca3af' : '#6b7280'
      }
    }
    
    // Chart refs
    const eventsByCategoryChart = ref(null)
    const eventsByFrameworkChart = ref(null)
    const eventsByStatusChart = ref(null)
    const eventsByPriorityChart = ref(null)
    const trendOverTimeChart = ref(null)
    const completionRateChart = ref(null)
    
    // Chart instances
    let eventsByCategoryChartInstance = null
    let eventsByFrameworkChartInstance = null
    let eventsByStatusChartInstance = null
    let eventsByPriorityChartInstance = null
    let trendOverTimeChartInstance = null
    let completionRateChartInstance = null

    // Export controls (UI uses main.css classes)
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
    const exportDropdownClickOutside = (e) => {
      if (exportSelectRef.value && !exportSelectRef.value.contains(e.target)) {
        isExportDropdownOpen.value = false
      }
    }
    const handleExportClick = () => {
      if (!exportFormat.value) return
      handleExport(exportFormat.value)
    }

    // Export helpers (same pattern as EventsList)
    const exportToCSV = (data, filename) => {
      if (!data || data.length === 0) return
      const headers = Object.keys(data[0])
      const csvContent = [
        headers.join(','),
        ...data.map(row =>
          headers.map(header => {
            const safeValue = sanitizeCSVCell(row[header])
            return `"${String(safeValue).replace(/"/g, '""')}"`
          }).join(',')
        )
      ].join('\n')
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${filename}.csv`
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(link.href)
    }
    const exportToExcel = async (data, filename) => {
      if (!data || data.length === 0) return
      const headers = Object.keys(data[0])
      const csvContent = [
        headers.join(','),
        ...data.map(row =>
          headers.map(header => {
            const safeValue = sanitizeCSVCell(row[header])
            const escaped = String(safeValue).replace(/"/g, '""')
            return (escaped.includes(',') || escaped.includes('"') || escaped.includes('\n')) ? `"${escaped}"` : escaped
          }).join(',')
        )
      ].join('\n')
      const BOM = '\uFEFF'
      const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${filename}.csv`
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(link.href)
    }
    const exportToPDF = async (data, filename) => {
      if (!data || data.length === 0) return
      const headers = Object.keys(data[0])
      const htmlContent = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Events Dashboard Export</title>
        <style>body{font-family:Segoe UI,Tahoma,sans-serif;margin:0;padding:20px;font-size:11px;}
        table{border-collapse:collapse;width:100%;}th,td{border:1px solid #ddd;padding:8px;}
        th{background:#2563eb;color:#fff;}</style></head><body>
        <h1>Events Dashboard Export</h1><p>Generated: ${new Date().toLocaleString()} | Total: ${data.length}</p>
        <table><thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>
        ${data.map(row => `<tr>${headers.map(h => `<td>${String(row[h] ?? '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</td>`).join('')}</tr>`).join('')}
        </tbody></table></body></html>`
      const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `${filename}_Report.html`
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(link.href)
    }

    const handleExport = async (format) => {
      if (!format) return
      try {
        isExporting.value = true
        const response = await eventService.getEventsList()
        const events = (response.data && response.data.success && response.data.events) ? response.data.events : []
        if (events.length === 0) {
          console.warn('No events to export')
          isExporting.value = false
          return
        }
        const exportData = events.map(event => ({
          'Event ID': event.id || event.event_id || 'N/A',
          'Event Title': event.title || 'N/A',
          'Framework': event.framework || 'N/A',
          'Module': event.module || 'N/A',
          'Category': event.category || 'General',
          'Owner': event.owner || 'Not Assigned',
          'Reviewer': event.reviewer || 'Not Assigned',
          'Status': event.status || 'Pending Review',
          'Priority': event.priority || 'Medium',
          'Created Date': event.createdDate || event.created_at || 'N/A',
          'Updated Date': event.updatedDate || event.updated_at || 'N/A',
          'Description': event.description || 'No description'
        }))
        const baseName = `Events_Dashboard_Export_${new Date().toISOString().split('T')[0]}`
        switch (format.toLowerCase()) {
          case 'csv':
            exportToCSV(exportData, baseName)
            break
          case 'xlsx':
            await exportToExcel(exportData, baseName)
            break
          case 'pdf':
            await exportToPDF(exportData, baseName)
            break
          default:
            console.warn('Unsupported format:', format)
        }
      } catch (err) {
        console.error('Export error:', err)
      } finally {
        isExporting.value = false
      }
    }

    const handleFilterChange = (filterData) => {
      console.log('Filter changed:', filterData)
      currentFilters.value = { ...filterData }
      // Refresh dashboard data with new filters
      fetchDashboardData()
    }

    const getStatusColorClass = (status) => {
      switch (status) {
        case 'Approved': return 'events-dashboard-status-approved'
        case 'Pending Review': return 'events-dashboard-status-pending-review'
        case 'Rejected': return 'events-dashboard-status-rejected'
        case 'Draft': return 'events-dashboard-status-draft'
        case 'Under Review': return 'events-dashboard-status-under-review'
        case 'Completed': return 'events-dashboard-status-completed'
        case 'Cancelled': return 'events-dashboard-status-cancelled'
        default: return 'events-dashboard-status-default'
      }
    }

    // Check for selected framework from session (similar to other modules)
    const checkSelectedFrameworkFromSession = async () => {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in EventsDashboard...')
        const response = await apiService.get('/api/frameworks/get-selected/')
        
        console.log('🔍 DEBUG: Framework response in EventsDashboard:', response)
        
        if (response && response.frameworkId) {
          const frameworkIdFromSession = response.frameworkId.toString()
          console.log('✅ DEBUG: Found selected framework in session for EventsDashboard:', frameworkIdFromSession)
          
          // Set the selected framework from session
          selectedFrameworkFromSession.value = frameworkIdFromSession
          console.log('📊 DEBUG: Events are now filtered by framework:', frameworkIdFromSession)
          console.log('📊 DEBUG: selectedFrameworkFromSession.value set to:', selectedFrameworkFromSession.value)
        } else {
          console.log('ℹ️ DEBUG: No framework filter active - showing all events')
          selectedFrameworkFromSession.value = null
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework in EventsDashboard:', error)
        selectedFrameworkFromSession.value = null
      }
    }

    const fetchDashboardData = async (options = {}) => {
      const silent = !!options.silent
      try {
        if (!silent) loading.value = true
        error.value = null
        
        console.log('[EventsDashboard] Checking for cached event data...')
        
        // ==========================================
        // NEW: Check if data is already cached from HomeView prefetch
        // ==========================================
        // Note: Dashboard still needs to fetch dashboard-specific analytics from API
        // But we can check if basic event data is available for initial state
        if (eventDataService.hasValidCache()) {
          console.log('[EventsDashboard] ✅ Event cache available from HomeView prefetch')
          const cachedEvents = eventDataService.getData('events') || []
          console.log('[EventsDashboard] Cached events count:', cachedEvents.length)
        } else if (window.eventDataFetchPromise) {
          console.log('[EventsDashboard] ⏳ Waiting for ongoing prefetch to complete...')
          await window.eventDataFetchPromise
          const cachedEvents = eventDataService.getData('events') || []
          console.log('[EventsDashboard] Cached events count:', cachedEvents.length)
        }
        
        // Dashboard needs specific analytics data, so we still fetch from dashboard API
        // Build query parameters from current filters
        const params = new URLSearchParams()
        if (currentFilters.value.framework) {
          params.append('framework', currentFilters.value.framework)
        }
        if (currentFilters.value.module) {
          params.append('module', currentFilters.value.module)
        }
        if (currentFilters.value.category) {
          params.append('category', currentFilters.value.category)
        }
        if (currentFilters.value.owner) {
          params.append('owner', currentFilters.value.owner)
        }
        
        const queryString = params.toString()
        const url = queryString ? `/api/events/dashboard/?${queryString}` : '/api/events/dashboard/'
        
        console.log('[EventsDashboard] Fetching dashboard analytics with filters:', currentFilters.value)
        console.log('Request URL:', url)
        
        const response = await eventService.getEventsDashboard(queryString)
        if (response.data.success) {
          dashboardData.value = response.data
          dashboardsStore.set('event', response.data)
          // Create charts after data is loaded
          await nextTick()
          // Add a small delay to ensure DOM is fully rendered
          setTimeout(() => {
            createCharts()
          }, 100)
        } else {
          console.error('Dashboard API returned error:', response.data)
          error.value = response.data.message || 'Failed to fetch dashboard data'
        }
      } catch (err) {
        console.error('Error fetching dashboard data:', err)
        
        // Check if it's an access denied error (403)
        if (err.response && err.response.status === 403) {
          AccessUtils.showAccessDenied('Event Management - Dashboard', 'You don\'t have permission to view the events dashboard. Required permission: event.view_all_event or event.view_module_event')
        } else {
          error.value = 'Failed to fetch dashboard data. Please try again.'
        }
      } finally {
        if (!silent) loading.value = false
      }
    }

    const createCharts = async () => {
      await nextTick()
      
      console.log('Creating charts with data:', dashboardData.value)
      console.log('Chart.js available:', typeof Chart !== 'undefined')
      
      // Register Chart.js components
      Chart.register(...registerables)
      
      createEventsByCategoryChart()
      createEventsByFrameworkChart()
      createEventsByStatusChart()
      createEventsByPriorityChart()
      createTrendOverTimeChart()
      createCompletionRateChart()
    }

    const createEventsByCategoryChart = () => {
      console.log('Creating Events by Category chart, canvas ref:', eventsByCategoryChart.value)
      if (!eventsByCategoryChart.value) {
        console.log('Events by Category chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (eventsByCategoryChartInstance) {
        eventsByCategoryChartInstance.destroy()
      }
      
      try {
        const ctx = eventsByCategoryChart.value.getContext('2d')
        console.log('Canvas context:', ctx)
        
        // Use real data from backend
        const categoryData = dashboardData.value?.charts?.events_by_category || []
        console.log('Category data from backend:', categoryData)
        
        // Prepare data for the chart
        const labels = categoryData.map(item => item.Category || 'Uncategorized')
        const data = categoryData.map(item => item.count || 0)
        
        // Balanced color palette for different categories - with colorblindness support
        const baseColors = ['#60A5FA', '#F87171', '#A78BFA', '#34D399', '#FBBF24', '#F472B6', '#A3E635', '#FB923C']
        const colors = baseColors.slice(0, labels.length).map(color => convertColorForColorblind(color))
        
        eventsByCategoryChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Events',
            data: data,
            backgroundColor: colors,
            borderRadius: 4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: getChartColors().tooltipBg,
              titleColor: getChartColors().tooltipText,
              bodyColor: getChartColors().tooltipText,
              borderColor: getChartColors().borderColor,
              borderWidth: 1,
              callbacks: {
                label: function(context) {
                  return `${context.label}: ${context.raw} events`
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              },
              ticks: {
                color: getChartColors().textColor
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Number of Events',
                color: getChartColors().textColor
              },
              ticks: {
                color: getChartColors().textColor
              },
              grid: {
                color: getChartColors().gridColor
              }
            }
          }
        }
      })
      console.log('Events by Category chart created successfully')
      } catch (error) {
        console.error('Error creating Events by Category chart:', error)
      }
    }

    const createEventsByFrameworkChart = () => {
      console.log('Creating Events by Framework chart, canvas ref:', eventsByFrameworkChart.value)
      if (!eventsByFrameworkChart.value) {
        console.log('Events by Framework chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (eventsByFrameworkChartInstance) {
        eventsByFrameworkChartInstance.destroy()
      }
      
      try {
        const ctx = eventsByFrameworkChart.value.getContext('2d')
        
        // Use real data from backend
        const frameworkData = dashboardData.value?.charts?.events_by_framework || []
        console.log('Framework data from backend:', frameworkData)
        
        // Prepare data for the chart
        const labels = frameworkData.map(item => item.FrameworkName || 'Unknown Framework')
        const data = frameworkData.map(item => item.count || 0)
        
        // Balanced color palette for different frameworks - with colorblindness support
        const baseColors = ['#60A5FA', '#F87171', '#FBBF24', '#34D399', '#A78BFA', '#F472B6', '#A3E635', '#FB923C']
        const colors = baseColors.slice(0, labels.length).map(color => convertColorForColorblind(color))
        
        eventsByFrameworkChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: data,
            backgroundColor: colors,
            borderWidth: 0,
            borderRadius: 3
          }]
        },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  usePointStyle: true,
                  padding: 20,
                  color: getChartColors().textColor,
                  generateLabels: function(chart) {
                    const data = chart.data
                    if (data.labels.length && data.datasets.length) {
                      return data.labels.map((label, i) => {
                        const value = data.datasets[0].data[i]
                        return {
                          text: `${label}: ${value} events`,
                          fillStyle: data.datasets[0].backgroundColor[i],
                          strokeStyle: data.datasets[0].backgroundColor[i],
                          lineWidth: 0,
                          pointStyle: 'circle',
                          hidden: false,
                          index: i,
                          fontColor: getChartColors().textColor
                        }
                      })
                    }
                    return []
                  }
                }
              },
              tooltip: {
                backgroundColor: getChartColors().tooltipBg,
                titleColor: getChartColors().tooltipText,
                bodyColor: getChartColors().tooltipText,
                borderColor: getChartColors().borderColor,
                borderWidth: 1,
                callbacks: {
                  label: function(context) {
                    return `${context.label}: ${context.raw} events`
                  }
                }
              }
            }
          }
      })
      } catch (error) {
        console.error('Error creating Events by Framework chart:', error)
      }
    }

    const createTrendOverTimeChart = () => {
      console.log('Creating Trend Over Time chart, canvas ref:', trendOverTimeChart.value)
      if (!trendOverTimeChart.value) {
        console.log('Trend Over Time chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (trendOverTimeChartInstance) {
        trendOverTimeChartInstance.destroy()
      }
      
      try {
        const ctx = trendOverTimeChart.value.getContext('2d')
        
        // Use real monthly trend data from backend
        const monthlyTrends = dashboardData.value?.charts?.monthly_trends || []
        console.log('Monthly trends data from backend:', monthlyTrends)
        
        let months, trendData, currentMonthIndex
        
        if (monthlyTrends.length > 0) {
          // Extract months and counts from backend data
          months = monthlyTrends.map(trend => trend.month)
          trendData = monthlyTrends.map(trend => trend.count)
          
          // Find current month index for highlighting
          const currentMonthName = new Date().toLocaleDateString('en-US', { month: 'short' })
          currentMonthIndex = months.indexOf(currentMonthName)
        } else {
          // Fallback to default months if no data
          months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
          trendData = [0, 0, 0, 0, 0, 0]
          currentMonthIndex = -1
        }
        
        console.log('Months:', months)
        console.log('Trend data:', trendData)
        console.log('Current month index:', currentMonthIndex)
        
        trendOverTimeChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: months,
          datasets: [{
            label: 'Events',
            data: trendData,
            borderColor: convertColorForColorblind('#60A5FA'),
            backgroundColor: convertColorForColorblind('rgba(96, 165, 250, 0.1)'),
            borderWidth: 3,
            tension: 0.4,
            fill: true,
            pointRadius: months.map((_, idx) => idx === currentMonthIndex ? 6 : 4),
            pointHoverRadius: 8,
            pointBackgroundColor: months.map(() => convertColorForColorblind('#60A5FA')),
            pointBorderColor: isDarkTheme.value ? '#1f2937' : '#ffffff',
            pointBorderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              mode: 'index',
              intersect: false,
              backgroundColor: getChartColors().tooltipBg,
              titleColor: getChartColors().tooltipText,
              bodyColor: getChartColors().tooltipText,
              borderColor: getChartColors().borderColor,
              borderWidth: 1,
              callbacks: {
                title: (context) => {
                  return context[0].label
                },
                label: (context) => {
                  const isCurrentMonth = context.dataIndex === currentMonthIndex
                  const monthLabel = isCurrentMonth ? ' (Current Month)' : ''
                  return `Events: ${context.raw}${monthLabel}`
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              },
              ticks: {
                color: getChartColors().textColor
              }
            },
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Number of Events',
                color: getChartColors().textColor
              },
              ticks: {
                color: getChartColors().textColor
              },
              grid: {
                color: getChartColors().gridColor
              }
            }
          }
        }
      })
      } catch (error) {
        console.error('Error creating Trend Over Time chart:', error)
      }
    }

    const createEventsByStatusChart = () => {
      console.log('Creating Events by Status chart, canvas ref:', eventsByStatusChart.value)
      if (!eventsByStatusChart.value) {
        console.log('Events by Status chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (eventsByStatusChartInstance) {
        eventsByStatusChartInstance.destroy()
      }
      
      try {
        const ctx = eventsByStatusChart.value.getContext('2d')
        
        // Use real data from backend
        const statusData = dashboardData.value?.charts?.events_by_status || []
        console.log('Status data from backend:', statusData)
        
        // Prepare data for the chart
        const labels = statusData.map(item => item.Status || 'Unknown')
        const data = statusData.map(item => item.count || 0)
        
        // Balanced color palette for different statuses - with colorblindness support
        const statusColors = {
          'Completed': '#34D399',
          'Approved': '#34D399',
          'Pending Review': '#FBBF24',
          'Under Review': '#60A5FA',
          'Draft': '#9CA3AF',
          'Rejected': '#F87171',
          'Cancelled': '#9CA3AF'
        }
        
        const colors = labels.map(status => {
          const baseColor = statusColors[status] || '#F1F5F9'
          return convertColorForColorblind(baseColor)
        })
        
        eventsByStatusChartInstance = new Chart(ctx, {
          type: 'pie',
          data: {
            labels: labels,
            datasets: [{
              data: data,
              backgroundColor: colors,
              borderWidth: 2,
              borderColor: isDarkTheme.value ? '#1f2937' : '#ffffff'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  usePointStyle: true,
                  padding: 15,
                  color: getChartColors().textColor
                }
              },
              tooltip: {
                backgroundColor: getChartColors().tooltipBg,
                titleColor: getChartColors().tooltipText,
                bodyColor: getChartColors().tooltipText,
                borderColor: getChartColors().borderColor,
                borderWidth: 1,
                callbacks: {
                  label: function(context) {
                    return `${context.label}: ${context.raw} events`
                  }
                }
              }
            }
          }
        })
      } catch (error) {
        console.error('Error creating Events by Status chart:', error)
      }
    }

    const createEventsByPriorityChart = () => {
      console.log('Creating Events by Priority chart, canvas ref:', eventsByPriorityChart.value)
      if (!eventsByPriorityChart.value) {
        console.log('Events by Priority chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (eventsByPriorityChartInstance) {
        eventsByPriorityChartInstance.destroy()
      }
      
      try {
        const ctx = eventsByPriorityChart.value.getContext('2d')
        
        // Use real data from backend
        const priorityData = dashboardData.value?.charts?.events_by_priority || []
        console.log('Priority data from backend:', priorityData)
        
        // Prepare data for the chart
        const labels = priorityData.map(item => item.Priority || 'Unknown')
        const data = priorityData.map(item => item.count || 0)
        
        // Balanced color palette for different priorities - with colorblindness support
        const priorityColors = {
          'Critical': '#F87171',
          'High': '#FB923C',
          'Medium': '#FBBF24',
          'Low': '#34D399'
        }
        
        const colors = labels.map(priority => {
          const baseColor = priorityColors[priority] || '#F1F5F9'
          return convertColorForColorblind(baseColor)
        })
        
        eventsByPriorityChartInstance = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'Events',
              data: data,
              backgroundColor: colors,
              borderRadius: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                backgroundColor: getChartColors().tooltipBg,
                titleColor: getChartColors().tooltipText,
                bodyColor: getChartColors().tooltipText,
                borderColor: getChartColors().borderColor,
                borderWidth: 1,
                callbacks: {
                  label: function(context) {
                    return `${context.label}: ${context.raw} events`
                  }
                }
              }
            },
            scales: {
              x: {
                grid: {
                  display: false
                },
                ticks: {
                  color: getChartColors().textColor
                }
              },
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'Number of Events',
                  color: getChartColors().textColor
                },
                ticks: {
                  color: getChartColors().textColor
                },
                grid: {
                  color: getChartColors().gridColor
                }
              }
            }
          }
        })
      } catch (error) {
        console.error('Error creating Events by Priority chart:', error)
      }
    }


    const createCompletionRateChart = () => {
      console.log('Creating Completion Rate chart, canvas ref:', completionRateChart.value)
      if (!completionRateChart.value) {
        console.log('Completion Rate chart canvas not found')
        return
      }
      
      // Destroy existing chart
      if (completionRateChartInstance) {
        completionRateChartInstance.destroy()
      }
      
      try {
        const ctx = completionRateChart.value.getContext('2d')
        
        // Use real data from backend
        const completionData = dashboardData.value?.charts?.completion_trends || []
        console.log('Completion data from backend:', completionData)
        
        let months, completionRates, totalEvents, completedEvents
        
        if (completionData.length > 0) {
          // Extract months and completion rates from backend data
          months = completionData.map(trend => trend.month)
          completionRates = completionData.map(trend => trend.completion_rate)
          totalEvents = completionData.map(trend => trend.total_events)
          completedEvents = completionData.map(trend => trend.completed_events)
        } else {
          // Fallback to default months if no data
          months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
          completionRates = [0, 0, 0, 0, 0, 0]
          totalEvents = [0, 0, 0, 0, 0, 0]
          completedEvents = [0, 0, 0, 0, 0, 0]
        }
        
        console.log('Months:', months)
        console.log('Completion rates:', completionRates)
        
        completionRateChartInstance = new Chart(ctx, {
          type: 'line',
          data: {
            labels: months,
            datasets: [{
              label: 'Completion Rate (%)',
              data: completionRates,
            borderColor: convertColorForColorblind('#34D399'),
            backgroundColor: convertColorForColorblind('rgba(52, 211, 153, 0.1)'),
              borderWidth: 3,
              tension: 0.4,
              fill: true,
              pointRadius: 5,
              pointHoverRadius: 8,
              pointBackgroundColor: convertColorForColorblind('#34D399'),
              pointBorderColor: isDarkTheme.value ? '#1f2937' : '#ffffff',
              pointBorderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: getChartColors().tooltipBg,
                titleColor: getChartColors().tooltipText,
                bodyColor: getChartColors().tooltipText,
                borderColor: getChartColors().borderColor,
                borderWidth: 1,
                callbacks: {
                  title: (context) => {
                    return context[0].label
                  },
                  label: (context) => {
                    const index = context.dataIndex
                    return [
                      `Completion Rate: ${context.raw}%`,
                      `Total Events: ${totalEvents[index]}`,
                      `Completed Events: ${completedEvents[index]}`
                    ]
                  }
                }
              }
            },
            scales: {
              x: {
                grid: {
                  display: false
                },
                ticks: {
                  color: getChartColors().textColor
                }
              },
              y: {
                beginAtZero: true,
                max: 100,
                title: {
                  display: true,
                  text: 'Completion Rate (%)',
                  color: getChartColors().textColor
                },
                ticks: {
                  color: getChartColors().textColor,
                  callback: function(value) {
                    return value + '%'
                  }
                },
                grid: {
                  color: getChartColors().gridColor
                }
              }
            }
          }
        })
      } catch (error) {
        console.error('Error creating Completion Rate chart:', error)
      }
    }

    // Watch for theme changes and re-render charts
    watch(isDarkTheme, () => {
      if (dashboardData.value) {
        setTimeout(() => {
          createCharts()
        }, 100)
      }
    })

    onMounted(async () => {
      // Initialize colorblindness tracking
      initColorblindnessTracking()
      
      // Check for framework selection from session
      await checkSelectedFrameworkFromSession()

      // Cache-first instant render
      const cached = dashboardsStore.get('event')
      if (cached) {
        dashboardData.value = cached
        loading.value = false
        await nextTick()
        setTimeout(() => createCharts(), 0)

        if (!dashboardsStore.isFresh('event')) {
          // Silent revalidation for stale cache.
          fetchDashboardData({ silent: true })
        }
      } else {
        // No cache available yet: fetch normally once.
        await fetchDashboardData()
      }
      
      document.addEventListener('click', exportDropdownClickOutside)
    })

    onActivated(async () => {
      if (dashboardData.value) {
        await nextTick()
        setTimeout(() => createCharts(), 0)
        fetchDashboardData({ silent: true }).catch(() => {})
        return
      }
      await fetchDashboardData()
    })

    onDeactivated(() => {
      // No-op: preserve rendered data; refresh is resumed on activate.
    })

    onUnmounted(() => {
      document.removeEventListener('click', exportDropdownClickOutside)
      // Clean up colorblindness observer
      if (colorblindObserver) {
        colorblindObserver.disconnect()
      }
      
      // Clean up chart instances
      if (eventsByCategoryChartInstance) {
        eventsByCategoryChartInstance.destroy()
      }
      if (eventsByFrameworkChartInstance) {
        eventsByFrameworkChartInstance.destroy()
      }
      if (eventsByStatusChartInstance) {
        eventsByStatusChartInstance.destroy()
      }
      if (eventsByPriorityChartInstance) {
        eventsByPriorityChartInstance.destroy()
      }
      if (trendOverTimeChartInstance) {
        trendOverTimeChartInstance.destroy()
      }
      if (completionRateChartInstance) {
        completionRateChartInstance.destroy()
      }
    })

    return {
      dashboardData,
      loading,
      error,
      selectedFrameworkFromSession,
      handleExport,
      handleFilterChange,
      getStatusColorClass,
      fetchDashboardData,
      eventsByCategoryChart,
      eventsByFrameworkChart,
      eventsByStatusChart,
      eventsByPriorityChart,
      trendOverTimeChart,
      completionRateChart,
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

<style>
@import '@/assets/css/main.css';
@import '@/assets/css/DashboardCards.css';

/* Events Dashboard Container */
.events-dashboard-container {
  padding: 24px;
  padding-top: 40px;
  background: white;
  min-height: 100vh;
  margin-left: -30px;
}

/* Events Dashboard Header: title + export controls (export-controls use main.css) */
.events-dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 32px;
}

.events-dashboard-title {
  font-size: 1.7rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 8px 0;
  line-height: 1.2;
}

.events-dashboard-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

.events-dashboard-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.events-dashboard-export-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.events-dashboard-export-btn:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

.events-dashboard-export-icon {
  width: 16px;
  height: 16px;
}

.events-dashboard-export-text {
  font-weight: 600;
}

/* Filters Section */
.events-dashboard-filters {
  margin-bottom: 32px;
}

/* Loading State */
.events-dashboard-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

.events-dashboard-loading-content {
  text-align: center;
}

.events-dashboard-loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: events-dashboard-spin 1s linear infinite;
  margin: 0 auto 16px;
}

.events-dashboard-loading-text {
  font-size: 1rem;
  color: #6b7280;
  margin: 0;
}

/* Error State */
.events-dashboard-error {
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.events-dashboard-error-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.events-dashboard-error-icon {
  flex-shrink: 0;
}

.events-dashboard-error-svg {
  width: 24px;
  height: 24px;
  color: #ef4444;
}

.events-dashboard-error-details {
  flex: 1;
}

.events-dashboard-error-title {
  font-size: 1rem;
  font-weight: 600;
  color: #dc2626;
  margin: 0 0 8px 0;
}

.events-dashboard-error-message {
  font-size: 0.9rem;
  color: #991b1b;
  margin: 0 0 16px 0;
}

.events-dashboard-error-retry {
  padding: 12px 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}

.events-dashboard-error-retry:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
}

/* Dashboard Content */
.events-dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* KPI grid – ensure 4 cards in a single row on Events dashboard */
.events-dashboard-container .kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
  gap: 16px;
  margin: 12px 0 24px;
}

@media (max-width: 768px) {
  .events-dashboard-container .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  }
}

@media (max-width: 480px) {
  .events-dashboard-container .kpi-grid {
    grid-template-columns: 1fr !important;
  }
}

/* Charts Grid - Using global dashboard charts grid from DashboardCards.css */
/* Chart containers now use global-dashboard-chart-card, global-dashboard-chart-header, etc. */

/* Recent Events */

.events-dashboard-recent-events-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f3f4f6;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.events-dashboard-recent-events-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

.events-dashboard-recent-events-subtitle {
  font-size: 0.85rem;
  color: #6b7280;
  font-weight: 500;
}

.events-dashboard-recent-events-list {
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.events-dashboard-recent-event-item {
  padding: 16px 0;
  border-bottom: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.events-dashboard-recent-event-item:last-child {
  border-bottom: none;
}

.events-dashboard-recent-event-item:hover {
  background: rgba(248, 249, 250, 0.5);
  padding-left: 8px;
  border-radius: 8px;
}

.events-dashboard-recent-event-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  line-height: 1.4;
}

.events-dashboard-recent-event-meta {
  font-size: 0.8rem;
  color: #6b7280;
  margin: 0;
  font-weight: 500;
}

.events-dashboard-recent-event-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.events-dashboard-recent-event-date {
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: 500;
}

.events-dashboard-recent-event-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.events-dashboard-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.events-dashboard-status-text {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Status dot colors - solid dots */
.events-dashboard-status-dot.events-dashboard-status-approved {
  background-color: #10b981;
}

.events-dashboard-status-dot.events-dashboard-status-pending-review {
  background-color: #f59e0b;
}

.events-dashboard-status-dot.events-dashboard-status-rejected {
  background-color: #ef4444;
}

.events-dashboard-status-dot.events-dashboard-status-draft {
  background-color: #6b7280;
}

.events-dashboard-status-dot.events-dashboard-status-under-review {
  background-color: #3b82f6;
}

.events-dashboard-status-dot.events-dashboard-status-completed {
  background-color: #10b981;
}

.events-dashboard-status-dot.events-dashboard-status-cancelled {
  background-color: #6b7280;
}

.events-dashboard-status-dot.events-dashboard-status-default {
  background-color: #6b7280;
}

/* Status text colors - matching the dots */
.events-dashboard-status-text.events-dashboard-status-approved {
  color: #10b981;
}

.events-dashboard-status-text.events-dashboard-status-pending-review {
  color: #f59e0b;
}

.events-dashboard-status-text.events-dashboard-status-rejected {
  color: #ef4444;
}

.events-dashboard-status-text.events-dashboard-status-draft {
  color: #6b7280;
}

.events-dashboard-status-text.events-dashboard-status-under-review {
  color: #3b82f6;
}

.events-dashboard-status-text.events-dashboard-status-completed {
  color: #10b981;
}

.events-dashboard-status-text.events-dashboard-status-cancelled {
  color: #6b7280;
}

.events-dashboard-status-text.events-dashboard-status-default {
  color: #6b7280;
}

/* Empty State */
.events-dashboard-recent-events-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.events-dashboard-recent-events-empty-icon {
  margin-bottom: 16px;
}

.events-dashboard-recent-events-empty-svg {
  width: 48px;
  height: 48px;
  color: #9ca3af;
}

.events-dashboard-recent-events-empty-title {
  font-size: 1rem;
  color: #6b7280;
  margin: 0 0 8px 0;
  font-weight: 600;
}

.events-dashboard-recent-events-empty-subtitle {
  font-size: 0.85rem;
  color: #9ca3af;
  margin: 0;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .events-dashboard-kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .events-dashboard-container {
    margin-left: 0;
    padding: 16px;
  }
  
  .events-dashboard-title {
    font-size: 1.5rem;
  }
  
  .events-dashboard-kpi-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .events-dashboard-kpi-card {
    padding: 20px;
  }
  
  .events-dashboard-kpi-card-value {
    font-size: 2rem;
  }
  
  /* Charts grid responsive handled by global-dashboard-charts-grid */
  
  .events-dashboard-recent-events-header {
    padding: 16px 20px 12px;
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  
  .events-dashboard-recent-events-list {
    padding: 16px 20px 20px;
  }
  
  .events-dashboard-recent-event-footer {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
}

/* Animations */
@keyframes events-dashboard-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes events-dashboard-fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.events-dashboard-kpi-card,
.events-dashboard-recent-events {
  animation: events-dashboard-fadeIn 0.5s ease-out;
}

/* Focus states for accessibility */
.events-dashboard-export-btn:focus,
.events-dashboard-error-retry:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
</style>
