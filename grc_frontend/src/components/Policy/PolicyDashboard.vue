<template>
  <div class="dashboard-container policy-dashboard-container">
    <div v-if="error" class="error-message">
      {{ error }}
      <button @click="fetchDashboardData" class="retry-btn">Retry</button>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <span>Loading dashboard data...</span>
    </div>

    <div v-if="!loading && !error">
      <!-- Breadcrumb Section for Selected Filters - Positioned above dashboard-header -->
      <div v-if="(selectedFramework && selectedFramework !== 'all' && getSelectedFrameworkName !== '') || (selectedPolicy && selectedPolicy !== 'all' && getSelectedPolicyName !== '')" class="filter-breadcrumbs">
        <div v-if="selectedFramework && selectedFramework !== 'all' && getSelectedFrameworkName !== ''" class="filter-breadcrumbs__item">
          <span class="filter-breadcrumbs__label">Framework:</span>
          <span class="filter-breadcrumbs__value">{{ getSelectedFrameworkName }}</span>
          <button class="filter-breadcrumbs__close" @click="clearFrameworkSelection" title="Clear Framework">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div v-if="selectedPolicy && selectedPolicy !== 'all' && getSelectedPolicyName !== ''" class="filter-breadcrumbs__item">
          <span class="filter-breadcrumbs__label">Policy:</span>
          <span class="filter-breadcrumbs__value">{{ getSelectedPolicyName }}</span>
          <button class="filter-breadcrumbs__close" @click="clearPolicySelection" title="Clear Policy">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
      
      <div class="dashboard-header">
        <div class="dashboard-header-left">
          <button
            class="back-icon-btn"
            @click="goBackToPolicyManagement"
            aria-label="Back to Policy Management"
          >
            <i class="fas fa-arrow-left"></i>
          </button>
          <h1>Policy Dashboard</h1>
        </div>
        <div class="policy-header-actions">
          <!-- Export controls using global styles from main.css (custom dropdown + button) -->
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
                @click="handleExportClick"
                :disabled="!selectedExportFormat || isExporting"
                :class="{ 'exporting': isExporting, 'success': exportSuccess }"
                title="Export Dashboard"
              >
                <i v-if="!isExporting" class="fas fa-download"></i>
                {{ isExporting ? 'Exporting...' : 'Export' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    
    <!-- Filter Dropdowns -->
    <div class="filter-dropdowns">
      <div class="filter-dropdown">
        <label class="dropdown-external-label">Framework:</label>
        <CustomDropdown
          v-model="selectedFramework"
          :options="frameworkOptions"
          @change="handleFrameworkChange"
          :config="{ label: 'All Frameworks' }"
          :showLabel="false"
        />
      </div>
      
      <div class="filter-dropdown">
        <label class="dropdown-external-label">Policy:</label>
        <CustomDropdown
          v-model="selectedPolicy"
          :options="policyOptions"
          @change="onPolicyChange"
          :config="{ label: 'All Policies' }"
          :showLabel="false"
        />
      </div>
      
    </div>

    <!-- Summary KPI Cards (using global KPI styles from main.css) -->
    <div class="kpi-grid">
      <!-- Approval Rate -->
      <div class="kpi-card">
        <div class="kpi-card-icon kpi-icon-approved">
          <i class="fas fa-chart-pie"></i>
        </div>
        <div class="kpi-card-body">
          <p class="kpi-card-title">Approval Rate</p>
          <div class="kpi-card-value">
            <span v-if="!initialDataLoaded" class="skeleton-text">--</span>
            <span v-else>{{ dashboardData.approval_rate }}%</span>
          </div>
          <p class="kpi-card-subtitle">
            Based on {{ dashboardData.total_policies }} policies
          </p>
        </div>
      </div>

      <!-- Active Policies -->
      <div class="kpi-card">
        <div class="kpi-card-icon kpi-icon-open">
          <i class="fas fa-chart-bar"></i>
        </div>
        <div class="kpi-card-body">
          <p class="kpi-card-title">Active Policies</p>
          <div class="kpi-card-value">
            <span v-if="!initialDataLoaded" class="skeleton-text">--</span>
            <span v-else>{{ dashboardData.active_policies }}</span>
          </div>
          <p class="kpi-card-subtitle">
            {{ dashboardData.total_policies }} total policies
          </p>
        </div>
      </div>

      <!-- Active Subpolicies -->
      <div class="kpi-card">
        <div class="kpi-card-icon kpi-icon-total">
          <i class="fas fa-chart-line"></i>
        </div>
        <div class="kpi-card-body">
          <p class="kpi-card-title">Active Subpolicies</p>
          <div class="kpi-card-value">
            <span v-if="!initialDataLoaded" class="skeleton-text">--</span>
            <span v-else>{{ dashboardData.active_subpolicies }}</span>
          </div>
          <p class="kpi-card-subtitle">
            {{ dashboardData.total_subpolicies }} total subpolicies
          </p>
        </div>
      </div>

      <!-- Average Approval Time -->
      <div class="kpi-card">
        <div class="kpi-card-icon">
          <i class="fas fa-stopwatch"></i>
        </div>
        <div class="kpi-card-body">
          <p class="kpi-card-title">Avg. Approval Time</p>
          <div class="kpi-card-value">
            <span v-if="!initialDataLoaded" class="skeleton-text">--</span>
            <span v-else>{{ avgApprovalTime }} days</span>
          </div>
          <p class="kpi-card-subtitle">
            Time to approve
          </p>
        </div>
      </div>
    </div>

    <!-- Charts Grid -->
    <div class="global-dashboard-charts-grid">
      <!-- Active/Inactive Donut Chart -->
      <DashboardChartCard
        title="Active/Inactive Distribution"
        icon="fas fa-chart-pie"
        icon-color="#10B981"
        chart-type="doughnut"
        :chart-data="activeInactiveData"
        :chart-options="donutChartOptions"
        :loading="chartsLoading"
        :error="error"
      />

      <!-- Category Distribution Line Chart -->
      <DashboardChartCard
        title="Category Distribution"
        icon="fas fa-chart-line"
        icon-color="#3B82F6"
        chart-type="line"
        :chart-data="categoryData"
        :chart-options="lineChartOptions"
        :loading="chartsLoading"
        :error="error"
      />

      <!-- Status Distribution Bar Chart -->
      <DashboardChartCard
        title="Status Distribution"
        icon="fas fa-chart-bar"
        icon-color="#F59E0B"
        chart-type="bar"
        :chart-data="statusData"
        :chart-options="barChartOptions"
        :loading="chartsLoading"
        :error="error"
      />
      
      <!-- Department Distribution Bar Chart -->
      <DashboardChartCard
        title="Department Distribution"
        icon="fas fa-chart-bar"
        icon-color="#8B5CF6"
        chart-type="bar"
        :chart-data="departmentData"
        :chart-options="barChartOptions"
        :loading="chartsLoading"
        :error="error"
      />
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
    </div>
  </div>
</template>

<script>
import dashboardService from '@/services/dashboardService';
import { ref, reactive, watch, onMounted, onUnmounted, computed } from 'vue'
import { useStore } from 'vuex'
import { Chart, ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'
import DashboardChartCard from '@/assets/css/DashboardChartCard.vue'
import apiService from '@/services/apiService'
import { API_ENDPOINTS } from '../../config/api.js'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import CustomDropdown from '@/components/CustomDropdown.vue'
import '@/assets/css/dropdown.css'

import '@fortawesome/fontawesome-free/css/all.min.css'

Chart.register(ArcElement, BarElement, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

export default {
  name: 'PolicyDashboard',
  components: {
    CustomDropdown,
    DashboardChartCard
  },
  setup() {
    const store = useStore()
    const showPolicyDetails = ref(true)
    const selectedFramework = ref('all')
    const selectedPolicy = ref('all')
    const selectedTimeRange = ref('last_6_months')
    const selectedCategory = ref('all')
    const selectedPriority = ref('all')
    const frameworks = ref([])
    const policies = ref([])
    const categories = ref([])
    
    // Framework session filtering properties
    const sessionFrameworkId = ref(null)
    const dashboardData = ref({
      total_policies: 0,
      total_subpolicies: 0,
      active_policies: 0,
      inactive_policies: 0,
      active_subpolicies: 0,
      approval_rate: 0,
      policies: []
    })
    const recentActivity = ref([])
    const recentActivities = ref([])
    const loadingActivities = ref(false)
    const activityRefreshInterval = ref(null)
    const avgApprovalTime = ref(0)
    const statusDistribution = ref([])
    const reviewerWorkload = ref([])
    const loading = ref(true)
    const error = ref(null)
    const isExporting = ref(false)
    const exportSuccess = ref(false)
    const updateTimeout = ref(null)
    const chartsLoading = ref(false)
    const initialDataLoaded = ref(false)
    const chartDataCache = ref(new Map())

    // Export controls (shared button styles from main.css – same pattern as FrameworkExplorer)
    const selectedExportFormat = ref('')
    const isExportDropdownOpen = ref(false)
    const exportFormatOptions = [
      { value: '', label: 'Select format' },
      // Policy dashboard currently supports only PDF export
      { value: 'pdf', label: 'PDF (.pdf)' }
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

    // Framework filtering computed properties
    const filteredFrameworks = computed(() => {
      if (sessionFrameworkId.value) {
        // If there's a session framework ID, show only that framework
        return frameworks.value.filter(fw => fw.id.toString() === sessionFrameworkId.value.toString())
      }
      // If no session framework ID, show all frameworks
      return frameworks.value
    })
    
    // Dropdown options computed properties
    const frameworkOptions = computed(() => {
      return [
        { value: 'all', label: 'All Frameworks' },
        ...filteredFrameworks.value.map(fw => ({
          value: fw.id,
          label: fw.name
        }))
      ]
    })
    
    const policyOptions = computed(() => {
      return [
        { value: 'all', label: 'All Policies' },
        ...policies.value.map(p => ({
          value: p.id,
          label: p.name
        }))
      ]
    })
    
    // Get selected framework name for breadcrumb
    const getSelectedFrameworkName = computed(() => {
      if (!selectedFramework.value || selectedFramework.value === 'all') return '';
      const framework = frameworks.value.find(fw => fw.id.toString() === selectedFramework.value.toString());
      return framework ? framework.name : '';
    })
    
    // Get selected policy name for breadcrumb
    const getSelectedPolicyName = computed(() => {
      if (!selectedPolicy.value || selectedPolicy.value === 'all') return '';
      const policy = policies.value.find(p => p.id.toString() === selectedPolicy.value.toString());
      return policy ? policy.name : '';
    })
    
    // Clear framework selection
    const clearFrameworkSelection = () => {
      selectedFramework.value = 'all'
      handleFrameworkChange()
    }
    
    // Clear policy selection
    const clearPolicySelection = () => {
      selectedPolicy.value = 'all'
      onPolicyChange()
    }

    // Chart data objects
    const activeInactiveData = reactive({
      labels: ['Active', 'Inactive'],
      datasets: [{
        data: [0, 0],
        backgroundColor: ['#10B981', '#EF4444'],
        borderWidth: 0,
        hoverOffset: 5
      }]
    })

    const categoryData = reactive({
      labels: [],
      datasets: [{
        label: 'Category Distribution',
        data: [],
        fill: false,
        borderColor: '#4f6cff',
        backgroundColor: 'rgba(79, 108, 255, 0.1)',
        tension: 0.4,
        pointBackgroundColor: '#4f6cff',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    })

    const statusData = reactive({
      labels: [],
      datasets: [{
        label: 'Status Distribution',
        data: [],
        backgroundColor: ['#10B981', '#EF4444', '#3B82F6', '#F59E0B', '#8B5CF6'],
        borderColor: ['#10B981', '#EF4444', '#3B82F6', '#F59E0B', '#8B5CF6'],
        borderWidth: 1,
        borderRadius: 4
      }]
    })

    const departmentData = reactive({
      labels: [],
      datasets: [{
        label: 'Department Distribution',
        data: [],
        backgroundColor: ['#4f6cff', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'],
        borderColor: ['#4f6cff', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'],
        borderWidth: 1,
        borderRadius: 4
      }]
    })

    // Chart options
    const donutChartOptions = {
      cutout: '70%',
      plugins: {
        legend: { 
          display: true,
          position: 'bottom',
          labels: {
            padding: 20,
            usePointStyle: true,
            font: { size: 11 }
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const value = context.raw || 0;
              const total = context.dataset.data.reduce((acc, val) => acc + val, 0);
              const percentage = Math.round((value / total) * 100);
              return `${context.label}: ${value} (${percentage}%)`;
            }
          }
        }
      },
      maintainAspectRatio: false,
      animation: {
        animateRotate: true,
        animateScale: true,
        duration: 500,
        easing: 'easeOutQuart'
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

    const lineChartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.label}: ${context.raw}`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            display: true,
            color: 'rgba(0,0,0,0.05)'
          },
          ticks: {
            font: { size: 11 },
            beginAtZero: true
          }
        },
        x: {
          grid: {
            display: false
          },
          ticks: {
            font: { size: 11 },
            maxRotation: 45,
            minRotation: 0
          }
        }
      },
      animation: {
        duration: 600,
        easing: 'easeOutQuart'
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

    const barChartOptions = {
      plugins: { 
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.label}: ${context.raw}`;
            }
          }
        }
      },
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { 
          stacked: false, 
          grid: { display: false },
          ticks: { 
            color: '#222', 
            font: { size: 10 },
            maxRotation: 45,
            minRotation: 0
          },
          // Reduce bar thickness
          categoryPercentage: 0.6,
          barPercentage: 0.6
        },
        y: { 
          stacked: false, 
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { 
            color: '#222', 
            font: { size: 10 },
            beginAtZero: true
          }
        }
      },
      animation: {
        duration: 500,
        easing: 'easeOutQuart'
      },
      layout: {
        padding: {
          top: 10,
          bottom: 10,
          left: 10,
          right: 10
        }
      },
      // Limit maximum bar thickness
      maxBarThickness: 40
    }

    // Framework session management methods
    const checkSelectedFrameworkFromSession = async () => {
      try {
        console.log('🔍 DEBUG: Checking for selected framework from session in PolicyDashboard...')
        
        // Get user ID from localStorage or session
        const userId = localStorage.getItem('user_id') || localStorage.getItem('grc_user_id') || localStorage.getItem('userId')
        
        if (!userId) {
          console.error('❌ DEBUG: No user ID found for checking framework')
          return
        }
        
        const response = await apiService.get(API_ENDPOINTS.FRAMEWORK_GET_SELECTED, {
            userId: userId
        })
        console.log('📊 DEBUG: Selected framework response:', response)
        
        if (response && response.success) {
          // Check if a framework is selected (not null)
          if (response.frameworkId) {
          const frameworkIdFromSession = response.frameworkId
          console.log('✅ DEBUG: Found selected framework in session:', frameworkIdFromSession)
          
          // Store the session framework ID for filtering
          sessionFrameworkId.value = frameworkIdFromSession
          
          // Check if this framework exists in our loaded frameworks
          const frameworkExists = frameworks.value.find(f => f.id.toString() === frameworkIdFromSession.toString())
          
          if (frameworkExists) {
            console.log('✅ DEBUG: Framework exists in loaded frameworks:', frameworkExists.name)
            // Automatically select the framework from session
            selectedFramework.value = frameworkExists.id.toString()
            console.log('✅ DEBUG: Auto-selected framework from session:', selectedFramework.value)
            // Refresh policies and dashboard data with the selected framework
            await fetchPolicies(frameworkExists.id.toString())
            await refreshDashboardSummary(frameworkExists.id.toString())
            await updateAllCharts()
          } else {
            console.log('⚠️ DEBUG: Framework from session (ID:', frameworkIdFromSession, ') not found in loaded frameworks')
            console.log('📋 DEBUG: Available frameworks:', frameworks.value.map(f => ({ id: f.id, name: f.name })))
            // Clear the session framework ID since it doesn't exist
            sessionFrameworkId.value = null
            }
          } else {
            // "All Frameworks" is selected (frameworkId is null)
            console.log('ℹ️ DEBUG: No framework selected in session (All Frameworks selected)')
            console.log('🌐 DEBUG: Clearing framework selection to show all frameworks')
            sessionFrameworkId.value = null
            selectedFramework.value = 'all'
            // Refresh policies and dashboard data for all frameworks
            await fetchPolicies(null)
            await refreshDashboardSummary(null)
            await updateAllCharts()
          }
        } else {
          console.log('ℹ️ DEBUG: No framework found in session')
          sessionFrameworkId.value = null
        }
      } catch (error) {
        console.error('❌ DEBUG: Error checking selected framework from session:', error)
        sessionFrameworkId.value = null
      }
    }
    
    const saveFrameworkToSession = async (frameworkId) => {
      try {
        console.log('💾 DEBUG: Saving framework to session:', frameworkId)
        
        // Get user ID from localStorage or session
        const userId = localStorage.getItem('user_id') || localStorage.getItem('grc_user_id') || localStorage.getItem('userId')
        
        if (!userId) {
          console.error('❌ DEBUG: No user ID found for saving framework')
          return
        }
        
        // Send null to clear framework filter when "All Frameworks" is selected
        const payload = { 
          frameworkId: frameworkId === 'all' ? null : frameworkId,
          userId: userId
        }
        
        await apiService.post(API_ENDPOINTS.FRAMEWORK_SET_SELECTED, payload)
        console.log('✅ DEBUG: Framework saved to session successfully')
      } catch (error) {
        console.error('❌ DEBUG: Error saving framework to session:', error)
      }
    }
    
    const handleFrameworkChange = async () => {
      console.log('🔍 DEBUG: handleFrameworkChange called with:', selectedFramework.value)
      
      // Find the framework name from the frameworks list
      const frameworkName = frameworks.value.find(f => f.id === selectedFramework.value)?.name || 'All Frameworks'
      
      // Update Vuex store (this will also save to backend session)
      await store.dispatch('framework/setFramework', {
        id: selectedFramework.value !== 'all' ? selectedFramework.value : 'all',
        name: frameworkName
      })
      
      console.log('✅ DEBUG: Framework saved to Vuex store in PolicyDashboard:', selectedFramework.value)
      
      // Call the original onFrameworkChange logic
      await onFrameworkChange()
      // Refresh dashboard summary data with the new framework filter
      await refreshDashboardSummary(selectedFramework.value)
      // Update all charts with the new framework filter
      await updateAllCharts()
    }


    // Fetch policies for dropdown
    const fetchPolicies = async (frameworkId = null) => {
      try {
        console.log('🔍 DEBUG: fetchPolicies called with frameworkId:', frameworkId)
        let response
        if (frameworkId && frameworkId !== 'all') {
          console.log('🔍 DEBUG: Fetching policies for specific framework:', frameworkId)
          response = await dashboardService.getPoliciesByFramework(frameworkId)
        } else {
          console.log('🔍 DEBUG: Fetching all policies (no framework filter)')
          response = await dashboardService.getAllPolicies()
        }
        
        console.log('🔍 DEBUG: Raw policies response:', response.data)
        
        let policiesData = []
        if (response.data && Array.isArray(response.data)) {
          policiesData = response.data
        } else if (response.data && response.data.policies) {
          policiesData = response.data.policies
        } else if (response.data && response.data.data) {
          policiesData = response.data.data
        }
        
        policies.value = policiesData.map(policy => ({
          id: policy.id || policy.PolicyId,
          name: policy.name || policy.PolicyName,
          category: policy.category || policy.Department || '',
          status: policy.status || policy.ActiveInactive || '',
          description: policy.description || policy.PolicyDescription || ''
        }))
        
        // Extract unique categories from policies
        const uniqueCategories = [...new Set(policies.value.map(policy => policy.category).filter(cat => cat && cat.trim() !== ''))]
        categories.value = uniqueCategories
        
        console.log('🔍 DEBUG: Processed policies count:', policies.value.length)
        console.log('🔍 DEBUG: Processed policies:', policies.value)
        console.log('🔍 DEBUG: Extracted categories:', categories.value)
      } catch (err) {
        console.error('Error fetching policies:', err)
        policies.value = []
        categories.value = []
      }
    }

    // Handle framework selection
    const onFrameworkChange = async () => {
      console.log('🔍 DEBUG: onFrameworkChange called with framework:', selectedFramework.value)
      selectedPolicy.value = 'all'
      
      // Clear chart cache when filters change
      chartDataCache.value.clear()
      
      if (selectedFramework.value && selectedFramework.value !== 'all') {
        console.log('🔍 DEBUG: Fetching policies for framework:', selectedFramework.value)
        await fetchPolicies(selectedFramework.value)
        // Refresh dashboard summary with framework filter
        await refreshDashboardSummary(selectedFramework.value)
      } else {
        console.log('🔍 DEBUG: Clearing policies (no framework selected)')
        policies.value = []
        // Refresh dashboard summary without framework filter
        await refreshDashboardSummary('all')
      }
      
      console.log('🔍 DEBUG: Updating all charts after framework change')
      await updateAllCharts()
    }

    // Handle policy selection
    const onPolicyChange = async () => {
      console.log('Policy changed to:', selectedPolicy.value)
      // Clear chart cache when filters change
      chartDataCache.value.clear()
      
      // Refresh dashboard summary with current filters
      const frameworkId = selectedFramework.value !== 'all' ? selectedFramework.value : null
      await refreshDashboardSummary(frameworkId)
      
      await updateAllCharts()
    }

    // Handle time range selection
    const onTimeRangeChange = async () => {
      console.log('Time range changed to:', selectedTimeRange.value)
      // Clear chart cache when filters change
      chartDataCache.value.clear()
      
      // Refresh dashboard summary with current filters
      const frameworkId = selectedFramework.value !== 'all' ? selectedFramework.value : null
      await refreshDashboardSummary(frameworkId)
      
      await updateAllCharts()
    }

    // Handle category selection
    const onCategoryChange = async () => {
      console.log('Category changed to:', selectedCategory.value)
      // Clear chart cache when filters change
      chartDataCache.value.clear()
      
      // Refresh dashboard summary with current filters
      const frameworkId = selectedFramework.value !== 'all' ? selectedFramework.value : null
      await refreshDashboardSummary(frameworkId)
      
      await updateAllCharts()
    }

    // Handle priority selection
    const onPriorityChange = async () => {
      console.log('Priority changed to:', selectedPriority.value)
      // Clear chart cache when filters change
      chartDataCache.value.clear()
      
      // Refresh dashboard summary with current filters
      const frameworkId = selectedFramework.value !== 'all' ? selectedFramework.value : null
      await refreshDashboardSummary(frameworkId)
      
      await updateAllCharts()
    }

    // Update all charts with current filters (debounced)
    const updateAllCharts = async () => {
      // Clear existing timeout
      if (updateTimeout.value) {
        clearTimeout(updateTimeout.value)
      }
      
      // Debounce chart updates to prevent excessive API calls
      updateTimeout.value = setTimeout(async () => {
        try {
          chartsLoading.value = true
          
          // Update charts in parallel for faster loading
          await Promise.all([
            updateActiveInactiveChart(),
            updateCategoryChart(),
            updateStatusChart(),
            updateDepartmentChart()
          ])
        
      } catch (err) {
        console.error('Error updating charts:', err)
        error.value = 'Failed to update charts'
      } finally {
          chartsLoading.value = false
      }
      }, 150) // 150ms debounce for faster response
    }

    // Update Active/Inactive Chart
    const updateActiveInactiveChart = async () => {
      try {
        const params = { x_axis: 'framework', y_axis: 'activeInactive' }
          
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          params.framework_id = selectedFramework.value
          console.log('🔍 DEBUG: Active/Inactive chart - applying framework filter:', selectedFramework.value)
        } else {
          console.log('🔍 DEBUG: Active/Inactive chart - no framework filter (all frameworks)')
        }
        
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          params.policy_id = selectedPolicy.value
        }
        
        if (selectedTimeRange.value && selectedTimeRange.value !== 'all') {
          params.time_range = selectedTimeRange.value
        }
        
        if (selectedCategory.value && selectedCategory.value !== 'all') {
          params.category = selectedCategory.value
        }
        
        if (selectedPriority.value && selectedPriority.value !== 'all') {
          params.priority = selectedPriority.value
        }
        
        // Check cache first
        const cacheKey = `activeInactive_${JSON.stringify(params)}`
        if (chartDataCache.value.has(cacheKey)) {
          const cachedData = chartDataCache.value.get(cacheKey)
          activeInactiveData.datasets[0].data = cachedData
          return
        }
        
        const response = await dashboardService.getPolicyAnalytics(params)
        const data = response.data
        
        // Process active/inactive data
        const activeCount = data.find(item => item.label === 'Active')?.value || 0
        const inactiveCount = data.find(item => item.label === 'Inactive')?.value || 0
        
        const chartData = [activeCount, inactiveCount]
        activeInactiveData.datasets[0].data = chartData
        
        // Cache the result
        chartDataCache.value.set(cacheKey, chartData)
        
      } catch (err) {
        console.error('Error updating active/inactive chart:', err)
        activeInactiveData.datasets[0].data = [0, 0]
      }
    }

    // Update Category Chart
    const updateCategoryChart = async () => {
      try {
        const params = { x_axis: 'framework', y_axis: 'category' }
          
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          params.framework_id = selectedFramework.value
          console.log('🔍 DEBUG: Category chart - applying framework filter:', selectedFramework.value)
        } else {
          console.log('🔍 DEBUG: Category chart - no framework filter (all frameworks)')
        }
          
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          params.policy_id = selectedPolicy.value
        }
        
        if (selectedTimeRange.value && selectedTimeRange.value !== 'all') {
          params.time_range = selectedTimeRange.value
        }
        
        if (selectedCategory.value && selectedCategory.value !== 'all') {
          params.category = selectedCategory.value
        }
        
        if (selectedPriority.value && selectedPriority.value !== 'all') {
          params.priority = selectedPriority.value
        }
        
        // Check cache first
        const cacheKey = `category_${JSON.stringify(params)}`
        if (chartDataCache.value.has(cacheKey)) {
          const cachedData = chartDataCache.value.get(cacheKey)
          categoryData.labels = cachedData.labels
          categoryData.datasets[0].data = cachedData.values
          return
        }
        
        const response = await dashboardService.getPolicyAnalytics(params)
        const data = response.data
        
        const labels = data.map(item => item.label || 'Unknown')
        const values = data.map(item => item.value || 0)
        
        categoryData.labels = labels
        categoryData.datasets[0].data = values
        
        // Cache the result
        chartDataCache.value.set(cacheKey, { labels, values })
        
      } catch (err) {
        console.error('Error updating category chart:', err)
        categoryData.labels = ['No Data']
        categoryData.datasets[0].data = [0]
      }
    }

    // Update Status Chart
    const updateStatusChart = async () => {
      try {
        const params = { x_axis: 'framework', y_axis: 'status' }
        
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          params.framework_id = selectedFramework.value
          console.log('🔍 DEBUG: Status chart - applying framework filter:', selectedFramework.value)
        } else {
          console.log('🔍 DEBUG: Status chart - no framework filter (all frameworks)')
        }
        
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          params.policy_id = selectedPolicy.value
        }
        
        if (selectedTimeRange.value && selectedTimeRange.value !== 'all') {
          params.time_range = selectedTimeRange.value
        }
        
        if (selectedCategory.value && selectedCategory.value !== 'all') {
          params.category = selectedCategory.value
        }
        
        if (selectedPriority.value && selectedPriority.value !== 'all') {
          params.priority = selectedPriority.value
        }
        
        // Check cache first
        const cacheKey = `status_${JSON.stringify(params)}`
        if (chartDataCache.value.has(cacheKey)) {
          const cachedData = chartDataCache.value.get(cacheKey)
          statusData.labels = cachedData.labels
          statusData.datasets[0].data = cachedData.values
          return
        }
        
        const response = await dashboardService.getPolicyAnalytics(params)
        const data = response.data
        
        const labels = data.map(item => item.label || 'Unknown')
        const values = data.map(item => item.value || 0)
        
        statusData.labels = labels
        statusData.datasets[0].data = values
        
        // Cache the result
        chartDataCache.value.set(cacheKey, { labels, values })
        
      } catch (err) {
        console.error('Error updating status chart:', err)
        statusData.labels = ['No Data']
        statusData.datasets[0].data = [0]
      }
    }

    // Update Department Chart
    const updateDepartmentChart = async () => {
      try {
        const params = { x_axis: 'framework', y_axis: 'department' }
        
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          params.framework_id = selectedFramework.value
          console.log('🔍 DEBUG: Department chart - applying framework filter:', selectedFramework.value)
        } else {
          console.log('🔍 DEBUG: Department chart - no framework filter (all frameworks)')
        }
        
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          params.policy_id = selectedPolicy.value
        }
        
        if (selectedTimeRange.value && selectedTimeRange.value !== 'all') {
          params.time_range = selectedTimeRange.value
        }
        
        if (selectedCategory.value && selectedCategory.value !== 'all') {
          params.category = selectedCategory.value
        }
        
        if (selectedPriority.value && selectedPriority.value !== 'all') {
          params.priority = selectedPriority.value
        }
        
        // Check cache first
        const cacheKey = `department_${JSON.stringify(params)}`
        if (chartDataCache.value.has(cacheKey)) {
          const cachedData = chartDataCache.value.get(cacheKey)
          departmentData.labels = cachedData.labels
          departmentData.datasets[0].data = cachedData.values
          return
        }
        
        const response = await dashboardService.getPolicyAnalytics(params)
        const data = response.data
        
        const labels = data.map(item => item.label || 'Unknown')
        const values = data.map(item => item.value || 0)
        
        departmentData.labels = labels
        departmentData.datasets[0].data = values
        
        // Cache the result
        chartDataCache.value.set(cacheKey, { labels, values })
        
      } catch (err) {
        console.error('Error updating department chart:', err)
        departmentData.labels = ['No Data']
        departmentData.datasets[0].data = [0]
      }
    }

    // Fetch critical dashboard data first (summary, frameworks)
    const fetchCriticalData = async () => {
      try {
        loading.value = true
        error.value = null

        // Load only critical data first - summary and frameworks
        const summaryParams = {}
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          summaryParams.framework_id = selectedFramework.value
        }

        const [summaryRes, frameworksRes] = await Promise.all([
          dashboardService.getDashboardSummary(summaryParams),
          dashboardService.getAllFrameworks()
        ])

        dashboardData.value = summaryRes.data
        
        // Process frameworks
        let frameworksData = []
        if (frameworksRes.data && Array.isArray(frameworksRes.data)) {
          frameworksData = frameworksRes.data
        } else if (frameworksRes.data && frameworksRes.data.frameworks) {
          frameworksData = frameworksRes.data.frameworks
        } else if (frameworksRes.data && frameworksRes.data.data) {
          frameworksData = frameworksRes.data.data
        }
        
        frameworks.value = frameworksData.map(fw => ({
          id: fw.id || fw.FrameworkId,
          name: fw.name || fw.FrameworkName,
          category: fw.category || fw.Category || '',
          status: fw.status || fw.ActiveInactive || '',
          description: fw.description || fw.FrameworkDescription || ''
        }))

        initialDataLoaded.value = true
        loading.value = false

        // Load remaining data in background
        loadBackgroundData()
        
      } catch (err) {
        console.error('Error fetching critical dashboard data:', err)
        error.value = 'Failed to load dashboard data'
        loading.value = false
      }
    }

    // Load non-critical data in background
    const loadBackgroundData = async () => {
      try {
        const summaryParams = {}
        const statusParams = {}
        const approvalTimeParams = {}
        const workloadParams = {}
        
        if (selectedFramework.value && selectedFramework.value !== 'all') {
          summaryParams.framework_id = selectedFramework.value
          statusParams.framework_id = selectedFramework.value
          approvalTimeParams.framework_id = selectedFramework.value
          workloadParams.framework_id = selectedFramework.value
        }

        // Load non-critical data AND charts in parallel for maximum speed
        const [statusRes, activityRes, approvalTimeRes, workloadRes] = await Promise.all([
          dashboardService.getPolicyStatusDistribution(statusParams),
          dashboardService.getRecentPolicyActivity(),
          dashboardService.getAvgApprovalTime(approvalTimeParams),
          dashboardService.getReviewerWorkload(workloadParams),
          // Load charts immediately in parallel
          loadCharts()
        ])

        statusDistribution.value = statusRes.data
        recentActivity.value = activityRes.data
        avgApprovalTime.value = approvalTimeRes.data.average_days
        reviewerWorkload.value = workloadRes.data
        
        // Load policies if needed
        if (!selectedFramework.value || selectedFramework.value === 'all') {
          await fetchPolicies()
        }

      } catch (err) {
        console.error('Error loading background data:', err)
      }
    }

    // Load charts separately
    const loadCharts = async () => {
      try {
        chartsLoading.value = true
        
        // Load charts immediately without debounce for initial load
        await Promise.all([
          updateActiveInactiveChart(),
          updateCategoryChart(),
          updateStatusChart(),
          updateDepartmentChart()
        ])
      } catch (err) {
        console.error('Error loading charts:', err)
      } finally {
        chartsLoading.value = false
      }
    }

    // Refresh dashboard summary data with all current filters
    const refreshDashboardSummary = async (frameworkId = null) => {
      try {
        console.log('🔍 DEBUG: Refreshing dashboard summary with framework:', frameworkId)
        
        // Prepare parameters for all current filters
        const summaryParams = {}
        const statusParams = {}
        const approvalTimeParams = {}
        const workloadParams = {}
        
        // Add framework filter if provided and not 'all'
        if (frameworkId && frameworkId !== 'all') {
          summaryParams.framework_id = frameworkId
          statusParams.framework_id = frameworkId
          approvalTimeParams.framework_id = frameworkId
          workloadParams.framework_id = frameworkId
          console.log('🔍 DEBUG: Applying framework filter:', frameworkId)
        } else {
          console.log('🔍 DEBUG: No framework filter - showing all frameworks data')
        }
        
        // Add policy filter if selected
        if (selectedPolicy.value && selectedPolicy.value !== 'all') {
          summaryParams.policy_id = selectedPolicy.value
          statusParams.policy_id = selectedPolicy.value
          approvalTimeParams.policy_id = selectedPolicy.value
          workloadParams.policy_id = selectedPolicy.value
        }
        
        // Add time range filter if selected
        if (selectedTimeRange.value && selectedTimeRange.value !== 'all') {
          summaryParams.time_range = selectedTimeRange.value
          statusParams.time_range = selectedTimeRange.value
          approvalTimeParams.time_range = selectedTimeRange.value
          workloadParams.time_range = selectedTimeRange.value
        }
        
        // Add category filter if selected
        if (selectedCategory.value && selectedCategory.value !== 'all') {
          summaryParams.category = selectedCategory.value
          statusParams.category = selectedCategory.value
          approvalTimeParams.category = selectedCategory.value
          workloadParams.category = selectedCategory.value
        }
        
        // Add priority filter if selected
        if (selectedPriority.value && selectedPriority.value !== 'all') {
          summaryParams.priority = selectedPriority.value
          statusParams.priority = selectedPriority.value
          approvalTimeParams.priority = selectedPriority.value
          workloadParams.priority = selectedPriority.value
        }

        console.log('🔍 DEBUG: Applying filters to dashboard summary:', {
          framework: frameworkId,
          policy: selectedPolicy.value,
          timeRange: selectedTimeRange.value,
          category: selectedCategory.value,
          priority: selectedPriority.value
        })

        const [
          summaryRes,
          statusRes,
          approvalTimeRes,
          workloadRes
        ] = await Promise.all([
          dashboardService.getDashboardSummary(summaryParams),
          dashboardService.getPolicyStatusDistribution(statusParams),
          dashboardService.getAvgApprovalTime(approvalTimeParams),
          dashboardService.getReviewerWorkload(workloadParams)
        ])

        // Update dashboard data with new filtered data
        dashboardData.value = {
          ...dashboardData.value,
          ...summaryRes.data
        }
        statusDistribution.value = statusRes.data
        avgApprovalTime.value = approvalTimeRes.data.average_days
        reviewerWorkload.value = workloadRes.data
        
        console.log('🔍 DEBUG: Dashboard summary refreshed with filters')
        console.log('🔍 DEBUG: Updated summary data:', summaryRes.data)
        console.log('🔍 DEBUG: Updated dashboardData.value:', dashboardData.value)
      } catch (err) {
        console.error('Error refreshing dashboard summary:', err)
      }
    }

    // Watch for filter changes
    watch([selectedFramework, selectedPolicy, selectedTimeRange, selectedCategory, selectedPriority], async () => {
      // Refresh dashboard summary with current filters
      const frameworkId = selectedFramework.value !== 'all' ? selectedFramework.value : null
      await refreshDashboardSummary(frameworkId)
      // Update charts
      await updateAllCharts()
    })

    // Fetch data on component mount
    onMounted(async () => {
      // Load framework from Vuex store
      const storeFrameworkId = store.state.framework.selectedFrameworkId
      if (storeFrameworkId && storeFrameworkId !== 'all') {
        selectedFramework.value = storeFrameworkId
        console.log('🔄 PolicyDashboard: Loaded framework from Vuex store:', storeFrameworkId)
      }
      
      // Load critical data and activities in parallel for faster loading
      await Promise.all([
        fetchCriticalData(),
        fetchRecentActivities() // Load activities in parallel with charts
      ])
      
      // Check for selected framework from session after loading frameworks
      await checkSelectedFrameworkFromSession()
      
      // Auto-refresh activities every 5 minutes
      activityRefreshInterval.value = setInterval(() => {
        fetchRecentActivities()
      }, 300000) // 5 minutes
    })

    // Cleanup on unmount
    onUnmounted(() => {
      if (activityRefreshInterval.value) {
        clearInterval(activityRefreshInterval.value)
      }
      if (updateTimeout.value) {
        clearTimeout(updateTimeout.value)
      }
    })
    
    // Watch for Vuex store framework changes
    watch(
      () => store.state.framework.selectedFrameworkId,
      async (newFrameworkId, oldFrameworkId) => {
        // Only update if value actually changed
        if (newFrameworkId === oldFrameworkId) return
        
        console.log('🔄 PolicyDashboard: Vuex store framework changed to:', newFrameworkId)
        // Update local filter to match store
        if (newFrameworkId === 'all' || !newFrameworkId) {
          selectedFramework.value = 'all'
        } else {
          selectedFramework.value = newFrameworkId
        }
        
        // Force data refresh
        const frameworkId = selectedFramework.value !== 'all' ? selectedFramework.value : null
        await refreshDashboardSummary(frameworkId)
        await updateAllCharts()
      }
    )


    const getActivityIconClass = (activityType) => {
      // Map activity types to global icon color classes from main.css
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
    };

    // Enhanced Recent Activities Methods
    const fetchRecentActivities = async () => {
      try {
        // Only show loading if we don't have any activities yet
        if (recentActivities.value.length === 0) {
          loadingActivities.value = true
        }
        console.log('Fetching recent policy activities...')
        
        let activities = []
        
        // First, try to fetch from the recent activity API (this is the most reliable)
        // Add timeout to prevent hanging
        try {
          const activityRes = await Promise.race([
            dashboardService.getRecentPolicyActivity(),
            new Promise((_, reject) => setTimeout(() => reject(new Error('Activity API timeout')), 10000))
          ])
          console.log('Activity API response:', activityRes)
          
          let policyActivities = []
          if (Array.isArray(activityRes.data)) {
            policyActivities = activityRes.data
          } else if (activityRes.data && Array.isArray(activityRes.data.results)) {
            policyActivities = activityRes.data.results
          } else if (activityRes.data && Array.isArray(activityRes.data.data)) {
            policyActivities = activityRes.data.data
          }
          
          console.log('Processed policy activities from API:', policyActivities.length)
          
          if (policyActivities && policyActivities.length > 0) {
            policyActivities.forEach(activity => {
              const policyName = activity.name || 'Unknown Policy'
              const createdBy = activity.created_by || 'Unknown User'
              const activityType = activity.type || 'policy_created'
              
              activities.push({
                type: getActivityTypeClass(activityType),
                icon: getActivityIcon(activityType),
                title: getActivityTitle(activityType),
                description: `"${truncateText(policyName, 50)}" ${getActivityDescription(activityType)}`,
                time: formatRelativeTime(activity.date),
                metadata: {
                  policyId: activity.policyId || activity.id,
                  creator: createdBy,
                  type: activityType
                }
              })
            })
            console.log(`Added ${activities.length} activities from recent activity API`)
          }
          } catch (activityError) {
          console.error('Error fetching recent activity API:', activityError)
          // Don't throw - continue to fallback
        }
        
        // If still no activities, try fetching recent policies as fallback
        // Add timeout to prevent hanging
        if (activities.length === 0) {
          try {
            console.log('No activities from API, trying fallback to recent policies...')
            const policiesRes = await Promise.race([
              dashboardService.getRecentPolicies(),
              new Promise((_, reject) => setTimeout(() => reject(new Error('Policies API timeout')), 10000))
            ])
            console.log('Recent policies response:', policiesRes)
            
            let policies = []
            if (Array.isArray(policiesRes.data)) {
              policies = policiesRes.data
            } else if (policiesRes.data && Array.isArray(policiesRes.data.results)) {
              policies = policiesRes.data.results
            } else if (policiesRes.data && Array.isArray(policiesRes.data.data)) {
              policies = policiesRes.data.data
            }
            
            console.log('Processed policies for activities:', policies.length)
            
            if (policies && policies.length > 0) {
              policies.slice(0, 3).forEach(policy => {
                const policyName = policy.PolicyName || policy.name || 'Unknown Policy'
                const createdBy = policy.CreatedByName || policy.CreatedBy || policy.created_by || 'Unknown User'
                const createdDate = policy.CreatedByDate || policy.CreatedDate || policy.created_date
                
                if (createdDate) {
                  activities.push({
                    type: 'created',
                    icon: 'fas fa-file-alt',
                    title: 'Policy Created',
                    description: `"${truncateText(policyName, 50)}" created by ${createdBy}`,
                    time: formatRelativeTime(createdDate),
                    metadata: {
                      policyId: policy.PolicyId || policy.id || policy.policyId,
                      creator: createdBy,
                      type: 'policy_created'
                    }
                  })
                }
              })
              console.log(`Added ${activities.length} activities from recent policies fallback`)
            }
          } catch (policiesError) {
            console.error('Error fetching recent policies:', policiesError)
            // Don't throw - just log the error and continue
          }
        }
        
        // If still no activities after all attempts, log a warning but don't fail
        if (activities.length === 0) {
          console.warn('⚠️ No activities found after all API attempts. This is normal if there are no recent policy activities.')
        }
        
        // Sort all activities by time (most recent first)
        activities.sort((a, b) => {
          const timeA = parseRelativeTime(a.time)
          const timeB = parseRelativeTime(b.time)
          return timeA - timeB // Sort by actual time difference (smaller = more recent)
        })
        
        // Remove duplicates and limit to 3 items (latest 3 actions)
        const uniqueActivities = activities.filter((activity, index, self) => 
          index === self.findIndex(a => a.description === activity.description)
        ).slice(0, 3)
        
        recentActivities.value = uniqueActivities
        console.log(`Loaded ${recentActivities.value.length} recent policy activities`)
        console.log('Recent activities data:', recentActivities.value)
        
      } catch (error) {
        console.error('Error fetching recent activities:', error)
        recentActivities.value = []
      } finally {
        loadingActivities.value = false
      }
    }

    const getActivityTypeClass = (activityType) => {
      switch (activityType) {
        case 'policy_created':
        case 'framework_created':
          return 'created'
        case 'policy_approved':
        case 'framework_approved':
          return 'approved'
        case 'policy_rejected':
        case 'framework_rejected':
          return 'rejected'
        case 'policy_updated':
        case 'framework_updated':
          return 'updated'
        case 'policy_deactivated':
        case 'framework_deactivated':
          return 'deactivation'
        case 'policy_review':
        case 'framework_review':
          return 'review'
        case 'policy_version':
        case 'framework_version':
          return 'version'
        case 'policy_submitted':
        case 'framework_submitted':
          return 'submitted'
        default:
          return 'created'
      }
    }

    const getActivityIcon = (activityType) => {
      switch (activityType) {
        case 'policy_created':
          return 'fas fa-file-alt'
        case 'framework_created':
          return 'fas fa-layer-group'
        case 'policy_approved':
          return 'fas fa-check-circle'
        case 'framework_approved':
          return 'fas fa-check-circle'
        case 'policy_rejected':
        case 'framework_rejected':
          return 'fas fa-times-circle'
        case 'policy_updated':
        case 'framework_updated':
          return 'fas fa-edit'
        case 'policy_deactivated':
        case 'framework_deactivated':
          return 'fas fa-power-off'
        case 'policy_review':
        case 'framework_review':
          return 'fas fa-eye'
        case 'policy_version':
        case 'framework_version':
          return 'fas fa-code-branch'
        case 'policy_submitted':
          return 'fas fa-paper-plane'
        case 'framework_submitted':
          return 'fas fa-paper-plane'
        default:
          // Default fallback based on activity type class
          if (activityType && activityType.includes('policy')) {
            return 'fas fa-file-alt'
          } else if (activityType && activityType.includes('framework')) {
            return 'fas fa-layer-group'
          }
          return 'fas fa-plus-circle'
      }
    }

    const getActivityTitle = (activityType) => {
      switch (activityType) {
        case 'policy_created':
          return 'New Policy Created'
        case 'framework_created':
          return 'New Framework Created'
        case 'policy_approved':
          return 'Policy Approved'
        case 'framework_approved':
          return 'Framework Approved'
        case 'policy_rejected':
          return 'Policy Rejected'
        case 'framework_rejected':
          return 'Framework Rejected'
        case 'policy_updated':
          return 'Policy Updated'
        case 'framework_updated':
          return 'Framework Updated'
        case 'policy_deactivated':
          return 'Policy Deactivated'
        case 'framework_deactivated':
          return 'Framework Deactivated'
        case 'policy_review':
          return 'Policy Under Review'
        case 'framework_review':
          return 'Framework Under Review'
        case 'policy_version':
          return 'Policy Version Created'
        case 'framework_version':
          return 'Framework Version Created'
        case 'policy_submitted':
          return 'Policy Submitted for Review'
        case 'framework_submitted':
          return 'Framework Submitted for Review'
        default:
          return 'Policy Activity'
      }
    }

    const getActivityDescription = (activityType) => {
      switch (activityType) {
        case 'policy_created':
          return 'created by user'
        case 'framework_created':
          return 'created by user'
        case 'policy_approved':
          return 'approved by reviewer'
        case 'framework_approved':
          return 'approved by reviewer'
        case 'policy_rejected':
          return 'needs revision'
        case 'framework_rejected':
          return 'needs revision'
        case 'policy_updated':
          return 'modified by user'
        case 'framework_updated':
          return 'modified by user'
        case 'policy_deactivated':
          return 'deactivated by user'
        case 'framework_deactivated':
          return 'deactivated by user'
        case 'policy_review':
          return 'submitted for review'
        case 'framework_review':
          return 'submitted for review'
        case 'policy_version':
          return 'new version created'
        case 'framework_version':
          return 'new version created'
        case 'policy_submitted':
          return 'submitted for review'
        case 'framework_submitted':
          return 'submitted for review'
        default:
          return 'activity occurred'
      }
    }

    const truncateText = (text, maxLength) => {
      if (!text) return 'Unknown'
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
    }

    const formatRelativeTime = (dateString) => {
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
    }

    const parseRelativeTime = (timeString) => {
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
    }

    const refreshRecentActivities = () => {
      // Don't show loading spinner on refresh if we already have activities
      // Just refresh in the background
      fetchRecentActivities()
    }

    // Export dashboard as PDF
    const exportDashboardAsPDF = async () => {
      isExporting.value = true
      try {
        await new Promise(resolve => setTimeout(resolve, 100)) // Small delay for Vue reactivity
        
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
              card.style.flexDirection = 'column'
              card.style.visibility = 'visible'
              card.style.opacity = '1'
              card.style.background = '#ffffff'
            })

            // Hide loading overlays in clone
            const loadingElements = clonedDoc.querySelectorAll('.loading-overlay, .error-message, .chart-loading, .activity-loading')
            loadingElements.forEach(el => el.style.display = 'none')
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
        const filename = `Policy-Dashboard-${timestamp}.pdf`

        // Download the PDF
        pdf.save(filename)

        console.log('PDF downloaded successfully')
        
        // Show success feedback
        exportSuccess.value = true
        setTimeout(() => {
          exportSuccess.value = false
        }, 2000)
      } catch (error) {
        console.error('Error generating PDF:', error)
        alert('Failed to generate PDF. Please try again.')
      } finally {
        isExporting.value = false
      }
    }

    // Handle export button click using the new export controls
    const handleExportClick = async () => {
      if (!selectedExportFormat.value) {
        return
      }

      // For now, only PDF export is supported for the policy dashboard
      if (selectedExportFormat.value === 'pdf') {
        await exportDashboardAsPDF()
      }
    }

    // Navigation function to go back to Policy Management
    const goBackToPolicyManagement = () => {
      // Navigate to the policy list or main policy page
      // You can adjust this route based on your application's routing structure
      window.history.back()
    }

    return {
      dashboardData,
      recentActivity,
      recentActivities,
      loadingActivities,
      activityRefreshInterval,
      avgApprovalTime,
      loading,
      error,
      activeInactiveData,
      categoryData,
      statusData,
      departmentData,
      donutChartOptions,
      lineChartOptions,
      barChartOptions,
      showPolicyDetails,
      fetchCriticalData,
      fetchRecentActivities,
      refreshRecentActivities,
      // Removed activeTab from return object
      getActivityIconClass,
      frameworks,
      policies,
      categories,
      selectedFramework,
      selectedPolicy,
      selectedTimeRange,
      selectedCategory,
      selectedPriority,
      onFrameworkChange,
      onPolicyChange,
      onTimeRangeChange,
      onCategoryChange,
      onPriorityChange,
      // Framework session filtering
      sessionFrameworkId,
      filteredFrameworks,
      frameworkOptions,
      policyOptions,
      checkSelectedFrameworkFromSession,
      saveFrameworkToSession,
      handleFrameworkChange,
      exportDashboardAsPDF,
      isExporting,
      exportSuccess,
      goBackToPolicyManagement,
      // New loading states
      chartsLoading,
      initialDataLoaded,
      chartDataCache,
      // Export controls (shared global styles)
      selectedExportFormat,
      selectedExportFormatLabel,
      isExportDropdownOpen,
      exportFormatOptions,
      selectExportFormatOption,
      handleExportClick,
      getSelectedFrameworkName,
      getSelectedPolicyName,
      clearFrameworkSelection,
      clearPolicySelection
    }
  }
}
</script>

<style scoped>
@import '@/assets/css/dropdown.css';
@import './PolicyDashboard.css';

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #4f6cff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background-color: #fee2e2;
  border: 1px solid #ef4444;
  color: #b91c1c;
  padding: 1rem;
  margin: 1rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.retry-btn {
  background-color: #b91c1c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background-color: #991b1b;
}

.activity-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #666;
  margin-top: 0.25rem;
}

.activity-author {
  color: #4f6cff;
  font-weight: 500;
}
</style> 