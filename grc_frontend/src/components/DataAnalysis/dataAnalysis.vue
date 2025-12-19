<template>
  <div class="data-analysis-container">
    <div class="header">
      <div class="header-content">
        <div>
          <h1 class="page-title">
            <i class="fas fa-chart-pie"></i>
            Data Analysis Dashboard
          </h1>
          <p class="page-subtitle">Data Inventory Analysis by Module</p>
        </div>
        <div class="framework-selector">
          <label for="framework-select" class="framework-label">
            <i class="fas fa-filter"></i>
            Filter by Framework:
          </label>
          <select
            id="framework-select"
            v-model="selectedFrameworkId"
            @change="onFrameworkChange"
            class="framework-dropdown"
            :disabled="loadingFrameworks"
          >
            <option value="all">All Frameworks</option>
            <option
              v-for="framework in frameworks"
              :key="framework.id"
              :value="framework.id"
            >
              {{ framework.name }}
            </option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Loading data analysis...</p>
    </div>

    <div v-else-if="error" class="error-container">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="fetchData" class="retry-button">Retry</button>
    </div>

    <div v-else class="dashboard-content">
      <!-- Summary Cards -->
      <div class="summary-section">
        <div class="summary-card">
          <div class="summary-icon personal">
            <i class="fas fa-user-shield"></i>
          </div>
          <div class="summary-content">
            <h3>Personal Data</h3>
            <p class="summary-percentage">{{ overallStats.personal }}%</p>
            <p class="summary-count">{{ overallStats.personalCount }} fields</p>
          </div>
        </div>
        <div class="summary-card">
          <div class="summary-icon regular">
            <i class="fas fa-file-alt"></i>
          </div>
          <div class="summary-content">
            <h3>Regular Data</h3>
            <p class="summary-percentage">{{ overallStats.regular }}%</p>
            <p class="summary-count">{{ overallStats.regularCount }} fields</p>
          </div>
        </div>
        <div class="summary-card">
          <div class="summary-icon confidential">
            <i class="fas fa-lock"></i>
          </div>
          <div class="summary-content">
            <h3>Confidential Data</h3>
            <p class="summary-percentage">{{ overallStats.confidential }}%</p>
            <p class="summary-count">{{ overallStats.confidentialCount }} fields</p>
          </div>
        </div>
        <div class="summary-card">
          <div class="summary-icon maturity">
            <i class="fas fa-chart-line"></i>
          </div>
          <div class="summary-content">
            <h3>Privacy Maturity</h3>
            <p class="summary-percentage">
              {{ privacyMetrics.maturity_score != null ? privacyMetrics.maturity_score : 0 }}<span style="font-size:14px;"> / 100</span>
            </p>
            <p class="summary-count">Overall privacy maturity score</p>
          </div>
        </div>
        <div class="summary-card">
          <div class="summary-icon minimization">
            <i class="fas fa-compress-arrows-alt"></i>
          </div>
          <div class="summary-content">
            <h3>Data Minimization</h3>
            <p class="summary-percentage">
              {{ privacyMetrics.minimization_score != null ? privacyMetrics.minimization_score : 0 }}<span style="font-size:14px;"> / 100</span>
            </p>
            <p class="summary-count">Lower sensitive data → higher score</p>
          </div>
        </div>
        <div class="summary-card">
          <div class="summary-icon coverage">
            <i class="fas fa-database"></i>
          </div>
          <div class="summary-content">
            <h3>Inventory Coverage</h3>
            <p class="summary-percentage">
              {{ privacyMetrics.data_inventory_coverage != null ? privacyMetrics.data_inventory_coverage : 0 }}%
            </p>
            <p class="summary-count">Modules with data inventory configured</p>
          </div>
        </div>
      </div>

      <!-- Module Cards -->
      <div class="modules-grid">
        <div
          v-for="(module, moduleName) in modules"
          :key="moduleName"
          class="module-card"
        >
          <div class="module-header">
            <h2 class="module-title">
              <i :class="getModuleIcon(moduleName)"></i>
              {{ formatModuleName(moduleName) }}
            </h2>
            <div class="module-stats">
              <span class="stat-item">
                <i class="fas fa-database"></i>
                {{ module.total_records }} records
              </span>
              <span class="stat-item">
                <i class="fas fa-list"></i>
                {{ module.total_fields }} fields
              </span>
            </div>
          </div>

          <div class="module-content">
            <!-- AI Privacy Metrics Mini Charts -->
            <div class="module-privacy-metrics" v-if="privacyMetrics">
              <div class="metric-row">
                <span class="metric-label">
                  <i class="fas fa-chart-line"></i>
                  Maturity
                </span>
                <div class="metric-bar">
                  <div
                    class="metric-bar-fill maturity"
                    :style="{ width: (privacyMetrics.maturity_score || 0) + '%' }"
                  ></div>
                </div>
                <span class="metric-value">
                  {{ privacyMetrics.maturity_score != null ? privacyMetrics.maturity_score : 0 }}/100
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">
                  <i class="fas fa-compress-arrows-alt"></i>
                  Minimization
                </span>
                <div class="metric-bar">
                  <div
                    class="metric-bar-fill minimization"
                    :style="{ width: (privacyMetrics.minimization_score || 0) + '%' }"
                  ></div>
                </div>
                <span class="metric-value">
                  {{ privacyMetrics.minimization_score != null ? privacyMetrics.minimization_score : 0 }}/100
                </span>
              </div>
              <div class="metric-row">
                <span class="metric-label">
                  <i class="fas fa-database"></i>
                  Coverage
                </span>
                <div class="metric-bar">
                  <div
                    class="metric-bar-fill coverage"
                    :style="{ width: (privacyMetrics.data_inventory_coverage || 0) + '%' }"
                  ></div>
                </div>
                <span class="metric-value">
                  {{ privacyMetrics.data_inventory_coverage != null ? privacyMetrics.data_inventory_coverage : 0 }}%
                </span>
              </div>
            </div>

            <!-- Progress Bars -->
            <div class="progress-section">
              <div class="progress-item">
                <div class="progress-label">
                  <span>Personal</span>
                  <span class="progress-value">{{ module.personal }}%</span>
                </div>
                <div class="progress-bar">
                  <div
                    class="progress-fill personal"
                    :style="{ width: module.personal + '%' }"
                  ></div>
                </div>
              </div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>Regular</span>
                  <span class="progress-value">{{ module.regular }}%</span>
                </div>
                <div class="progress-bar">
                  <div
                    class="progress-fill regular"
                    :style="{ width: module.regular + '%' }"
                  ></div>
                </div>
              </div>
              <div class="progress-item">
                <div class="progress-label">
                  <span>Confidential</span>
                  <span class="progress-value">{{ module.confidential }}%</span>
                </div>
                <div class="progress-bar">
                  <div
                    class="progress-fill confidential"
                    :style="{ width: module.confidential + '%' }"
                  ></div>
                </div>
              </div>
            </div>

            <!-- Pie Chart Visualization -->
            <div class="chart-container">
              <div class="pie-chart-wrapper">
                <div class="pie-chart">
                  <svg viewBox="0 0 100 100" class="pie-svg">
                  <circle
                    cx="50"
                    cy="50"
                    r="38"
                    fill="none"
                    stroke="#e0e0e0"
                    stroke-width="12"
                  />
                    <circle
                      v-if="module.personal > 0"
                      cx="50"
                      cy="50"
                      r="38"
                      fill="none"
                      stroke="#81C784"
                      stroke-width="12"
                      :stroke-dasharray="`${module.personal * 2.387} 238.7`"
                      stroke-dashoffset="0"
                      transform="rotate(-90 50 50)"
                      class="chart-segment personal-segment"
                      @mouseenter="showTooltip($event, 'personal', module.columns?.personal || [])"
                      @mouseleave="hideTooltip"
                      @mousemove="updateTooltipPosition($event)"
                      style="cursor: pointer;"
                    />
                    <circle
                      v-if="module.regular > 0"
                      cx="50"
                      cy="50"
                      r="38"
                      fill="none"
                      stroke="#64B5F6"
                      stroke-width="12"
                      :stroke-dasharray="`${module.regular * 2.387} 238.7`"
                      :stroke-dashoffset="-(module.personal * 2.387)"
                      transform="rotate(-90 50 50)"
                      class="chart-segment regular-segment"
                      @mouseenter="showTooltip($event, 'regular', module.columns?.regular || [])"
                      @mouseleave="hideTooltip"
                      @mousemove="updateTooltipPosition($event)"
                      style="cursor: pointer;"
                    />
                    <circle
                      v-if="module.confidential > 0"
                      cx="50"
                      cy="50"
                      r="38"
                      fill="none"
                      stroke="#E57373"
                      stroke-width="12"
                      :stroke-dasharray="`${module.confidential * 2.387} 238.7`"
                      :stroke-dashoffset="-(module.personal + module.regular) * 2.387"
                      transform="rotate(-90 50 50)"
                      class="chart-segment confidential-segment"
                      @mouseenter="showTooltip($event, 'confidential', module.columns?.confidential || [])"
                      @mouseleave="hideTooltip"
                      @mousemove="updateTooltipPosition($event)"
                      style="cursor: pointer;"
                    />
                  </svg>
                  <div class="pie-center">
                    <span class="pie-total">{{ module.total_fields }}</span>
                    <span class="pie-label">Fields</span>
                  </div>
                </div>
                <!-- Tooltip -->
                <transition name="tooltip-fade">
                  <div
                    v-if="tooltip.visible"
                    class="chart-tooltip"
                    :style="{ top: tooltip.y + 'px', left: tooltip.x + 'px' }"
                  >
                  <div class="tooltip-header">
                    <i :class="getCategoryIcon(tooltip.category)"></i>
                    {{ tooltip.category }} Data
                  </div>
                  <div class="tooltip-content">
                    <div v-if="tooltip.columns && tooltip.columns.length > 0" class="tooltip-columns">
                      <div class="tooltip-subtitle">Column Headers:</div>
                      <div
                        v-for="(column, index) in tooltip.columns"
                        :key="index"
                        class="tooltip-column-item"
                      >
                        <i class="fas fa-chevron-right"></i>
                        {{ column }}
                      </div>
                    </div>
                    <div v-else class="tooltip-empty">No columns found</div>
                  </div>
                  </div>
                </transition>
              </div>
            </div>

            <!-- Count Details -->
            <div class="count-details" v-if="module.counts">
              <div class="count-item">
                <span class="count-label personal">Personal:</span>
                <span class="count-value">{{ module.counts.personal }}</span>
              </div>
              <div class="count-item">
                <span class="count-label regular">Regular:</span>
                <span class="count-value">{{ module.counts.regular }}</span>
              </div>
              <div class="count-item">
                <span class="count-label confidential">Confidential:</span>
                <span class="count-value">{{ module.counts.confidential }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { API_ENDPOINTS, API_BASE_URL } from '../../config/api.js'
import './dataAnalysis.css'
import aiPrivacyService from '@/services/aiPrivacyService' // NEW: reuse AI privacy metrics

export default {
  name: 'DataAnalysis',
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const data = ref({})
    const frameworks = ref([])
    const loadingFrameworks = ref(false)
    const selectedFrameworkId = ref('all')
    const tooltip = ref({
      visible: false,
      category: '',
      columns: [],
      x: 0,
      y: 0
    })
    const privacyMetrics = ref({
      maturity_score: 0,
      minimization_score: 0,
      data_inventory_coverage: 0
    })

    const modules = computed(() => {
      return data.value || {}
    })

    const overallStats = computed(() => {
      const modules = data.value || {}
      let totalPersonal = 0
      let totalRegular = 0
      let totalConfidential = 0

      Object.values(modules).forEach(module => {
        if (module.counts) {
          totalPersonal += module.counts.personal || 0
          totalRegular += module.counts.regular || 0
          totalConfidential += module.counts.confidential || 0
        }
      })

      const total = totalPersonal + totalRegular + totalConfidential
      if (total === 0) {
        return {
          personal: 0,
          regular: 0,
          confidential: 0,
          personalCount: 0,
          regularCount: 0,
          confidentialCount: 0
        }
      }

      return {
        personal: ((totalPersonal / total) * 100).toFixed(2),
        regular: ((totalRegular / total) * 100).toFixed(2),
        confidential: ((totalConfidential / total) * 100).toFixed(2),
        personalCount: totalPersonal,
        regularCount: totalRegular,
        confidentialCount: totalConfidential
      }
    })

    const fetchFrameworks = async () => {
      try {
        loadingFrameworks.value = true
        const accessToken = localStorage.getItem('access_token')
        const response = await axios.get(`${API_BASE_URL}/api/frameworks/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          }
        })

        if (Array.isArray(response.data)) {
          frameworks.value = response.data.map(fw => ({
            id: fw.FrameworkId || fw.id,
            name: fw.FrameworkName || fw.name
          }))
        } else if (response.data.frameworks) {
          frameworks.value = response.data.frameworks.map(fw => ({
            id: fw.FrameworkId || fw.id,
            name: fw.FrameworkName || fw.name
          }))
        }
      } catch (err) {
        console.error('Error fetching frameworks:', err)
      } finally {
        loadingFrameworks.value = false
      }
    }

    const fetchData = async () => {
      try {
        loading.value = true
        error.value = null

        let frameworkId = selectedFrameworkId.value
        
        // Handle "all" frameworks case
        if (frameworkId === 'all' || frameworkId === null || frameworkId === undefined) {
          frameworkId = null
        }

        const url = API_ENDPOINTS.DATA_ANALYSIS(frameworkId)
        const accessToken = localStorage.getItem('access_token')

        const response = await axios.get(url, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.data && response.data.status === 'success') {
          data.value = response.data.data
        } else {
          throw new Error(response.data?.message || 'Failed to fetch data analysis')
        }
      } catch (err) {
        console.error('Error fetching data analysis:', err)
        error.value = err.response?.data?.message || err.message || 'Failed to load data analysis'
      } finally {
        loading.value = false
      }
    }

    const fetchPrivacyMetrics = async () => {
      try {
        let frameworkId = selectedFrameworkId.value
        if (frameworkId === 'all' || frameworkId === null || frameworkId === undefined) {
          frameworkId = null
        }

        // Prefer cached AI privacy analysis if available
        if (aiPrivacyService.hasValidCache(frameworkId)) {
          console.log('[DataAnalysis] Using cached AI privacy metrics')
          const cached = aiPrivacyService.getAnalysis(frameworkId)
          if (cached?.metrics) {
            privacyMetrics.value = cached.metrics
          }
          return
        }

        console.log('[DataAnalysis] No cached AI privacy metrics, fetching via service...')
        const data = await aiPrivacyService.fetchAnalysis(frameworkId)
        if (data?.metrics) {
          privacyMetrics.value = data.metrics
        }
      } catch (err) {
        console.error('Error fetching privacy metrics:', err)
        // Keep existing values (defaults) on error
      }
    }

    const onFrameworkChange = () => {
      fetchData()
      fetchPrivacyMetrics()
    }

    let tooltipTimeout = null
    let positionUpdateFrame = null

    const showTooltip = (event, category, columns) => {
      // Clear any pending hide timeout
      if (tooltipTimeout) {
        clearTimeout(tooltipTimeout)
        tooltipTimeout = null
      }
      
      // Cancel any pending position update
      if (positionUpdateFrame) {
        cancelAnimationFrame(positionUpdateFrame)
        positionUpdateFrame = null
      }
      
      tooltip.value = {
        visible: true,
        category: category.charAt(0).toUpperCase() + category.slice(1),
        columns: columns,
        x: event.clientX,
        y: event.clientY
      }
    }

    const updateTooltipPosition = (event) => {
      if (tooltip.value.visible) {
        // Use requestAnimationFrame for smooth position updates
        if (positionUpdateFrame) {
          cancelAnimationFrame(positionUpdateFrame)
        }
        positionUpdateFrame = requestAnimationFrame(() => {
          tooltip.value.x = event.clientX
          tooltip.value.y = event.clientY
          positionUpdateFrame = null
        })
      }
    }

    const hideTooltip = () => {
      // Cancel any pending position updates
      if (positionUpdateFrame) {
        cancelAnimationFrame(positionUpdateFrame)
        positionUpdateFrame = null
      }
      // Add small delay to prevent flickering when moving between segments
      if (tooltipTimeout) {
        clearTimeout(tooltipTimeout)
      }
      tooltipTimeout = setTimeout(() => {
        tooltip.value.visible = false
        tooltipTimeout = null
      }, 150)
    }

    const getCategoryIcon = (category) => {
      const icons = {
        'Personal': 'fas fa-user-shield',
        'Regular': 'fas fa-file-alt',
        'Confidential': 'fas fa-lock'
      }
      return icons[category] || 'fas fa-info-circle'
    }

    // Watch for framework changes
    watch(selectedFrameworkId, () => {
      fetchData()
      fetchPrivacyMetrics()
    })

    const formatModuleName = (name) => {
      return name.charAt(0).toUpperCase() + name.slice(1)
    }

    const getModuleIcon = (moduleName) => {
      const icons = {
        policy: 'fas fa-file-alt',
        compliance: 'fas fa-check-circle',
        audit: 'fas fa-clipboard-check',
        incident: 'fas fa-exclamation-circle',
        risk: 'fas fa-exclamation-triangle',
        event: 'fas fa-calendar-alt'
      }
      return icons[moduleName] || 'fas fa-folder'
    }

    onMounted(async () => {
      await fetchFrameworks()
      await fetchData()
      await fetchPrivacyMetrics()
    })

    return {
      loading,
      error,
      modules,
      overallStats,
      frameworks,
      loadingFrameworks,
      selectedFrameworkId,
      tooltip,
      privacyMetrics,
      fetchData,
      fetchFrameworks,
      onFrameworkChange,
      showTooltip,
      updateTooltipPosition,
      hideTooltip,
      getCategoryIcon,
      formatModuleName,
      getModuleIcon
    }
  }
}
</script>

