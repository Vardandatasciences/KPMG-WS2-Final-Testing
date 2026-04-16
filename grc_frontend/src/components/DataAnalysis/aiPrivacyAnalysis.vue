<template>
  <div class="ai-privacy-analysis-container">
    <div class="header">
      <div class="header-content">
        <div>
          <h1 class="page-title">
            <i class="fas fa-robot"></i>
            AI-Powered Privacy Analysis
          </h1>
          <p class="page-subtitle">Comprehensive Privacy Metrics & AI-Generated Insights</p>
        </div>
        <div class="header-actions">
          <div class="framework-selector">
            <label class="framework-label">
              <i class="fas fa-filter"></i>
              Framework:
            </label>
            <div class="framework-dropdown-group">
              <CustomDropdown
                :options="frameworkOptions"
                v-model="selectedFrameworkId"
                :disabled="loadingFrameworks"
                placeholder="All Frameworks"
                :show-label="false"
                :show-search-bar="true"
              />
            </div>
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
                  :disabled="!exportFormat || loading || !analysisData || isExporting"
                  @click="handleExport"
                >
                  <i class="fas fa-download" aria-hidden="true"></i>
                  <span class="export-btn-text">{{ isExporting ? 'Exporting...' : 'Export' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Alerts Section -->
    <div v-if="alerts.length > 0" class="alerts-section">
      <div
        v-for="(alert, index) in alerts"
        :key="index"
        :class="['alert', `alert-${alert.type}`]"
      >
        <i :class="alert.icon"></i>
        <div class="alert-content">
          <strong>{{ alert.title }}</strong>
          <p>{{ alert.message }}</p>
        </div>
        <button @click="dismissAlert(index)" class="alert-close">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <div class="spinner"></div>
      <p>Analyzing privacy data with AI...</p>
      <p class="loading-subtitle">This may take a few moments</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-container">
      <i class="fas fa-exclamation-triangle"></i>
      <p>{{ error }}</p>
      <button @click="fetchAnalysis" class="retry-button">Retry</button>
    </div>

    <!-- Main Content -->
    <div v-else-if="analysisData" class="dashboard-content">
      <!-- Key Metrics Cards (reuse global KPI card styling from main.css) -->
      <div class="metrics-section kpi-grid">
        <div class="metric-card maturity kpi-card">
          <div class="metric-icon">
            <i class="fas fa-chart-line"></i>
          </div>
          <div class="metric-content">
            <h3>Maturity Score</h3>
            <div class="metric-value">
              <span class="score">{{ metrics.maturity_score }}</span>
              <span class="score-max">/ 100</span>
            </div>
            <div class="metric-progress">
              <div
                class="progress-bar"
                :style="{ width: metrics.maturity_score + '%' }"
                :class="getScoreClass(metrics.maturity_score)"
              ></div>
            </div>
            <p class="metric-label">{{ getMaturityLevel(metrics.maturity_score) }}</p>
          </div>
        </div>

        <div class="metric-card minimization kpi-card">
          <div class="metric-icon">
            <i class="fas fa-compress-arrows-alt"></i>
          </div>
          <div class="metric-content">
            <h3>Minimization Score</h3>
            <div class="metric-value">
              <span class="score">{{ metrics.minimization_score }}</span>
              <span class="score-max">/ 100</span>
            </div>
            <div class="metric-progress">
              <div
                class="progress-bar"
                :style="{ width: metrics.minimization_score + '%' }"
                :class="getScoreClass(metrics.minimization_score)"
              ></div>
            </div>
            <p class="metric-label">Data Minimization Effectiveness</p>
          </div>
        </div>

        <div class="metric-card coverage kpi-card">
          <div class="metric-icon">
            <i class="fas fa-database"></i>
          </div>
          <div class="metric-content">
            <h3>Inventory Coverage</h3>
            <div class="metric-value">
              <span class="score">{{ metrics.data_inventory_coverage }}</span>
              <span class="score-max">%</span>
            </div>
            <div class="metric-progress">
              <div
                class="progress-bar"
                :style="{ width: metrics.data_inventory_coverage + '%' }"
                :class="getScoreClass(metrics.data_inventory_coverage)"
              ></div>
            </div>
            <p class="metric-label">Modules with Data Inventory</p>
          </div>
        </div>

        <div class="metric-card consent kpi-card">
          <div class="metric-icon">
            <i class="fas fa-handshake"></i>
          </div>
          <div class="metric-content">
            <h3>Consent Rate</h3>
            <div class="metric-value">
              <span class="score">{{ consentData.consent_configuration_rate }}</span>
              <span class="score-max">%</span>
            </div>
            <div class="metric-progress">
              <div
                class="progress-bar"
                :style="{ width: consentData.consent_configuration_rate + '%' }"
                :class="getScoreClass(consentData.consent_configuration_rate)"
              ></div>
            </div>
            <p class="metric-label">Consent Management Active</p>
          </div>
        </div>
      </div>

      <!-- Data Distribution Chart -->
      <div class="chart-section">
        <div class="chart-card">
          <h3 class="chart-title">
            <i class="fas fa-chart-pie"></i>
            Data Distribution Across Modules
          </h3>
          <div class="chart-container">
            <canvas ref="distributionChart"></canvas>
          </div>
        </div>

        <div class="chart-card">
          <h3 class="chart-title">
            <i class="fas fa-chart-bar"></i>
            Module Maturity Scores
          </h3>
          <div class="chart-container">
            <canvas ref="maturityChart"></canvas>
          </div>
        </div>
      </div>

      <!-- AI Insights Section -->
      <div v-if="aiInsights" class="insights-section">
        <div v-if="aiInsights.error" class="insights-error">
          <i class="fas fa-exclamation-triangle"></i>
          <p>{{ aiInsights.error }}</p>
          <p class="error-subtitle">Basic metrics and module analysis are still available below.</p>
        </div>
        <template v-else>
        <div class="insights-header">
          <h2>
            <i class="fas fa-lightbulb"></i>
            AI-Generated Insights & Recommendations
          </h2>
          <span class="insights-badge">
            <i class="fas fa-robot"></i>
            Powered by AI
          </span>
        </div>

        <!-- Executive Summary -->
        <div v-if="aiInsights.executive_summary" class="insight-card summary">
          <h3>
            <i class="fas fa-file-alt"></i>
            Executive Summary
          </h3>
          <p>{{ aiInsights.executive_summary }}</p>
        </div>

        <!-- Key Findings -->
        <div v-if="aiInsights.key_findings && aiInsights.key_findings.length > 0" class="insight-card findings">
          <h3>
            <i class="fas fa-search"></i>
            Key Findings
          </h3>
          <ul class="findings-list">
            <li v-for="(finding, index) in aiInsights.key_findings" :key="index">
              <i class="fas fa-check-circle"></i>
              {{ finding }}
            </li>
          </ul>
        </div>

        <!-- Strengths & Weaknesses -->
        <div class="insights-grid">
          <div v-if="aiInsights.strengths && aiInsights.strengths.length > 0" class="insight-card strengths">
            <h3>
              <i class="fas fa-thumbs-up"></i>
              Strengths
            </h3>
            <ul class="strengths-list">
              <li v-for="(strength, index) in aiInsights.strengths" :key="index">
                <i class="fas fa-check"></i>
                {{ strength }}
              </li>
            </ul>
          </div>

          <div v-if="aiInsights.weaknesses && aiInsights.weaknesses.length > 0" class="insight-card weaknesses">
            <h3>
              <i class="fas fa-exclamation-triangle"></i>
              Areas for Improvement
            </h3>
            <ul class="weaknesses-list">
              <li v-for="(weakness, index) in aiInsights.weaknesses" :key="index">
                <i class="fas fa-times"></i>
                {{ weakness }}
              </li>
            </ul>
          </div>
        </div>

        <!-- Recommendations -->
        <div v-if="aiInsights.recommendations && aiInsights.recommendations.length > 0" class="insight-card recommendations">
          <h3>
            <i class="fas fa-tasks"></i>
            Prioritized Recommendations
          </h3>
          <div class="recommendations-list">
            <div
              v-for="(rec, index) in aiInsights.recommendations"
              :key="index"
              :class="['recommendation-item', `priority-${rec.priority}`]"
            >
              <div class="rec-header">
                <span class="priority-badge" :class="`badge-${rec.priority}`">
                  {{ rec.priority.toUpperCase() }}
                </span>
                <span class="category-badge">{{ rec.category }}</span>
              </div>
              <h4>{{ rec.title }}</h4>
              <p>{{ rec.description }}</p>
              <div class="rec-impact">
                <strong>Expected Impact:</strong> {{ rec.impact }}
              </div>
            </div>
          </div>
        </div>

        <!-- Risk Assessment -->
        <div v-if="aiInsights.risk_assessment" class="insight-card risk">
          <h3>
            <i class="fas fa-shield-alt"></i>
            Risk Assessment
          </h3>
          <div class="risk-level" :class="`risk-${aiInsights.risk_assessment.overall_risk_level}`">
            <span class="risk-label">Overall Risk Level:</span>
            <span class="risk-value">{{ aiInsights.risk_assessment.overall_risk_level.toUpperCase() }}</span>
          </div>
          <div v-if="aiInsights.risk_assessment.risk_factors" class="risk-factors">
            <h4>Risk Factors:</h4>
            <ul>
              <li v-for="(factor, index) in aiInsights.risk_assessment.risk_factors" :key="index">
                {{ factor }}
              </li>
            </ul>
          </div>
          <div v-if="aiInsights.risk_assessment.compliance_gaps" class="compliance-gaps">
            <h4>Compliance Gaps:</h4>
            <ul>
              <li v-for="(gap, index) in aiInsights.risk_assessment.compliance_gaps" :key="index">
                {{ gap }}
              </li>
            </ul>
          </div>
        </div>

        <!-- Next Steps -->
        <div v-if="aiInsights.next_steps && aiInsights.next_steps.length > 0" class="insight-card next-steps">
          <h3>
            <i class="fas fa-arrow-right"></i>
            Recommended Next Steps
          </h3>
          <ol class="steps-list">
            <li v-for="(step, index) in aiInsights.next_steps" :key="index">
              {{ step }}
            </li>
          </ol>
        </div>
        </template>
      </div>

      <!-- Field Miscategorization Analysis Section -->
      <div v-if="miscategorizations.length > 0" class="miscategorizations-section">
        <div class="section-header">
          <h2>
            <i class="fas fa-exclamation-triangle"></i>
            Field Classification Issues Detected
          </h2>
          <span class="count-badge">{{ miscategorizations.length }} Issue{{ miscategorizations.length !== 1 ? 's' : '' }}</span>
        </div>
        <p class="section-description">
          AI analysis has identified potential miscategorizations of data fields. Review these recommendations to ensure proper data classification for privacy compliance.
        </p>
        <div class="miscategorizations-list">
          <div
            v-for="(miscat, index) in miscategorizations"
            :key="index"
            :class="['miscat-card', `risk-${miscat.risk_level}`]"
          >
            <div class="miscat-header">
              <div class="miscat-field-info">
                <h4>
                  <i class="fas fa-tag"></i>
                  {{ miscat.field_name }}
                </h4>
                <span class="module-badge">{{ miscat.module }}</span>
              </div>
              <div class="miscat-badges">
                <span class="confidence-badge" :class="`confidence-${miscat.confidence}`">
                  {{ miscat.confidence }} Confidence
                </span>
                <span class="risk-badge" :class="`risk-${miscat.risk_level}`">
                  {{ miscat.risk_level.toUpperCase() }} Risk
                </span>
              </div>
            </div>
            <div class="miscat-classification">
              <div class="classification-current">
                <span class="label">Current:</span>
                <span class="value" :class="`classification-${miscat.current_classification}`">
                  {{ miscat.current_classification.toUpperCase() }}
                </span>
              </div>
              <i class="fas fa-arrow-right"></i>
              <div class="classification-suggested">
                <span class="label">Suggested:</span>
                <span class="value" :class="`classification-${miscat.suggested_classification}`">
                  {{ miscat.suggested_classification.toUpperCase() }}
                </span>
              </div>
            </div>
            <div class="miscat-details">
              <div class="miscat-reason">
                <strong><i class="fas fa-info-circle"></i> Reason:</strong>
                <p>{{ miscat.reason }}</p>
              </div>
              <div class="miscat-recommendation">
                <strong><i class="fas fa-lightbulb"></i> Recommendation:</strong>
                <p>{{ miscat.recommendation }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Module Breakdown -->
      <div class="module-breakdown-section">
        <h2>
          <i class="fas fa-layer-group"></i>
          Module-Level Analysis
        </h2>
        <div class="modules-grid">
          <div
            v-for="(module, moduleName) in moduleBreakdown"
            :key="moduleName"
            class="module-card"
          >
            <div class="module-header">
              <h3>
                <i :class="getModuleIcon(moduleName)"></i>
                {{ formatModuleName(moduleName) }}
              </h3>
            </div>
            <div class="module-metrics">
              <div class="module-metric">
                <span class="metric-label">Maturity:</span>
                <span class="metric-value" :class="getScoreClass(module.maturity)">
                  {{ module.maturity }}
                </span>
              </div>
              <div class="module-metric">
                <span class="metric-label">Minimization:</span>
                <span class="metric-value" :class="getScoreClass(module.minimization)">
                  {{ module.minimization }}
                </span>
              </div>
              <div class="module-metric">
                <span class="metric-label">Coverage:</span>
                <span class="metric-value" :class="getScoreClass(module.coverage)">
                  {{ module.coverage }}%
                </span>
              </div>
            </div>
            <div class="module-data">
              <div class="data-item">
                <span>Personal Data:</span>
                <strong>{{ typeof module.personal_percentage === 'number' ? module.personal_percentage.toFixed(2) : module.personal_percentage }}%</strong>
              </div>
              <div class="data-item">
                <span>Confidential Data:</span>
                <strong>{{ typeof module.confidential_percentage === 'number' ? module.confidential_percentage.toFixed(2) : module.confidential_percentage }}%</strong>
              </div>
              <div class="data-item">
                <span>Total Records:</span>
                <strong>{{ module.total_records || 0 }}</strong>
              </div>
              <div class="data-item">
                <span>Total Fields:</span>
                <strong>{{ module.total_fields || 0 }}</strong>
              </div>
            </div>
          </div>
        </div>
        <div v-if="Object.keys(moduleBreakdown).length === 0" class="no-modules-message">
          <i class="fas fa-info-circle"></i>
          <p>No modules with data inventory found. Configure data inventory for modules to see analysis.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../../config/api.js'
import { Chart, registerables } from 'chart.js'
import CustomDropdown from '@/components/CustomDropdown.vue'
import './aiPrivacyAnalysis.css'
import aiPrivacyService from '@/services/aiPrivacyService' // NEW: centralized AI privacy cache

// Register Chart.js components
if (registerables && registerables.length > 0) {
  Chart.register(...registerables)
}

export default {
  name: 'AIPrivacyAnalysis',
  components: { CustomDropdown },
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const analysisData = ref(null)
    const frameworks = ref([])
    const loadingFrameworks = ref(false)
    const selectedFrameworkId = ref('all')
    const alerts = ref([])
    const distributionChart = ref(null)
    const maturityChart = ref(null)
    let distributionChartInstance = null
    let maturityChartInstance = null

    const exportFormat = ref('')
    const exportFormatOptions = [
      { value: '', label: 'Select format' },
      { value: 'pdf', label: 'PDF (.pdf)' },
      { value: 'excel', label: 'Excel (.xlsx)' }
    ]
    const isExportDropdownOpen = ref(false)
    const exportSelectRef = ref(null)
    const isExporting = ref(false)

    const exportFormatLabel = computed(() => {
      const match = exportFormatOptions.find(opt => opt.value === exportFormat.value)
      return match ? match.label : 'Select format'
    })

    const frameworkOptions = computed(() => [
      { value: 'all', label: 'All Frameworks' },
      ...frameworks.value.map(f => ({ value: f.id, label: f.name }))
    ])

    const metrics = computed(() => {
      return analysisData.value?.metrics || {
        maturity_score: 0,
        minimization_score: 0,
        data_inventory_coverage: 0
      }
    })

    const consentData = computed(() => {
      return analysisData.value?.consent_data || {
        consent_configuration_rate: 0
      }
    })

    const aiInsights = computed(() => {
      return analysisData.value?.ai_insights || null
    })

    const miscategorizations = computed(() => {
      if (!aiInsights.value || !aiInsights.value.miscategorizations) {
        return []
      }
      return aiInsights.value.miscategorizations || []
    })

    const moduleBreakdown = computed(() => {
      const modules = analysisData.value?.privacy_data?.modules || {}
      const moduleScores = analysisData.value?.metrics?.module_scores || {}
      const breakdown = {}
      
      // Only include modules that have data inventory
      const modulesWithInventory = analysisData.value?.privacy_data?.modules_with_inventory || []
      
      for (const moduleName of modulesWithInventory) {
        const moduleData = modules[moduleName] || {}
        const scores = moduleScores[moduleName] || {}
        
        breakdown[moduleName] = {
          maturity: scores.maturity || 0,
          minimization: scores.minimization || 0,
          coverage: scores.coverage || 0,
          personal_percentage: moduleData.personal_percentage || 0,
          confidential_percentage: moduleData.confidential_percentage || 0,
          total_records: moduleData.total_records || 0,
          total_fields: moduleData.total_fields || 0
        }
      }
      
      return breakdown
    })

    const fetchFrameworks = async () => {
      try {
        loadingFrameworks.value = true
        const isLoggedIn = (sessionStorage.getItem('is_logged_in') || localStorage.getItem('is_logged_in')) === 'true'
        const hasAuthFlag = (sessionStorage.getItem('isAuthenticated') || localStorage.getItem('isAuthenticated')) === 'true'
        
        if (!isLoggedIn && !hasAuthFlag) {
          console.log('[AI Privacy] User not authenticated - skipping frameworks fetch')
          return
        }

        const response = await axios.get(`${API_BASE_URL}/api/frameworks/`, {
          headers: {
            'Content-Type': 'application/json'
          },
          withCredentials: true
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

    const fetchAnalysis = async () => {
      try {
        loading.value = true
        error.value = null

        let frameworkId = selectedFrameworkId.value
        if (frameworkId === 'all' || frameworkId === null || frameworkId === undefined) {
          frameworkId = null
        }

        // 1) Try to use cached analysis from the shared AI privacy service
        if (aiPrivacyService.hasValidCache(frameworkId)) {
          console.log('[AI Privacy] Using cached analysis data')
          const cachedData = aiPrivacyService.getAnalysis(frameworkId)
          if (cachedData) {
            analysisData.value = cachedData
            checkAlerts(cachedData)
            await nextTick()
            setTimeout(() => {
              renderCharts()
            }, 100)
            return
          }
        }

        // 2) If no cache, trigger fetch via the shared service
        console.log('[AI Privacy] No valid cache, fetching from API via service...')
        const data = await aiPrivacyService.fetchAnalysis(frameworkId)
        analysisData.value = data
        checkAlerts(data)

        // Wait for DOM to be ready before rendering charts
        await nextTick()
        setTimeout(() => {
          renderCharts()
        }, 100)
      } catch (err) {
        console.error('Error fetching AI analysis:', err)
        error.value = err.response?.data?.message || err.message || 'Failed to load AI analysis'
      } finally {
        loading.value = false
      }
    }

    const checkAlerts = (data) => {
      alerts.value = []
      const metrics = data.metrics || {}
      const consent = data.consent_data || {}

      // Maturity score alert
      if (metrics.maturity_score < 50) {
        alerts.value.push({
          type: 'critical',
          icon: 'fas fa-exclamation-circle',
          title: 'Low Maturity Score',
          message: `Your privacy maturity score is ${metrics.maturity_score}. Immediate action recommended.`
        })
      } else if (metrics.maturity_score < 70) {
        alerts.value.push({
          type: 'warning',
          icon: 'fas fa-exclamation-triangle',
          title: 'Maturity Score Needs Improvement',
          message: `Your privacy maturity score is ${metrics.maturity_score}. Consider implementing recommendations.`
        })
      }

      // Minimization score alert
      if (metrics.minimization_score < 50) {
        alerts.value.push({
          type: 'warning',
          icon: 'fas fa-compress-arrows-alt',
          title: 'Data Minimization Concerns',
          message: `High percentage of sensitive data detected. Minimization score: ${metrics.minimization_score}`
        })
      }

      // Coverage alert
      if (metrics.data_inventory_coverage < 50) {
        alerts.value.push({
          type: 'info',
          icon: 'fas fa-database',
          title: 'Low Data Inventory Coverage',
          message: `Only ${metrics.data_inventory_coverage}% of modules have data inventory configured.`
        })
      }

      // Consent rate alert
      if (consent.consent_configuration_rate < 50) {
        alerts.value.push({
          type: 'warning',
          icon: 'fas fa-handshake',
          title: 'Low Consent Management Rate',
          message: `Only ${consent.consent_configuration_rate}% of consent configurations are enabled. Consider reviewing consent settings.`
        })
      }

      // Risk assessment alerts
      if (data.ai_insights?.risk_assessment) {
        const riskLevel = data.ai_insights.risk_assessment.overall_risk_level
        if (riskLevel === 'high' || riskLevel === 'critical') {
          alerts.value.push({
            type: 'critical',
            icon: 'fas fa-shield-alt',
            title: 'High Risk Detected',
            message: 'AI analysis indicates high privacy risk. Review recommendations immediately.'
          })
        }
      }

      // Miscategorization alerts
      if (data.ai_insights?.miscategorizations && data.ai_insights.miscategorizations.length > 0) {
        const highRiskMiscats = data.ai_insights.miscategorizations.filter(
          m => m.risk_level === 'high' || m.risk_level === 'critical'
        )
        if (highRiskMiscats.length > 0) {
          alerts.value.push({
            type: 'critical',
            icon: 'fas fa-exclamation-triangle',
            title: 'Field Classification Issues',
            message: `AI detected ${highRiskMiscats.length} high-risk field miscategorization${highRiskMiscats.length !== 1 ? 's' : ''}. Review the miscategorization analysis section.`
          })
        } else if (data.ai_insights.miscategorizations.length > 0) {
          alerts.value.push({
            type: 'warning',
            icon: 'fas fa-tag',
            title: 'Field Classification Review Needed',
            message: `AI detected ${data.ai_insights.miscategorizations.length} potential field classification issue${data.ai_insights.miscategorizations.length !== 1 ? 's' : ''}. Review recommendations below.`
          })
        }
      }
    }

    const dismissAlert = (index) => {
      alerts.value.splice(index, 1)
    }

    const renderCharts = () => {
      if (!analysisData.value || !analysisData.value.privacy_data) {
        console.warn('No privacy data available for charts')
        return
      }

      try {
        // Data Distribution Chart
        if (distributionChart.value) {
          if (distributionChartInstance) {
            distributionChartInstance.destroy()
            distributionChartInstance = null
          }

          const privacyData = analysisData.value.privacy_data
          
          // Check if we have data to display
          const totalData = (privacyData.personal_data_count || 0) + 
                           (privacyData.regular_data_count || 0) + 
                           (privacyData.confidential_data_count || 0)
          
          if (totalData === 0) {
            console.warn('No data available for distribution chart')
            return
          }

          const ctx = distributionChart.value.getContext('2d')
          if (!ctx) {
            console.error('Could not get canvas context for distribution chart')
            return
          }

          distributionChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
              labels: ['Personal Data', 'Regular Data', 'Confidential Data'],
              datasets: [{
                data: [
                  privacyData.personal_data_count || 0,
                  privacyData.regular_data_count || 0,
                  privacyData.confidential_data_count || 0
                ],
                backgroundColor: ['#81C784', '#64B5F6', '#E57373'],
                borderWidth: 2,
                borderColor: '#fff'
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  position: 'bottom'
                },
                tooltip: {
                  callbacks: {
                    label: function(context) {
                      const total = context.dataset.data.reduce((a, b) => a + b, 0)
                      const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(2) : 0
                      return `${context.label}: ${context.parsed} fields (${percentage}%)`
                    }
                  }
                }
              }
            }
          })
        }
      } catch (error) {
        console.error('Error rendering distribution chart:', error)
      }

      try {
        // Module Maturity Chart
        if (maturityChart.value) {
          if (maturityChartInstance) {
            maturityChartInstance.destroy()
            maturityChartInstance = null
          }

          const modules = analysisData.value.privacy_data.modules || {}
          const modulesWithInventory = analysisData.value.privacy_data.modules_with_inventory || []
          const moduleScores = analysisData.value.metrics?.module_scores || {}
          
          const moduleNames = Object.keys(modules).filter(name => 
            modulesWithInventory.includes(name)
          )
          
          if (moduleNames.length === 0) {
            console.warn('No modules with inventory for maturity chart')
            return
          }
          
          const maturityScores = moduleNames.map(name => 
            moduleScores[name]?.maturity || 0
          )

          const ctx = maturityChart.value.getContext('2d')
          if (!ctx) {
            console.error('Could not get canvas context for maturity chart')
            return
          }

          maturityChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
              labels: moduleNames.map(formatModuleName),
              datasets: [{
                label: 'Maturity Score',
                data: maturityScores,
                backgroundColor: maturityScores.map(score => {
                  if (score >= 70) return '#81C784'
                  if (score >= 50) return '#FFB74D'
                  return '#E57373'
                }),
                borderColor: '#fff',
                borderWidth: 2
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              scales: {
                y: {
                  beginAtZero: true,
                  max: 100,
                  ticks: {
                    callback: function(value) {
                      return value + '%'
                    }
                  }
                }
              },
              plugins: {
                legend: {
                  display: false
                },
                tooltip: {
                  callbacks: {
                    label: function(context) {
                      return `Maturity: ${context.parsed.y}%`
                    }
                  }
                }
              }
            }
          })
        }
      } catch (error) {
        console.error('Error rendering maturity chart:', error)
      }
    }

    const onFrameworkChange = () => {
      fetchAnalysis()
    }

    const selectExportFormatOption = (opt) => {
      exportFormat.value = opt.value
      isExportDropdownOpen.value = false
    }

    const handleExport = () => {
      if (!exportFormat.value) return
      exportReport(exportFormat.value)
    }

    const exportReport = async (format) => {
      try {
        isExporting.value = true
        let frameworkId = selectedFrameworkId.value
        if (frameworkId === 'all' || frameworkId === null || frameworkId === undefined) {
          frameworkId = null
        }

        const params = new URLSearchParams()
        params.append('format', format)
        if (frameworkId) params.append('framework_id', frameworkId)
        params.append('include_ai', 'true')

        const url = `${API_BASE_URL}/api/export-privacy-report/?${params.toString()}`

        const response = await axios.get(url, {
          withCredentials: true,
          responseType: 'blob'
        })

        // Create blob and download
        const blob = new Blob([response.data], {
          type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        const url_blob = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url_blob
        link.download = `privacy_compliance_report_${new Date().toISOString().split('T')[0]}.${format === 'pdf' ? 'pdf' : 'xlsx'}`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url_blob)
      } catch (err) {
        console.error('Error exporting report:', err)
        alert('Failed to export report. Please try again.')
      }
    }

    const getScoreClass = (score) => {
      if (score >= 70) return 'score-high'
      if (score >= 50) return 'score-medium'
      return 'score-low'
    }

    const getMaturityLevel = (score) => {
      if (score >= 80) return 'Optimizing'
      if (score >= 60) return 'Managed'
      if (score >= 40) return 'Defined'
      if (score >= 20) return 'Developing'
      return 'Initial'
    }

    const formatModuleName = (name) => {
      return name.split('_').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1)
      ).join(' ')
    }

    const getModuleIcon = (moduleName) => {
      const icons = {
        policy: 'fas fa-file-alt',
        compliance: 'fas fa-check-circle',
        audit: 'fas fa-clipboard-check',
        incident: 'fas fa-exclamation-circle',
        risk: 'fas fa-exclamation-triangle',
        risk_instance: 'fas fa-exclamation-triangle',
        event: 'fas fa-calendar-alt'
      }
      return icons[moduleName] || 'fas fa-folder'
    }

    watch(selectedFrameworkId, () => {
      fetchAnalysis()
    })

    watch(analysisData, () => {
      if (analysisData.value) {
        nextTick(() => {
          setTimeout(() => {
            renderCharts()
          }, 200)
        })
      }
    }, { deep: true })

    const exportDropdownClickOutside = (e) => {
      if (exportSelectRef.value && !exportSelectRef.value.contains(e.target)) {
        isExportDropdownOpen.value = false
      }
    }

    onMounted(async () => {
      await fetchFrameworks()
      await fetchAnalysis()
      document.addEventListener('click', exportDropdownClickOutside)
    })

    onBeforeUnmount(() => {
      document.removeEventListener('click', exportDropdownClickOutside)
    })

    return {
      loading,
      error,
      analysisData,
      metrics,
      consentData,
      aiInsights,
      miscategorizations,
      moduleBreakdown,
      frameworkOptions,
      frameworks,
      loadingFrameworks,
      selectedFrameworkId,
      alerts,
      distributionChart,
      maturityChart,
      fetchAnalysis,
      onFrameworkChange,
      exportFormat,
      exportFormatOptions,
      exportFormatLabel,
      isExportDropdownOpen,
      selectExportFormatOption,
      handleExport,
      exportReport,
      isExporting,
      dismissAlert,
      getScoreClass,
      getMaturityLevel,
      formatModuleName,
      getModuleIcon
    }
  }
}
</script>

