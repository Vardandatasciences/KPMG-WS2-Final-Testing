"""
SLA MODULE INTEGRATION EXAMPLE
==============================

This file shows how to integrate the Risk Analysis module with an SLA Management module.
Use this as a template for your SLA module integration.

INTEGRATION STEPS:
1. Update entity_table_mappings in entity_service.py
2. Implement data retrieval methods
3. Add risk generation to your views
4. Create frontend components
"""

# ============================================================================
# STEP 1: UPDATE entity_service.py
# ============================================================================
"""
Add these to backend/risk_analysis/entity_service.py:

# In __init__ method, update mappings:
self.entity_table_mappings = {
    'sla_module': ['sla_agreements', 'sla_performance', 'sla_violations'],
    # ... other modules
}

self.entity_display_names = {
    'sla_module': 'SLA Management',
    # ... other modules  
}

self.entity_llama_mapping = {
    'sla_module': 'SLA',
    # ... other modules
}

# In get_rows_for_table method, add:
elif table_name == 'sla_agreements':
    return self._get_sla_agreements()
elif table_name == 'sla_performance':
    return self._get_sla_performance()
elif table_name == 'sla_violations':
    return self._get_sla_violations()

# Add these methods to EntityDataService class:
def _get_sla_agreements(self) -> List[Dict]:
    try:
        from sla_module.models import SLAAgreement
        agreements = SLAAgreement.objects.all().values(
            'sla_id', 'sla_name', 'service_type', 'status', 'uptime_target'
        )
        
        result = []
        for agreement in agreements:
            display_text = f"SLA {agreement['sla_id']} - {agreement['sla_name']} ({agreement['service_type']})"
            result.append({
                'id': agreement['sla_id'],
                'display_text': display_text,
                'data': agreement
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching SLA agreements: {e}")
        return []

def _get_sla_performance(self) -> List[Dict]:
    try:
        from sla_module.models import SLAPerformance
        performances = SLAPerformance.objects.all().values(
            'performance_id', 'sla_id', 'measurement_period', 'uptime_actual', 'uptime_target'
        )
        
        result = []
        for performance in performances:
            uptime_pct = (performance['uptime_actual'] / performance['uptime_target']) * 100
            display_text = f"Performance {performance['performance_id']} - SLA {performance['sla_id']} ({uptime_pct:.1f}% uptime)"
            result.append({
                'id': performance['performance_id'],
                'display_text': display_text,
                'data': performance
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching SLA performance: {e}")
        return []
"""

# ============================================================================
# STEP 2: INTEGRATE IN YOUR SLA VIEWS
# ============================================================================

# In your sla_module/views.py:
from tprm_backend.risk_analysis.services import RiskAnalysisService
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

