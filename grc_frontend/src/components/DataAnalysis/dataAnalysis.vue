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
          :class="{ 'module-card-selected': selectedModule === moduleName }"
          @click="selectModule(moduleName)"
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
                    />
                  </svg>
                  <div class="pie-center">
                    <span class="pie-total">{{ module.total_fields }}</span>
                    <span class="pie-label">Fields</span>
                  </div>
                </div>
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

      <!-- Detailed Module Report -->
      <div v-if="selectedModule" class="module-report-section">
        <div class="report-header">
          <h2 class="report-title">
            <i :class="getModuleIcon(selectedModule)"></i>
            {{ formatModuleName(selectedModule) }} - Detailed Report
          </h2>
          <button @click="closeReport" class="close-report-btn">
            <i class="fas fa-times"></i>
            Close
          </button>
        </div>

        <div class="report-content">
          <!-- Data Classification Columns -->
          <div class="report-section">
            <h3 class="report-section-title">
              <i class="fas fa-columns"></i>
              Data Classification Columns
            </h3>
            <div class="columns-grid">
              <div class="column-category" v-if="selectedModuleData.columns?.personal?.length > 0">
                <div class="column-category-header personal">
                  <i class="fas fa-user-shield"></i>
                  <span>Personal Data ({{ selectedModuleData.columns.personal.length }} columns)</span>
                </div>
                <div class="column-list">
                  <div
                    v-for="(column, index) in selectedModuleData.columns.personal"
                    :key="index"
                    class="column-item"
                  >
                    <i class="fas fa-chevron-right"></i>
                    {{ column }}
                  </div>
                </div>
              </div>

              <div class="column-category" v-if="selectedModuleData.columns?.regular?.length > 0">
                <div class="column-category-header regular">
                  <i class="fas fa-file-alt"></i>
                  <span>Regular Data ({{ selectedModuleData.columns.regular.length }} columns)</span>
                </div>
                <div class="column-list">
                  <div
                    v-for="(column, index) in selectedModuleData.columns.regular"
                    :key="index"
                    class="column-item"
                  >
                    <i class="fas fa-chevron-right"></i>
                    {{ column }}
                  </div>
                </div>
              </div>

              <div class="column-category" v-if="selectedModuleData.columns?.confidential?.length > 0">
                <div class="column-category-header confidential">
                  <i class="fas fa-lock"></i>
                  <span>Confidential Data ({{ selectedModuleData.columns.confidential.length }} columns)</span>
                </div>
                <div class="column-list">
                  <div
                    v-for="(column, index) in selectedModuleData.columns.confidential"
                    :key="index"
                    class="column-item"
                  >
                    <i class="fas fa-chevron-right"></i>
                    {{ column }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- AI Privacy Metrics -->
          <div class="report-section">
            <h3 class="report-section-title">
              <i class="fas fa-robot"></i>
              AI Privacy Metrics
            </h3>
            <div class="ai-metrics-grid">
              <div class="ai-metric-card">
                <div class="ai-metric-icon maturity">
                  <i class="fas fa-chart-line"></i>
                </div>
                <div class="ai-metric-content">
                  <h4>Maturity Score</h4>
                  <p class="ai-metric-value">
                    {{ moduleAiMetrics.maturity != null ? moduleAiMetrics.maturity : 'N/A' }}
                    <span v-if="moduleAiMetrics.maturity != null">/ 100</span>
                  </p>
                  <p class="ai-metric-description">
                    Measures overall privacy maturity based on data inventory coverage and classification quality
                  </p>
                </div>
              </div>

              <div class="ai-metric-card">
                <div class="ai-metric-icon minimization">
                  <i class="fas fa-compress-arrows-alt"></i>
                </div>
                <div class="ai-metric-content">
                  <h4>Minimization Score</h4>
                  <p class="ai-metric-value">
                    {{ moduleAiMetrics.minimization != null ? moduleAiMetrics.minimization : 'N/A' }}
                    <span v-if="moduleAiMetrics.minimization != null">/ 100</span>
                  </p>
                  <p class="ai-metric-description">
                    Higher score indicates better data minimization (less sensitive data relative to regular data)
                  </p>
                </div>
              </div>

              <div class="ai-metric-card">
                <div class="ai-metric-icon coverage">
                  <i class="fas fa-database"></i>
                </div>
                <div class="ai-metric-content">
                  <h4>Coverage Score</h4>
                  <p class="ai-metric-value">
                    {{ moduleAiMetrics.coverage != null ? moduleAiMetrics.coverage : 'N/A' }}
                    <span v-if="moduleAiMetrics.coverage != null">%</span>
                  </p>
                  <p class="ai-metric-description">
                    Percentage of records in this module with data inventory configured
                  </p>
                </div>
              </div>
            </div>

            <!-- AI Recommendations to Improve Scores -->
            <div v-if="moduleRecommendations.length > 0" class="ai-recommendations-section">
              <h4 class="recommendations-title">
                <i class="fas fa-lightbulb"></i>
                AI Recommendations to Improve Scores
              </h4>
              <div class="recommendations-list">
                <div
                  v-for="(rec, index) in moduleRecommendations"
                  :key="index"
                  :class="['recommendation-card', getPriorityClass(rec.priority)]"
                >
                  <div class="recommendation-header">
                    <div class="recommendation-priority-badge" :class="getPriorityClass(rec.priority)">
                      <i :class="rec.priority === 'high' || rec.priority === 'critical' ? 'fas fa-exclamation-circle' : 'fas fa-info-circle'"></i>
                      {{ rec.priority?.toUpperCase() || 'MEDIUM' }} PRIORITY
                    </div>
                    <span class="recommendation-category">{{ rec.category?.replace('_', ' ') || 'General' }}</span>
                  </div>
                  <h5 class="recommendation-title">{{ rec.title }}</h5>
                  <p class="recommendation-description">{{ rec.description }}</p>
                  <div v-if="rec.impact" class="recommendation-impact">
                    <i class="fas fa-chart-line"></i>
                    <strong>Expected Impact:</strong> {{ rec.impact }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Miscategorized Columns -->
            <div v-if="moduleMiscategorizations.length > 0" class="miscategorizations-section">
              <h4 class="miscategorizations-title">
                <i class="fas fa-exclamation-triangle"></i>
                Miscategorized Columns Detected
                <span class="miscat-count-badge">{{ moduleMiscategorizations.length }}</span>
              </h4>
              <p class="miscategorizations-description">
                AI analysis has identified potential miscategorizations in this module. Review and update these field classifications to improve accuracy and compliance.
              </p>
              <div class="miscategorizations-list">
                <div
                  v-for="(miscat, index) in moduleMiscategorizations"
                  :key="index"
                  :class="['miscat-card', getRiskClass(miscat.risk_level)]"
                >
                  <div class="miscat-header">
                    <div class="miscat-field-name">
                      <i class="fas fa-tag"></i>
                      <strong>{{ miscat.field_name }}</strong>
                    </div>
                    <div class="miscat-risk-badge" :class="getRiskClass(miscat.risk_level)">
                      {{ miscat.risk_level?.toUpperCase() || 'MEDIUM' }} RISK
                    </div>
                  </div>
                  <div class="miscat-classification-change">
                    <div class="classification-badge current" :style="{ backgroundColor: getClassificationColor(miscat.current_classification) + '20', color: getClassificationColor(miscat.current_classification), borderColor: getClassificationColor(miscat.current_classification) }">
                      <i class="fas fa-arrow-right"></i>
                      Current: {{ miscat.current_classification?.toUpperCase() || 'UNKNOWN' }}
                    </div>
                    <i class="fas fa-arrow-right classification-arrow"></i>
                    <div class="classification-badge suggested" :style="{ backgroundColor: getClassificationColor(miscat.suggested_classification) + '20', color: getClassificationColor(miscat.suggested_classification), borderColor: getClassificationColor(miscat.suggested_classification) }">
                      <i class="fas fa-check-circle"></i>
                      Suggested: {{ miscat.suggested_classification?.toUpperCase() || 'UNKNOWN' }}
                    </div>
                  </div>
                  <div class="miscat-details">
                    <div class="miscat-reason">
                      <i class="fas fa-info-circle"></i>
                      <strong>Reason:</strong> {{ miscat.reason }}
                    </div>
                    <div v-if="miscat.recommendation" class="miscat-recommendation">
                      <i class="fas fa-lightbulb"></i>
                      <strong>Action:</strong> {{ miscat.recommendation }}
                    </div>
                    <div v-if="miscat.confidence" class="miscat-confidence">
                      <i class="fas fa-certificate"></i>
                      <strong>Confidence:</strong> {{ miscat.confidence?.toUpperCase() || 'MEDIUM' }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Loading State -->
            <div v-if="loadingModuleAI" class="loading-ai-analysis">
              <div class="spinner-small"></div>
              <p>Analyzing module with AI...</p>
            </div>

            <!-- No AI Data Message -->
            <div v-if="!loadingModuleAI && moduleRecommendations.length === 0 && moduleMiscategorizations.length === 0 && moduleAiMetrics.maturity != null" class="no-ai-data-message">
              <i class="fas fa-info-circle"></i>
              <p>No specific AI recommendations or miscategorizations found for this module. The current classification appears to be accurate.</p>
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
import moduleAiAnalysisService from '@/services/moduleAiAnalysisService' // NEW: reuse module AI analysis

export default {
  name: 'DataAnalysis',
  setup() {
    const loading = ref(true)
    const error = ref(null)
    const data = ref({})
    const frameworks = ref([])
    const loadingFrameworks = ref(false)
    const selectedFrameworkId = ref('all')
    const selectedModule = ref(null)
    const moduleAiMetrics = ref({
      maturity: null,
      minimization: null,
      coverage: null
    })
    const moduleRecommendations = ref([])
    const moduleMiscategorizations = ref([])
    const loadingModuleAI = ref(false)
    const privacyMetrics = ref({
      maturity_score: 0,
      minimization_score: 0,
      data_inventory_coverage: 0
    })

    const modules = computed(() => {
      return data.value || {}
    })

    const selectedModuleData = computed(() => {
      if (!selectedModule.value || !modules.value[selectedModule.value]) {
        return {
          columns: {
            personal: [],
            regular: [],
            confidential: []
          }
        }
      }
      return modules.value[selectedModule.value]
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

    const selectModule = async (moduleName) => {
      selectedModule.value = moduleName
      loadingModuleAI.value = true
      
      // Fetch module-level AI metrics
      try {
        let frameworkId = selectedFrameworkId.value
        if (frameworkId === 'all' || frameworkId === null || frameworkId === undefined) {
          frameworkId = null
        }

        // Get AI analysis data (use cache if available)
        let aiData = null
        if (aiPrivacyService.hasValidCache(frameworkId)) {
          aiData = aiPrivacyService.getAnalysis(frameworkId)
        } else {
          aiData = await aiPrivacyService.fetchAnalysis(frameworkId)
        }

        // Extract module-level metrics
        if (aiData?.metrics?.module_scores?.[moduleName]) {
          const moduleScores = aiData.metrics.module_scores[moduleName]
          moduleAiMetrics.value = {
            maturity: moduleScores.maturity || null,
            minimization: moduleScores.minimization || null,
            coverage: moduleScores.coverage || null
          }
        } else {
          // Reset if no module scores available
          moduleAiMetrics.value = {
            maturity: null,
            minimization: null,
            coverage: null
          }
        }

        // Fetch module-specific AI analysis (recommendations and miscategorizations)
        // First try to use cached data from the service
        try {
          if (moduleAiAnalysisService.hasValidCache(moduleName, frameworkId)) {
            console.log(`[DataAnalysis] Using cached module AI analysis for ${moduleName}`)
            const cachedData = moduleAiAnalysisService.getModuleAnalysis(moduleName, frameworkId)
            if (cachedData?.ai_analysis) {
              const aiAnalysis = cachedData.ai_analysis
              moduleRecommendations.value = aiAnalysis.recommendations || []
              moduleMiscategorizations.value = aiAnalysis.miscategorizations || []
            } else {
              moduleRecommendations.value = []
              moduleMiscategorizations.value = []
            }
          } else {
            // If no cache, fetch from API via service
            console.log(`[DataAnalysis] No cached module AI analysis for ${moduleName}, fetching from API...`)
            const moduleData = await moduleAiAnalysisService.fetchModuleAnalysis(moduleName, frameworkId)
            if (moduleData?.ai_analysis) {
              const aiAnalysis = moduleData.ai_analysis
              moduleRecommendations.value = aiAnalysis.recommendations || []
              moduleMiscategorizations.value = aiAnalysis.miscategorizations || []
            } else {
              moduleRecommendations.value = []
              moduleMiscategorizations.value = []
            }
          }
        } catch (aiErr) {
          console.error('Error fetching module AI analysis:', aiErr)
          moduleRecommendations.value = []
          moduleMiscategorizations.value = []
        }
      } catch (err) {
        console.error('Error fetching module AI metrics:', err)
        moduleAiMetrics.value = {
          maturity: null,
          minimization: null,
          coverage: null
        }
        moduleRecommendations.value = []
        moduleMiscategorizations.value = []
      } finally {
        loadingModuleAI.value = false
      }
    }

    const closeReport = () => {
      selectedModule.value = null
      moduleAiMetrics.value = {
        maturity: null,
        minimization: null,
        coverage: null
      }
      moduleRecommendations.value = []
      moduleMiscategorizations.value = []
    }

    const getPriorityClass = (priority) => {
      const priorityMap = {
        'high': 'priority-high',
        'medium': 'priority-medium',
        'low': 'priority-low',
        'critical': 'priority-critical'
      }
      return priorityMap[priority?.toLowerCase()] || 'priority-medium'
    }

    const getRiskClass = (riskLevel) => {
      const riskMap = {
        'critical': 'risk-critical',
        'high': 'risk-high',
        'medium': 'risk-medium',
        'low': 'risk-low'
      }
      return riskMap[riskLevel?.toLowerCase()] || 'risk-medium'
    }

    const getClassificationColor = (classification) => {
      const colorMap = {
        'personal': '#66BB6A',
        'regular': '#64B5F6',
        'confidential': '#E57373'
      }
      return colorMap[classification?.toLowerCase()] || '#999'
    }

    const onFrameworkChange = () => {
      fetchData()
      fetchPrivacyMetrics()
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
      selectedModule,
      selectedModuleData,
      moduleAiMetrics,
      moduleRecommendations,
      moduleMiscategorizations,
      loadingModuleAI,
      privacyMetrics,
      fetchData,
      fetchFrameworks,
      onFrameworkChange,
      selectModule,
      closeReport,
      getPriorityClass,
      getRiskClass,
      getClassificationColor,
      getCategoryIcon,
      formatModuleName,
      getModuleIcon
    }
  }
}
</script>

