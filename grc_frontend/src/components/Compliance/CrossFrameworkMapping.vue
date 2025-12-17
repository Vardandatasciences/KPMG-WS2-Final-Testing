<template>
  <div class="cross-framework-mapping-container">
    <!-- Header -->
    <div class="cfm-header">
      <h2 class="cfm-title">
        <i class="fas fa-code-branch"></i>
        Gap Analysis
      </h2>
      <p class="cfm-subtitle">
        Compare two versions of a framework and identify what changed
      </p>
    </div>

    <!-- Loading Overlay -->
    <div v-if="isProcessing" class="cfm-loading-overlay">
      <div class="cfm-loader">
        <div class="cfm-spinner"></div>
        <h3>{{ processingMessage }}</h3>
        <p>{{ processingSubMessage }}</p>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="cfm-error-message">
      <i class="fas fa-exclamation-circle"></i>
      <span>{{ error }}</span>
      <button @click="error = ''" class="cfm-close-btn">&times;</button>
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="cfm-success-message">
      <i class="fas fa-check-circle"></i>
      <span>{{ successMessage }}</span>
      <button @click="successMessage = ''" class="cfm-close-btn">&times;</button>
    </div>

    <!-- Debug Info -->
    <div style="background: #fff3cd; border: 2px solid #ffc107; padding: 12px; margin-bottom: 16px; border-radius: 8px;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <strong>🔍 Debug Info:</strong><br>
          Available Frameworks: {{ availableFrameworks.length }}<br>
          <template v-if="availableFrameworks.length > 0">
            <div style="max-height: 100px; overflow-y: auto; margin-top: 8px; padding: 8px; background: white; border-radius: 4px;">
              <div v-for="fw in availableFrameworks" :key="fw.framework_id" style="margin: 4px 0;">
                {{ fw.framework_id }}: {{ fw.framework_name }} ({{ fw.category }})
              </div>
            </div>
          </template>
          <template v-else>
            <span style="color: red;">No frameworks loaded! Check console for errors.</span>
          </template>
        </div>
        <button @click="loadAvailableFrameworks" class="cfm-btn cfm-btn-secondary" style="margin-left: 12px;">
          <i class="fas fa-sync"></i> Reload Frameworks
        </button>
      </div>
    </div>

    <!-- Action Bar -->
    <div class="cfm-action-bar">
      <button 
        @click="performMapping" 
        class="cfm-btn cfm-btn-primary cfm-btn-large"
        :disabled="!canPerformMapping || isProcessing"
      >
        <i class="fas fa-balance-scale"></i>
        {{ isProcessing ? 'Comparing...' : 'Compare Framework Versions' }}
      </button>
      <button 
        @click="clearAll" 
        class="cfm-btn cfm-btn-secondary"
        :disabled="isProcessing"
      >
        <i class="fas fa-redo"></i>
        Reset
      </button>
    </div>

    <!-- Split Screen Layout -->
    <div class="cfm-split-container">
      <!-- Left Panel - Framework 1 -->
      <div class="cfm-panel cfm-panel-left">
        <div class="cfm-panel-header">
          <h3>
            <i class="fas fa-shield-alt"></i>
            Version 1 (Old Version)
          </h3>
        </div>
        <div class="cfm-panel-content">
          <div class="cfm-framework-selector">
            <label>Select Framework</label>
            <select 
              v-model="framework1Id" 
              @change="loadFramework1Compliances"
              class="cfm-select"
              :disabled="isProcessing"
            >
              <option value="">Choose a framework...</option>
              <option 
                v-for="fw in availableFrameworks" 
                :key="fw.framework_id" 
                :value="fw.framework_id"
              >
                {{ fw.framework_name }}
              </option>
            </select>
          </div>

          <!-- Framework 1 Info -->
          <div v-if="framework1" class="cfm-framework-info">
            <div class="cfm-info-item">
              <span class="cfm-info-label">Category:</span>
              <span class="cfm-info-value">{{ framework1.category }}</span>
            </div>
            <div class="cfm-info-item">
              <span class="cfm-info-label">Total Controls:</span>
              <span class="cfm-info-value">{{ framework1Compliances.length }}</span>
            </div>
          </div>

          <!-- Framework 1 Compliances List -->
          <div v-if="framework1Compliances.length > 0" class="cfm-compliances-list">
            <div class="cfm-list-header">
              <h4>Compliance Controls</h4>
              <span class="cfm-count-badge">{{ framework1Compliances.length }}</span>
            </div>
            <div class="cfm-compliances-scroll">
              <div 
                v-for="(compliance, index) in framework1Compliances" 
                :key="compliance.ComplianceId"
                class="cfm-compliance-item"
                :class="{ 'cfm-compliance-selected': selectedCompliance1 === compliance.ComplianceId }"
                @click="selectCompliance1(compliance)"
              >
                <div class="cfm-compliance-number">{{ index + 1 }}</div>
                <div class="cfm-compliance-content">
                  <div class="cfm-compliance-title">
                    {{ compliance.ComplianceTitle || compliance.Identifier || `Control ${compliance.ComplianceId}` }}
                  </div>
                  <div class="cfm-compliance-desc">
                    {{ truncateText(compliance.ComplianceItemDescription, 100) }}
                  </div>
                  <div class="cfm-compliance-meta">
                    <span class="cfm-meta-badge">{{ compliance.Criticality || 'N/A' }}</span>
                    <span class="cfm-meta-badge">{{ compliance.MandatoryOptional || 'N/A' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Center Connector -->
      <div class="cfm-connector">
        <div class="cfm-connector-line"></div>
        <div class="cfm-connector-icon">
          <i class="fas fa-exchange-alt"></i>
        </div>
        <div class="cfm-connector-label">Mapping</div>
      </div>

      <!-- Right Panel - Framework 2 -->
      <div class="cfm-panel cfm-panel-right">
        <div class="cfm-panel-header">
          <h3>
            <i class="fas fa-shield-alt"></i>
            Version 2 (New Version)
          </h3>
        </div>
        <div class="cfm-panel-content">
          <div class="cfm-framework-selector">
            <label>Select Framework</label>
            <select 
              v-model="framework2Id" 
              @change="loadFramework2Compliances"
              class="cfm-select"
              :disabled="isProcessing"
            >
              <option value="">Choose a framework...</option>
              <option 
                v-for="fw in availableFrameworks" 
                :key="fw.framework_id" 
                :value="fw.framework_id"
                :disabled="fw.framework_id === framework1Id"
              >
                {{ fw.framework_name }}
              </option>
            </select>
          </div>

          <!-- Framework 2 Info -->
          <div v-if="framework2" class="cfm-framework-info">
            <div class="cfm-info-item">
              <span class="cfm-info-label">Category:</span>
              <span class="cfm-info-value">{{ framework2.category }}</span>
            </div>
            <div class="cfm-info-item">
              <span class="cfm-info-label">Total Controls:</span>
              <span class="cfm-info-value">{{ framework2Compliances.length }}</span>
            </div>
          </div>

          <!-- Framework 2 Compliances List -->
          <div v-if="framework2Compliances.length > 0" class="cfm-compliances-list">
            <div class="cfm-list-header">
              <h4>Compliance Controls</h4>
              <span class="cfm-count-badge">{{ framework2Compliances.length }}</span>
            </div>
            <div class="cfm-compliances-scroll">
              <div 
                v-for="(compliance, index) in framework2Compliances" 
                :key="compliance.ComplianceId"
                class="cfm-compliance-item"
                :class="{ 'cfm-compliance-selected': selectedCompliance2 === compliance.ComplianceId }"
                @click="selectCompliance2(compliance)"
              >
                <div class="cfm-compliance-number">{{ index + 1 }}</div>
                <div class="cfm-compliance-content">
                  <div class="cfm-compliance-title">
                    {{ compliance.ComplianceTitle || compliance.Identifier || `Control ${compliance.ComplianceId}` }}
                  </div>
                  <div class="cfm-compliance-desc">
                    {{ truncateText(compliance.ComplianceItemDescription, 100) }}
                  </div>
                  <div class="cfm-compliance-meta">
                    <span class="cfm-meta-badge">{{ compliance.Criticality || 'N/A' }}</span>
                    <span class="cfm-meta-badge">{{ compliance.MandatoryOptional || 'N/A' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Version Comparison Results Section -->
    <div v-if="mappingResults && mappingResults.length > 0" class="cfm-results-section">
      <div class="cfm-results-header">
        <h3>
          <i class="fas fa-code-branch"></i>
          Version Comparison Results
        </h3>
        <div class="cfm-results-stats">
          <span class="cfm-stat-item cfm-stat-new">
            <i class="fas fa-plus-circle"></i>
            <strong>{{ newControlsCount }}</strong> New
          </span>
          <span class="cfm-stat-item cfm-stat-modified">
            <i class="fas fa-edit"></i>
            <strong>{{ modifiedControlsCount }}</strong> Modified
          </span>
          <span class="cfm-stat-item cfm-stat-removed">
            <i class="fas fa-minus-circle"></i>
            <strong>{{ removedControlsCount }}</strong> Removed
          </span>
          <span class="cfm-stat-item cfm-stat-unchanged">
            <i class="fas fa-check-circle"></i>
            <strong>{{ unchangedControlsCount }}</strong> Unchanged
          </span>
        </div>
      </div>

      <div class="cfm-results-grid">
        <div 
          v-for="(change, index) in mappingResults" 
          :key="index"
          class="cfm-mapping-result"
          :class="getChangeClass(change.change_type)"
        >
          <!-- NEW Control -->
          <template v-if="change.change_type === 'NEW'">
            <div class="cfm-mapping-empty">
              <div class="cfm-empty-placeholder">
                <i class="fas fa-minus-circle"></i>
                <p>Not present in {{ change.framework1_name }}</p>
              </div>
            </div>
            
            <div class="cfm-mapping-arrow">
              <i class="fas fa-plus"></i>
              <div class="cfm-change-badge cfm-badge-new">
                NEW
              </div>
            </div>
            
            <div class="cfm-mapping-to">
              <div class="cfm-mapping-framework">{{ change.framework2_name }}</div>
              <div class="cfm-mapping-control">
                <span v-if="change.control2_identifier" class="cfm-control-identifier">[{{ change.control2_identifier }}]</span>
                {{ change.control2_title }}
              </div>
              <div class="cfm-mapping-description">{{ truncateText(change.control2_description, 100) }}</div>
            </div>
          </template>

          <!-- REMOVED Control -->
          <template v-else-if="change.change_type === 'REMOVED'">
            <div class="cfm-mapping-from">
              <div class="cfm-mapping-framework">{{ change.framework1_name }}</div>
              <div class="cfm-mapping-control">
                <span v-if="change.control1_identifier" class="cfm-control-identifier">[{{ change.control1_identifier }}]</span>
                {{ change.control1_title }}
              </div>
              <div class="cfm-mapping-description">{{ truncateText(change.control1_description, 100) }}</div>
            </div>
            
            <div class="cfm-mapping-arrow">
              <i class="fas fa-times"></i>
              <div class="cfm-change-badge cfm-badge-removed">
                REMOVED
              </div>
            </div>
            
            <div class="cfm-mapping-empty">
              <div class="cfm-empty-placeholder">
                <i class="fas fa-minus-circle"></i>
                <p>Not present in {{ change.framework2_name }}</p>
              </div>
            </div>
          </template>

          <!-- MODIFIED or UNCHANGED Control -->
          <template v-else>
            <div class="cfm-mapping-from">
              <div class="cfm-mapping-framework">{{ change.framework1_name }}</div>
              <div class="cfm-mapping-control">
                <span v-if="change.control1_identifier" class="cfm-control-identifier">[{{ change.control1_identifier }}]</span>
                {{ change.control1_title }}
              </div>
              <div class="cfm-mapping-description">{{ truncateText(change.control1_description, 100) }}</div>
            </div>
            
            <div class="cfm-mapping-arrow">
              <i :class="change.change_type === 'MODIFIED' ? 'fas fa-exchange-alt' : 'fas fa-equals'"></i>
              <div class="cfm-change-badge" :class="change.change_type === 'MODIFIED' ? 'cfm-badge-modified' : 'cfm-badge-unchanged'">
                {{ change.change_type }}
              </div>
            </div>
            
            <div class="cfm-mapping-to">
              <div class="cfm-mapping-framework">{{ change.framework2_name }}</div>
              <div class="cfm-mapping-control">
                <span v-if="change.control2_identifier" class="cfm-control-identifier">[{{ change.control2_identifier }}]</span>
                {{ change.control2_title }}
              </div>
              <div class="cfm-mapping-description">{{ truncateText(change.control2_description, 100) }}</div>
            </div>
          </template>

          <div v-if="change.ai_analysis" class="cfm-mapping-analysis">
            <i class="fas fa-info-circle"></i>
            <span>{{ change.ai_analysis }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { API_BASE_URL } from '../../config/api.js'

export default {
  name: 'CrossFrameworkMapping',
  data() {
    return {
      framework1Id: null,
      framework2Id: null,
      framework1: null,
      framework2: null,
      framework1Compliances: [],
      framework2Compliances: [],
      selectedCompliance1: null,
      selectedCompliance2: null,
      availableFrameworks: [],
      isProcessing: false,
      processingMessage: 'Analyzing cross-framework mappings...',
      processingSubMessage: 'This may take a few minutes',
      error: '',
      successMessage: '',
      mappingResults: []
    }
  },
  computed: {
    canPerformMapping() {
      return this.framework1Id && this.framework2Id && 
             this.framework1Compliances.length > 0 && 
             this.framework2Compliances.length > 0
    },
    newControlsCount() {
      return this.mappingResults.filter(m => m.change_type === 'NEW').length
    },
    modifiedControlsCount() {
      return this.mappingResults.filter(m => m.change_type === 'MODIFIED').length
    },
    removedControlsCount() {
      return this.mappingResults.filter(m => m.change_type === 'REMOVED').length
    },
    unchangedControlsCount() {
      return this.mappingResults.filter(m => m.change_type === 'UNCHANGED').length
    }
  },
  mounted() {
    console.log('='.repeat(80))
    console.log('🚀 CrossFrameworkMapping component mounted!')
    console.log('📍 API_BASE_URL:', API_BASE_URL)
    console.log('📍 Starting to load frameworks...')
    console.log('='.repeat(80))
    
    // Add slight delay to ensure DOM is ready
    setTimeout(() => {
      this.loadAvailableFrameworks()
    }, 100)
  },
  methods: {
    async loadAvailableFrameworks() {
      try {
        console.log('='.repeat(80))
        console.log('🔄 Loading frameworks from API...')
        console.log('🌐 URL:', `${API_BASE_URL}/api/compliance/frameworks/`)
        console.log('='.repeat(80))
        
        // Increase timeout for large datasets
        const response = await axios.get(`${API_BASE_URL}/api/compliance/frameworks/`, {
          timeout: 60000 // 60 seconds instead of default 30
        })
        
        console.log('✅ API Response received!')
        console.log('✅ Response data:', response.data)
        console.log('✅ Response status:', response.status)
        
        if (response.data.success && response.data.frameworks) {
          // Transform to expected format
          const allFrameworks = response.data.frameworks.map(fw => ({
            framework_id: fw.id,
            framework_name: fw.name,
            category: fw.category || '',
            description: fw.description || '',
            status: fw.status
          }))
          
          console.log(`📊 Total frameworks from API: ${allFrameworks.length}`)
          
          // Filter for active frameworks - check ActiveInactive field
          this.availableFrameworks = allFrameworks.filter(fw => {
            const isActive = fw.status && fw.status.toLowerCase() === 'active'
            if (!isActive) {
              console.log(`⏭️  Skipping framework "${fw.framework_name}" (status: "${fw.status}")`)
            }
            return isActive
          })
          
          console.log(`✅ Loaded ${this.availableFrameworks.length} active frameworks:`, 
            this.availableFrameworks.map(f => f.framework_name))
          
          // Fallback: if no active frameworks, show all frameworks
          if (this.availableFrameworks.length === 0) {
            console.warn('⚠️  No frameworks with status="Active" found. Showing all frameworks as fallback.')
            this.availableFrameworks = allFrameworks
            this.error = ''
          }
        } else {
          console.error('❌ Invalid response format:', response.data)
          this.error = 'Invalid response format from server'
        }
      } catch (error) {
        console.error('❌ Error loading frameworks:', error)
        console.error('❌ Error details:', error.response || error.message || error)
        this.error = `Failed to load available frameworks: ${error.message || 'Unknown error'}`
      }
    },

    async loadFramework1Compliances() {
      if (!this.framework1Id) return
      
      try {
        this.framework1 = this.availableFrameworks.find(fw => fw.framework_id === this.framework1Id)
        
        console.log(`🔍 Loading compliances for framework ${this.framework1Id}`)
        
        // Use the BRAND NEW dedicated endpoint for cross-framework mapping
        const response = await axios.get(`${API_BASE_URL}/api/cross-framework-mapping/${this.framework1Id}/`)
        if (response.data.success) {
          // Use the backend data directly - it already has the correct format
          this.framework1Compliances = response.data.compliances || []
          this.selectedCompliance1 = null
          this.mappingResults = []
        }
      } catch (error) {
        console.error('Error loading framework 1 compliances:', error)
        this.error = 'Failed to load controls for Framework 1'
      }
    },

    async loadFramework2Compliances() {
      if (!this.framework2Id) return
      
      try {
        this.framework2 = this.availableFrameworks.find(fw => fw.framework_id === this.framework2Id)
        
        console.log(`🔍 Loading compliances for framework ${this.framework2Id}`)
        
        // Use the BRAND NEW dedicated endpoint for cross-framework mapping
        const response = await axios.get(`${API_BASE_URL}/api/cross-framework-mapping/${this.framework2Id}/`)
        if (response.data.success) {
          // Use the backend data directly - it already has the correct format
          this.framework2Compliances = response.data.compliances || []
          this.selectedCompliance2 = null
          this.mappingResults = []
        }
      } catch (error) {
        console.error('Error loading framework 2 compliances:', error)
        this.error = 'Failed to load controls for Framework 2'
      }
    },

    selectCompliance1(compliance) {
      this.selectedCompliance1 = compliance.ComplianceId
    },

    selectCompliance2(compliance) {
      this.selectedCompliance2 = compliance.ComplianceId
    },

    async performMapping() {
      if (!this.canPerformMapping) {
        this.error = 'Please select both framework versions to compare'
        return
      }

      this.isProcessing = true
      this.error = ''
      this.successMessage = ''
      this.processingMessage = 'Comparing framework versions...'
      this.processingSubMessage = 'Detecting changes between versions'

      try {
        const changes = []
        
        // Create maps for quick lookup by identifier
        const v1Map = new Map()
        const v2Map = new Map()
        
        this.framework1Compliances.forEach(comp => {
          const key = (comp.Identifier || `ID_${comp.ComplianceId}`).trim()
          v1Map.set(key, comp)
        })
        
        this.framework2Compliances.forEach(comp => {
          const key = (comp.Identifier || `ID_${comp.ComplianceId}`).trim()
          v2Map.set(key, comp)
        })
        
        // 1. Find NEW controls (in V2 but not in V1)
        for (const [key, comp2] of v2Map) {
          if (!v1Map.has(key)) {
            changes.push({
              change_type: 'NEW',
              framework1_id: this.framework1Id,
              framework1_name: this.framework1.framework_name,
              framework2_id: this.framework2Id,
              framework2_name: this.framework2.framework_name,
              control2_id: comp2.ComplianceId,
              control2_title: comp2.ComplianceTitle || comp2.Identifier || `Control ${comp2.ComplianceId}`,
              control2_description: comp2.ComplianceItemDescription || '',
              control2_identifier: comp2.Identifier,
              ai_analysis: '✨ New control added in this version'
            })
          }
        }
        
        // 2. Find REMOVED controls (in V1 but not in V2)
        for (const [key, comp1] of v1Map) {
          if (!v2Map.has(key)) {
            changes.push({
              change_type: 'REMOVED',
              framework1_id: this.framework1Id,
              framework1_name: this.framework1.framework_name,
              control1_id: comp1.ComplianceId,
              control1_title: comp1.ComplianceTitle || comp1.Identifier || `Control ${comp1.ComplianceId}`,
              control1_description: comp1.ComplianceItemDescription || '',
              control1_identifier: comp1.Identifier,
              framework2_id: this.framework2Id,
              framework2_name: this.framework2.framework_name,
              ai_analysis: '🗑️ Control removed in this version'
            })
          }
        }
        
        // 3. Find MODIFIED and UNCHANGED controls (in both versions)
        for (const [key, comp1] of v1Map) {
          if (v2Map.has(key)) {
            const comp2 = v2Map.get(key)
            
            // Check if content changed
            const changes_detected = []
            
            if ((comp1.ComplianceTitle || '') !== (comp2.ComplianceTitle || '')) {
              changes_detected.push('Title changed')
            }
            if ((comp1.ComplianceItemDescription || '') !== (comp2.ComplianceItemDescription || '')) {
              changes_detected.push('Description updated')
            }
            if ((comp1.Criticality || '') !== (comp2.Criticality || '')) {
              changes_detected.push(`Criticality: ${comp1.Criticality || 'N/A'} → ${comp2.Criticality || 'N/A'}`)
            }
            if ((comp1.MandatoryOptional || '') !== (comp2.MandatoryOptional || '')) {
              changes_detected.push(`Status: ${comp1.MandatoryOptional || 'N/A'} → ${comp2.MandatoryOptional || 'N/A'}`)
            }
            if ((comp1.Scope || '') !== (comp2.Scope || '')) {
              changes_detected.push('Scope modified')
            }
            if ((comp1.Objective || '') !== (comp2.Objective || '')) {
              changes_detected.push('Objective modified')
            }
            
            if (changes_detected.length > 0) {
              changes.push({
                change_type: 'MODIFIED',
                framework1_id: this.framework1Id,
                framework1_name: this.framework1.framework_name,
                control1_id: comp1.ComplianceId,
                control1_title: comp1.ComplianceTitle || comp1.Identifier || `Control ${comp1.ComplianceId}`,
                control1_description: comp1.ComplianceItemDescription || '',
                control1_identifier: comp1.Identifier,
                framework2_id: this.framework2Id,
                framework2_name: this.framework2.framework_name,
                control2_id: comp2.ComplianceId,
                control2_title: comp2.ComplianceTitle || comp2.Identifier || `Control ${comp2.ComplianceId}`,
                control2_description: comp2.ComplianceItemDescription || '',
                control2_identifier: comp2.Identifier,
                ai_analysis: `📝 ${changes_detected.join(' • ')}`
              })
            } else {
              changes.push({
                change_type: 'UNCHANGED',
                framework1_id: this.framework1Id,
                framework1_name: this.framework1.framework_name,
                control1_id: comp1.ComplianceId,
                control1_title: comp1.ComplianceTitle || comp1.Identifier || `Control ${comp1.ComplianceId}`,
                control1_description: comp1.ComplianceItemDescription || '',
                control1_identifier: comp1.Identifier,
                framework2_id: this.framework2Id,
                framework2_name: this.framework2.framework_name,
                control2_id: comp2.ComplianceId,
                control2_title: comp2.ComplianceTitle || comp2.Identifier || `Control ${comp2.ComplianceId}`,
                control2_description: comp2.ComplianceItemDescription || '',
                control2_identifier: comp2.Identifier,
                ai_analysis: '✓ No changes detected'
              })
            }
          }
        }
        
        // Sort: NEW, MODIFIED, REMOVED, UNCHANGED
        const sortOrder = { 'NEW': 1, 'MODIFIED': 2, 'REMOVED': 3, 'UNCHANGED': 4 }
        changes.sort((a, b) => sortOrder[a.change_type] - sortOrder[b.change_type])
        
        this.mappingResults = changes
        
        const newCount = changes.filter(c => c.change_type === 'NEW').length
        const removedCount = changes.filter(c => c.change_type === 'REMOVED').length
        const modifiedCount = changes.filter(c => c.change_type === 'MODIFIED').length
        const unchangedCount = changes.filter(c => c.change_type === 'UNCHANGED').length
        
        this.successMessage = `Comparison complete: ${newCount} new, ${modifiedCount} modified, ${removedCount} removed, ${unchangedCount} unchanged`

      } catch (error) {
        console.error('Error performing comparison:', error)
        this.error = 'Failed to compare framework versions'
      } finally {
        this.isProcessing = false
      }
    },

    calculateSimilarity(comp1, comp2) {
      // Enhanced text-based similarity calculation using multiple fields
      const text1 = `${comp1.ComplianceTitle || ''} ${comp1.ComplianceItemDescription || ''} ${comp1.Scope || ''} ${comp1.Objective || ''}`.toLowerCase()
      const text2 = `${comp2.ComplianceTitle || ''} ${comp2.ComplianceItemDescription || ''} ${comp2.Scope || ''} ${comp2.Objective || ''}`.toLowerCase()
      
      // Extract keywords (words longer than 3 characters)
      const words1 = text1.split(/\s+/).filter(w => w.length > 3)
      const words2 = text2.split(/\s+/).filter(w => w.length > 3)
      
      // Remove common stop words for better matching
      const stopWords = ['that', 'this', 'with', 'from', 'have', 'been', 'will', 'shall', 'must', 'should', 'could', 'would', 'their', 'which', 'there', 'where', 'when']
      const filteredWords1 = words1.filter(w => !stopWords.includes(w))
      const filteredWords2 = words2.filter(w => !stopWords.includes(w))
      
      // Count common words
      const commonWords = filteredWords1.filter(w => filteredWords2.includes(w)).length
      const totalWords = Math.max(filteredWords1.length, filteredWords2.length)
      
      if (totalWords === 0) return 0
      
      // Base similarity from text overlap
      let similarity = (commonWords / totalWords) * 0.6 // Weight text similarity at 60%
      
      // Boost for exact identifier match (often frameworks use similar identifiers)
      if (comp1.Identifier && comp2.Identifier && 
          comp1.Identifier.toLowerCase().includes(comp2.Identifier.toLowerCase().substring(0, 3))) {
        similarity += 0.15
      }
      
      // Boost similarity if criticality matches
      if (comp1.Criticality === comp2.Criticality && comp1.Criticality) {
        similarity += 0.1
      }
      
      // Boost similarity if compliance types match
      if (comp1.ComplianceType === comp2.ComplianceType && comp1.ComplianceType) {
        similarity += 0.15
      }
      
      // Boost if both are mandatory or both optional
      if (comp1.MandatoryOptional === comp2.MandatoryOptional && comp1.MandatoryOptional) {
        similarity += 0.05
      }
      
      return Math.min(similarity, 1.0)
    },

    generateMappingReason(comp1, comp2, confidence) {
      const reasons = []
      
      if (confidence > 0.7) {
        reasons.push('High textual similarity')
      } else if (confidence > 0.5) {
        reasons.push('Moderate textual similarity')
      } else {
        reasons.push('Low textual similarity')
      }
      
      if (comp1.Criticality === comp2.Criticality && comp1.Criticality) {
        reasons.push(`Both ${comp1.Criticality} criticality`)
      }
      
      if (comp1.ComplianceType === comp2.ComplianceType && comp1.ComplianceType) {
        reasons.push(`Same type: ${comp1.ComplianceType}`)
      }
      
      return reasons.join(' • ')
    },

    clearAll() {
      this.framework1Id = null
      this.framework2Id = null
      this.framework1 = null
      this.framework2 = null
      this.framework1Compliances = []
      this.framework2Compliances = []
      this.selectedCompliance1 = null
      this.selectedCompliance2 = null
      this.mappingResults = []
      this.error = ''
      this.successMessage = ''
    },

    getChangeClass(changeType) {
      switch (changeType) {
        case 'NEW': return 'cfm-change-new'
        case 'MODIFIED': return 'cfm-change-modified'
        case 'REMOVED': return 'cfm-change-removed'
        case 'UNCHANGED': return 'cfm-change-unchanged'
        default: return ''
      }
    },

    truncateText(text, maxLength) {
      if (!text) return 'N/A'
      if (text.length <= maxLength) return text
      return text.substring(0, maxLength) + '...'
    }
  }
}
</script>

<style scoped>
.cross-framework-mapping-container {
  padding: 24px;
  margin-left: 270px;
  background: #f9fafb;
  min-height: 100vh;
}

.cfm-header {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e5e7eb;
}

.cfm-title {
  font-size: 2rem;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.cfm-title i {
  color: #3b82f6;
}

.cfm-subtitle {
  color: #6b7280;
  font-size: 1rem;
  margin: 0;
}

.cfm-action-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  justify-content: center;
}

.cfm-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.cfm-btn-primary {
  background: #3b82f6;
  color: white;
}

.cfm-btn-primary:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-2px);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.cfm-btn-secondary {
  background: #6b7280;
  color: white;
}

.cfm-btn-secondary:hover:not(:disabled) {
  background: #4b5563;
}

.cfm-btn-large {
  padding: 14px 28px;
  font-size: 1.05rem;
}

.cfm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Split Screen Layout */
.cfm-split-container {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 0;
  margin-bottom: 24px;
  min-height: 600px;
}

.cfm-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.cfm-panel-left {
  border: 2px solid #3b82f6;
}

.cfm-panel-right {
  border: 2px solid #10b981;
}

.cfm-panel-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  color: white;
}

.cfm-panel-left .cfm-panel-header {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.cfm-panel-right .cfm-panel-header {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.cfm-panel-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.cfm-panel-content {
  padding: 24px;
}

.cfm-framework-selector {
  margin-bottom: 24px;
}

.cfm-framework-selector label {
  display: block;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.cfm-select {
  width: 100%;
  padding: 12px;
  border: 2px solid #d1d5db;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.2s;
  background: white;
}

.cfm-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.cfm-framework-info {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.cfm-info-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.cfm-info-item:last-child {
  margin-bottom: 0;
}

.cfm-info-label {
  font-weight: 600;
  color: #6b7280;
  font-size: 0.85rem;
}

.cfm-info-value {
  color: #1f2937;
  font-weight: 500;
}

.cfm-compliances-list {
  margin-top: 20px;
}

.cfm-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e5e7eb;
}

.cfm-list-header h4 {
  margin: 0;
  font-size: 1rem;
  color: #1f2937;
}

.cfm-count-badge {
  background: #3b82f6;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.cfm-compliances-scroll {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 8px;
}

.cfm-compliances-scroll::-webkit-scrollbar {
  width: 6px;
}

.cfm-compliances-scroll::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 10px;
}

.cfm-compliances-scroll::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 10px;
}

.cfm-compliances-scroll::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.cfm-compliance-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.cfm-compliance-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
  transform: translateX(4px);
}

.cfm-compliance-selected {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.cfm-compliance-number {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.85rem;
}

.cfm-compliance-content {
  flex: 1;
}

.cfm-compliance-title {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
  font-size: 0.95rem;
}

.cfm-compliance-desc {
  color: #6b7280;
  font-size: 0.85rem;
  line-height: 1.4;
  margin-bottom: 8px;
}

.cfm-compliance-meta {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.cfm-meta-badge {
  padding: 2px 8px;
  background: #e5e7eb;
  color: #4b5563;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Connector */
.cfm-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 24px;
  position: relative;
}

.cfm-connector-line {
  position: absolute;
  width: 2px;
  height: 100%;
  background: linear-gradient(180deg, #3b82f6 0%, #10b981 100%);
  left: 50%;
  transform: translateX(-50%);
}

.cfm-connector-icon {
  width: 60px;
  height: 60px;
  background: white;
  border: 3px solid #3b82f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: #3b82f6;
  z-index: 1;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.cfm-connector-label {
  margin-top: 12px;
  background: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  color: #3b82f6;
  font-size: 0.9rem;
  z-index: 1;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Results Section */
.cfm-results-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.cfm-results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e5e7eb;
}

.cfm-results-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 12px;
}

.cfm-results-stats {
  display: flex;
  gap: 20px;
}

.cfm-stat-item {
  font-size: 0.9rem;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  background: #f9fafb;
}

.cfm-stat-item i {
  font-size: 1rem;
}

.cfm-stat-item strong {
  color: #1f2937;
  font-size: 1.1rem;
}

.cfm-stat-new {
  background: #f0fdf4;
  color: #10b981;
}

.cfm-stat-new i {
  color: #10b981;
}

.cfm-stat-modified {
  background: #fffbeb;
  color: #f59e0b;
}

.cfm-stat-modified i {
  color: #f59e0b;
}

.cfm-stat-removed {
  background: #fef2f2;
  color: #ef4444;
}

.cfm-stat-removed i {
  color: #ef4444;
}

.cfm-stat-unchanged {
  background: #f9fafb;
  color: #6b7280;
}

.cfm-stat-unchanged i {
  color: #9ca3af;
}

.cfm-results-grid {
  display: grid;
  gap: 16px;
}

.cfm-mapping-result {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 20px;
  padding: 20px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s;
  position: relative;
}

.cfm-mapping-result:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

/* Change Type Styles */
.cfm-change-new {
  border-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
}

.cfm-change-modified {
  border-color: #f59e0b;
  background: linear-gradient(135deg, #fffbeb 0%, #ffffff 100%);
}

.cfm-change-removed {
  border-color: #ef4444;
  background: linear-gradient(135deg, #fef2f2 0%, #ffffff 100%);
}

.cfm-change-unchanged {
  border-color: #9ca3af;
  background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
}

.cfm-mapping-from,
.cfm-mapping-to {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cfm-mapping-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  background: #f9fafb;
}

.cfm-empty-placeholder {
  text-align: center;
  color: #9ca3af;
}

.cfm-empty-placeholder i {
  font-size: 2rem;
  margin-bottom: 8px;
  display: block;
}

.cfm-empty-placeholder p {
  margin: 0;
  font-size: 0.85rem;
  font-weight: 500;
}

.cfm-mapping-framework {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cfm-mapping-control {
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
}

.cfm-control-identifier {
  display: inline-block;
  background: #3b82f6;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 8px;
  font-family: monospace;
}

.cfm-mapping-description {
  font-size: 0.85rem;
  color: #6b7280;
  line-height: 1.4;
}

.cfm-mapping-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.cfm-mapping-arrow i {
  font-size: 1.5rem;
  color: #3b82f6;
}

.cfm-change-badge {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cfm-badge-new {
  background: #10b981;
  color: white;
}

.cfm-badge-modified {
  background: #f59e0b;
  color: white;
}

.cfm-badge-removed {
  background: #ef4444;
  color: white;
}

.cfm-badge-unchanged {
  background: #9ca3af;
  color: white;
}

.cfm-mapping-analysis {
  grid-column: 1 / -1;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #6b7280;
  font-style: italic;
}

.cfm-mapping-analysis i {
  color: #3b82f6;
}

/* Loading and Messages */
.cfm-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.cfm-loader {
  background: white;
  padding: 40px;
  border-radius: 12px;
  text-align: center;
  max-width: 400px;
}

.cfm-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.cfm-error-message,
.cfm-success-message {
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.cfm-error-message {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.cfm-success-message {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.cfm-close-btn {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  opacity: 0.7;
}

.cfm-close-btn:hover {
  opacity: 1;
}

/* Responsive Design */
@media (max-width: 1200px) {
  .cross-framework-mapping-container {
    margin-left: 0;
    padding: 16px;
  }

  .cfm-split-container {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .cfm-connector {
    display: none;
  }

  .cfm-mapping-result {
    grid-template-columns: 1fr;
  }

  .cfm-mapping-arrow {
    transform: rotate(90deg);
    margin: 12px 0;
  }
}
</style>