def save_sla_performance(request, sla_id):
    """
    Example: Save SLA performance metrics and generate risks
    """
    try:
        # Your existing save logic here...
        performance_data = request.data
        performance = save_performance_to_database(performance_data)
        
        # Generate risks after performance data is saved
        try:
            # Generate risks for SLA performance
            task = generate_risks_for_sla_performance.delay(
                sla_id=sla_id,
                performance_id=performance.performance_id
            )
            
            response_data = {
                'performance_id': performance.performance_id,
                'sla_id': sla_id,
                'status': 'completed',
                'risk_generation_task': task.id,
                'message': 'Performance data saved and risk analysis started'
            }
            
        except Exception as e:
            logger.error(f"Failed to start risk generation: {e}")
            response_data = {
                'performance_id': performance.performance_id,
                'sla_id': sla_id,
                'status': 'completed',
                'message': 'Performance data saved (risk analysis failed)'
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error saving SLA performance: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@shared_task
def generate_risks_for_sla_performance(sla_id, performance_id):
    """
    Background task to generate risks for SLA performance data
    """
    try:
        service = RiskAnalysisService()
        
        # Generate risks for the SLA performance
        result = service.analyze_entity_data_row(
            entity='sla_module',
            table='sla_performance',
            row_id=performance_id
        )
        
        risks = result.get('risks', [])
        logger.info(f"Generated {len(risks)} risks for SLA performance {performance_id}")
        
        # Also generate risks for the SLA agreement itself
        sla_result = service.analyze_entity_data_row(
            entity='sla_module',
            table='sla_agreements',
            row_id=sla_id
        )
        
        sla_risks = sla_result.get('risks', [])
        logger.info(f"Generated {len(sla_risks)} risks for SLA agreement {sla_id}")
        
        return {
            'performance_risks': len(risks),
            'sla_risks': len(sla_risks),
            'total_risks': len(risks) + len(sla_risks)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate risks for SLA {sla_id}: {e}")
        raise

def generate_sla_violation_risks(violation_id):
    """
    Generate risks when SLA violations occur
    """
    try:
        service = RiskAnalysisService()
        
        # Generate risks for SLA violation
        result = service.analyze_entity_data_row(
            entity='sla_module',
            table='sla_violations',
            row_id=violation_id
        )
        
        risks = result.get('risks', [])
        logger.info(f"Generated {len(risks)} risks for SLA violation {violation_id}")
        
        # Send alerts for critical risks
        critical_risks = [r for r in risks if r['priority'] == 'Critical']
        if critical_risks:
            send_critical_risk_alert(critical_risks, violation_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate risks for SLA violation {violation_id}: {e}")
        raise

# ============================================================================
# STEP 3: FRONTEND INTEGRATION
# ============================================================================

# In your Vue component (e.g., SLADashboard.vue):
"""
<template>
  <div class="sla-dashboard">
    <!-- Your existing SLA dashboard content -->
    
    <!-- Risk Analysis Section -->
    <div class="risk-analysis-section">
      <h3>SLA Risk Analysis</h3>
      
      <!-- SLA Selection -->
      <div class="sla-selection">
        <label>Select SLA for Risk Analysis:</label>
        <select v-model="selectedSLA" @change="loadSLAOptions">
          <option value="">Choose SLA...</option>
          <option 
            v-for="sla in slaOptions" 
            :key="sla.id" 
            :value="sla.id"
          >
            {{ sla.display_text }}
          </option>
        </select>
        
        <button 
          @click="generateSLARisks" 
          :disabled="!selectedSLA || isGeneratingRisks"
        >
          {{ isGeneratingRisks ? 'Analyzing...' : 'Analyze SLA Risks' }}
        </button>
      </div>
      
      <!-- Performance Selection -->
      <div class="performance-selection" v-if="selectedSLA">
        <label>Select Performance Period:</label>
        <select v-model="selectedPerformance">
          <option value="">Choose Performance Period...</option>
          <option 
            v-for="perf in performanceOptions" 
            :key="perf.id" 
            :value="perf.id"
          >
            {{ perf.display_text }}
          </option>
        </select>
        
        <button 
          @click="generatePerformanceRisks" 
          :disabled="!selectedPerformance || isGeneratingRisks"
        >
          Analyze Performance Risks
        </button>
      </div>
      
      <!-- Risk Results -->
      <div class="risk-results" v-if="generatedRisks.length > 0">
        <h4>SLA Risk Analysis Results ({{ generatedRisks.length }})</h4>
        
        <!-- Risk Summary -->
        <div class="risk-summary">
          <div class="summary-item critical">
            Critical: {{ riskCounts.critical }}
          </div>
          <div class="summary-item high">
            High: {{ riskCounts.high }}
          </div>
          <div class="summary-item medium">
            Medium: {{ riskCounts.medium }}
          </div>
          <div class="summary-item low">
            Low: {{ riskCounts.low }}
          </div>
        </div>
        
        <!-- Risk List -->
        <div class="risk-list">
          <div 
            v-for="risk in generatedRisks" 
            :key="risk.id"
            class="risk-item"
            :class="`priority-${risk.priority.toLowerCase()}`"
          >
            <div class="risk-header">
              <span class="risk-title">{{ risk.title }}</span>
              <div class="risk-metrics">
                <span class="risk-priority">{{ risk.priority }}</span>
                <span class="risk-score">Score: {{ risk.score }}</span>
                <span class="risk-likelihood">Likelihood: {{ risk.likelihood }}/5</span>
                <span class="risk-impact">Impact: {{ risk.impact }}/5</span>
              </div>
            </div>
            
            <div class="risk-description">{{ risk.description }}</div>
            <div class="risk-explanation">{{ risk.ai_explanation }}</div>
            
            <div class="risk-mitigations" v-if="risk.suggested_mitigations.length > 0">
              <h5>Recommended Actions:</h5>
              <ul>
                <li v-for="mitigation in risk.suggested_mitigations" :key="mitigation">
                  {{ mitigation }}
                </li>
              </ul>
            </div>
            
            <div class="risk-actions">
              <button @click="acknowledgeRisk(risk.id)" class="btn-acknowledge">
                Acknowledge
              </button>
              <button @click="assignRisk(risk.id)" class="btn-assign">
                Assign Owner
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- SLA Health Indicator -->
      <div class="sla-health-indicator" v-if="selectedSLA">
        <h4>SLA Health Status</h4>
        <div class="health-metrics">
          <div class="metric">
            <span class="metric-label">Current Uptime:</span>
            <span class="metric-value" :class="getUptimeClass(currentUptime)">
              {{ currentUptime }}%
            </span>
          </div>
          <div class="metric">
            <span class="metric-label">Target Uptime:</span>
            <span class="metric-value">{{ targetUptime }}%</span>
          </div>
          <div class="metric">
            <span class="metric-label">Risk Level:</span>
            <span class="metric-value" :class="getRiskLevelClass(overallRiskLevel)">
              {{ overallRiskLevel }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      selectedSLA: '',
      selectedPerformance: '',
      slaOptions: [],
      performanceOptions: [],
      isGeneratingRisks: false,
      generatedRisks: [],
      currentUptime: 0,
      targetUptime: 99.9,
      overallRiskLevel: 'Low'
    }
  },
  
  computed: {
    riskCounts() {
      const counts = { critical: 0, high: 0, medium: 0, low: 0 };
      this.generatedRisks.forEach(risk => {
        counts[risk.priority.toLowerCase()]++;
      });
      return counts;
    }
  },
  
  methods: {
    async loadSLAOptions() {
      try {
        const response = await this.$http.get('/api/risk-analysis/entity-dropdown/', {
          params: { action: 'tables', entity: 'sla_module' }
        });
        
        const slaTable = response.data.tables.find(t => t.table_name === 'sla_agreements');
        if (slaTable) {
          const slaResponse = await this.$http.get('/api/risk-analysis/entity-dropdown/', {
            params: { action: 'rows', table: 'sla_agreements' }
          });
          this.slaOptions = slaResponse.data.rows;
        }
      } catch (error) {
        console.error('Failed to load SLA options:', error);
      }
    },
    
    async loadPerformanceOptions() {
      if (!this.selectedSLA) return;
      
      try {
        const response = await this.$http.get('/api/risk-analysis/entity-dropdown/', {
          params: { action: 'rows', table: 'sla_performance' }
        });
        
        // Filter performance data for selected SLA
        this.performanceOptions = response.data.rows.filter(row => 
          row.data.sla_id === this.selectedSLA
        );
      } catch (error) {
        console.error('Failed to load performance options:', error);
      }
    },
    
    async generateSLARisks() {
      this.isGeneratingRisks = true;
      
      try {
        const response = await this.$http.post('/api/risk-analysis/entity-risk-generation/', {
          entity: 'sla_module',
          table: 'sla_agreements',
          row_id: this.selectedSLA
        });
        
        this.generatedRisks = response.data.risks || [];
        this.updateOverallRiskLevel();
        this.$toast.success(`Generated ${this.generatedRisks.length} SLA risks`);
        
      } catch (error) {
        console.error('Failed to generate SLA risks:', error);
        this.$toast.error('Failed to generate SLA risks');
      } finally {
        this.isGeneratingRisks = false;
      }
    },
    
    async generatePerformanceRisks() {
      this.isGeneratingRisks = true;
      
      try {
        const response = await this.$http.post('/api/risk-analysis/entity-risk-generation/', {
          entity: 'sla_module',
          table: 'sla_performance',
          row_id: this.selectedPerformance
        });
        
        this.generatedRisks = response.data.risks || [];
        this.updateOverallRiskLevel();
        this.$toast.success(`Generated ${this.generatedRisks.length} performance risks`);
        
      } catch (error) {
        console.error('Failed to generate performance risks:', error);
        this.$toast.error('Failed to generate performance risks');
      } finally {
        this.isGeneratingRisks = false;
      }
    },
    
    updateOverallRiskLevel() {
      if (this.generatedRisks.length === 0) {
        this.overallRiskLevel = 'Low';
        return;
      }
      
      const criticalCount = this.riskCounts.critical;
      const highCount = this.riskCounts.high;
      
      if (criticalCount > 0) {
        this.overallRiskLevel = 'Critical';
      } else if (highCount > 2) {
        this.overallRiskLevel = 'High';
      } else if (highCount > 0 || this.riskCounts.medium > 3) {
        this.overallRiskLevel = 'Medium';
      } else {
        this.overallRiskLevel = 'Low';
      }
    },
    
    getUptimeClass(uptime) {
      if (uptime >= this.targetUptime) return 'uptime-good';
      if (uptime >= this.targetUptime - 1) return 'uptime-warning';
      return 'uptime-critical';
    },
    
    getRiskLevelClass(riskLevel) {
      return `risk-level-${riskLevel.toLowerCase()}`;
    },
    
    async acknowledgeRisk(riskId) {
      try {
        await this.$http.post(`/api/risk-analysis/risks/${riskId}/acknowledge/`);
        this.$toast.success('Risk acknowledged');
        // Refresh risk data
        this.generateSLARisks();
      } catch (error) {
        console.error('Failed to acknowledge risk:', error);
        this.$toast.error('Failed to acknowledge risk');
      }
    },
    
    async assignRisk(riskId) {
      // Open assignment modal or navigate to assignment page
      this.$router.push({
        name: 'RiskAssignment',
        params: { riskId: riskId }
      });
    }
  },
  
  watch: {
    selectedSLA() {
      this.selectedPerformance = '';
      this.performanceOptions = [];
      this.generatedRisks = [];
      this.loadPerformanceOptions();
    }
  }
}
</script>

<style scoped>
.risk-analysis-section {
  margin-top: 2rem;
  padding: 1.5rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}

.sla-selection, .performance-selection {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.risk-summary {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.summary-item {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-weight: bold;
  color: white;
}

.summary-item.critical { background-color: #dc3545; }
.summary-item.high { background-color: #fd7e14; }
.summary-item.medium { background-color: #ffc107; color: #000; }
.summary-item.low { background-color: #28a745; }

.risk-item {
  margin-bottom: 1.5rem;
  padding: 1.5rem;
  border-radius: 8px;
  border-left: 4px solid #ccc;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.priority-critical { border-left-color: #dc3545; }
.priority-high { border-left-color: #fd7e14; }
.priority-medium { border-left-color: #ffc107; }
.priority-low { border-left-color: #28a745; }

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.risk-metrics {
  display: flex;
  gap: 1rem;
  font-size: 0.9rem;
}

.risk-metrics span {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background-color: #f8f9fa;
}

.risk-actions {
  margin-top: 1rem;
  display: flex;
  gap: 1rem;
}

.btn-acknowledge, .btn-assign {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-acknowledge {
  background-color: #28a745;
  color: white;
}

.btn-assign {
  background-color: #007bff;
  color: white;
}

.sla-health-indicator {
  margin-top: 2rem;
  padding: 1rem;
  background-color: white;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.health-metrics {
  display: flex;
  gap: 2rem;
}

.metric {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.metric-label {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: bold;
}

.uptime-good { color: #28a745; }
.uptime-warning { color: #ffc107; }
.uptime-critical { color: #dc3545; }

.risk-level-critical { color: #dc3545; }
.risk-level-high { color: #fd7e14; }
.risk-level-medium { color: #ffc107; }
.risk-level-low { color: #28a745; }
</style>
"""
