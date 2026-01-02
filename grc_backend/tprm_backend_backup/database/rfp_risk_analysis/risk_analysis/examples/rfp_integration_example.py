"""
RFP MODULE INTEGRATION EXAMPLE
==============================

This file shows how to integrate the Risk Analysis module with an RFP (Request for Proposal) Management module.
Use this as a template for your RFP module integration.

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
    'rfp_module': ['rfp_requests', 'rfp_responses', 'rfp_evaluations'],
    # ... other modules
}

self.entity_display_names = {
    'rfp_module': 'RFP Management',
    # ... other modules  
}

self.entity_llama_mapping = {
    'rfp_module': 'RFP',
    # ... other modules
}

# In get_rows_for_table method, add:
elif table_name == 'rfp_requests':
    return self._get_rfp_requests()
elif table_name == 'rfp_responses':
    return self._get_rfp_responses()
elif table_name == 'rfp_evaluations':
    return self._get_rfp_evaluations()

# Add these methods to EntityDataService class:
def _get_rfp_requests(self) -> List[Dict]:
    try:
        from rfp_module.models import RFPRequest
        requests = RFPRequest.objects.all().values(
            'rfp_id', 'rfp_title', 'rfp_type', 'status', 'budget', 
            'submission_deadline', 'department', 'created_by'
        )
        
        result = []
        for request in requests:
            display_text = f"RFP {request['rfp_id']} - {request['rfp_title']} ({request['rfp_type']})"
            result.append({
                'id': request['rfp_id'],
                'display_text': display_text,
                'data': request
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching RFP requests: {e}")
        return []

def _get_rfp_responses(self) -> List[Dict]:
    try:
        from rfp_module.models import RFPResponse
        responses = RFPResponse.objects.all().values(
            'response_id', 'rfp_id', 'vendor_id', 'status', 'proposed_amount', 'submitted_date'
        )
        
        result = []
        for response in responses:
            display_text = f"Response {response['response_id']} - RFP {response['rfp_id']} (Vendor: {response['vendor_id']})"
            result.append({
                'id': response['response_id'],
                'display_text': display_text,
                'data': response
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching RFP responses: {e}")
        return []

def _get_rfp_evaluations(self) -> List[Dict]:
    try:
        from rfp_module.models import RFPEvaluation
        evaluations = RFPEvaluation.objects.all().values(
            'evaluation_id', 'rfp_id', 'response_id', 'evaluator_id', 
            'overall_score', 'status', 'evaluation_date'
        )
        
        result = []
        for evaluation in evaluations:
            display_text = f"Evaluation {evaluation['evaluation_id']} - RFP {evaluation['rfp_id']} (Score: {evaluation['overall_score']})"
            result.append({
                'id': evaluation['evaluation_id'],
                'display_text': display_text,
                'data': evaluation
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching RFP evaluations: {e}")
        return []
"""

# ============================================================================
# STEP 2: INTEGRATE IN YOUR RFP VIEWS
# ============================================================================

# In your rfp_module/views.py:
from tprm_backend.risk_analysis.services import RiskAnalysisService
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

def save_rfp_request(request):
    """
    Example: Save RFP request and generate risks
    """
    try:
        # Your existing save logic here...
        rfp_data = request.data
        rfp_request = save_rfp_to_database(rfp_data)
        
        # Generate risks after RFP request is saved
        try:
            # Generate risks for the RFP request
            task = generate_risks_for_rfp_request.delay(
                rfp_id=rfp_request.rfp_id
            )
            
            response_data = {
                'rfp_id': rfp_request.rfp_id,
                'status': 'created',
                'risk_generation_task': task.id,
                'message': 'RFP request created and risk analysis started'
            }
            
        except Exception as e:
            logger.error(f"Failed to start risk generation: {e}")
            response_data = {
                'rfp_id': rfp_request.rfp_id,
                'status': 'created',
                'message': 'RFP request created (risk analysis failed)'
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error saving RFP request: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def save_rfp_response(request, rfp_id):
    """
    Example: Save RFP response and generate risks
    """
    try:
        # Your existing save logic here...
        response_data = request.data
        rfp_response = save_response_to_database(response_data, rfp_id)
        
        # Generate risks after RFP response is saved
        try:
            # Generate risks for the RFP response
            task = generate_risks_for_rfp_response.delay(
                rfp_id=rfp_id,
                response_id=rfp_response.response_id
            )
            
            response_data = {
                'response_id': rfp_response.response_id,
                'rfp_id': rfp_id,
                'status': 'submitted',
                'risk_generation_task': task.id,
                'message': 'RFP response submitted and risk analysis started'
            }
            
        except Exception as e:
            logger.error(f"Failed to start risk generation: {e}")
            response_data = {
                'response_id': rfp_response.response_id,
                'rfp_id': rfp_id,
                'status': 'submitted',
                'message': 'RFP response submitted (risk analysis failed)'
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error saving RFP response: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def save_rfp_evaluation(request, rfp_id, response_id):
    """
    Example: Save RFP evaluation and generate risks
    """
    try:
        # Your existing save logic here...
        evaluation_data = request.data
        rfp_evaluation = save_evaluation_to_database(evaluation_data, rfp_id, response_id)
        
        # Generate risks after RFP evaluation is saved
        try:
            # Generate risks for the RFP evaluation
            task = generate_risks_for_rfp_evaluation.delay(
                rfp_id=rfp_id,
                response_id=response_id,
                evaluation_id=rfp_evaluation.evaluation_id
            )
            
            response_data = {
                'evaluation_id': rfp_evaluation.evaluation_id,
                'rfp_id': rfp_id,
                'response_id': response_id,
                'status': 'evaluated',
                'risk_generation_task': task.id,
                'message': 'RFP evaluation completed and risk analysis started'
            }
            
        except Exception as e:
            logger.error(f"Failed to start risk generation: {e}")
            response_data = {
                'evaluation_id': rfp_evaluation.evaluation_id,
                'rfp_id': rfp_id,
                'response_id': response_id,
                'status': 'evaluated',
                'message': 'RFP evaluation completed (risk analysis failed)'
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error saving RFP evaluation: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@shared_task
def generate_risks_for_rfp_request(rfp_id):
    """
    Background task to generate risks for RFP request
    """
    try:
        service = RiskAnalysisService()
        
        # Generate risks for the RFP request
        result = service.analyze_entity_data_row(
            entity='rfp_module',
            table='rfp_requests',
            row_id=rfp_id
        )
        
        risks = result.get('risks', [])
        logger.info(f"Generated {len(risks)} risks for RFP request {rfp_id}")
        
        # Check for critical risks and send alerts
        critical_risks = [r for r in risks if r['priority'] == 'Critical']
        if critical_risks:
            send_rfp_risk_alert(critical_risks, rfp_id, 'request')
        
        return {
            'rfp_risks': len(risks),
            'critical_risks': len(critical_risks)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate risks for RFP request {rfp_id}: {e}")
        raise

@shared_task
def generate_risks_for_rfp_response(rfp_id, response_id):
    """
    Background task to generate risks for RFP response
    """
    try:
        service = RiskAnalysisService()
        
        # Generate risks for the RFP response
        result = service.analyze_entity_data_row(
            entity='rfp_module',
            table='rfp_responses',
            row_id=response_id
        )
        
        risks = result.get('risks', [])
        logger.info(f"Generated {len(risks)} risks for RFP response {response_id}")
        
        return {
            'response_risks': len(risks)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate risks for RFP response {response_id}: {e}")
        raise

@shared_task
def generate_risks_for_rfp_evaluation(rfp_id, response_id, evaluation_id):
    """
    Background task to generate risks for RFP evaluation
    """
    try:
        service = RiskAnalysisService()
        
        # Generate risks for the RFP evaluation
        result = service.analyze_entity_data_row(
            entity='rfp_module',
            table='rfp_evaluations',
            row_id=evaluation_id
        )
        
        risks = result.get('risks', [])
        logger.info(f"Generated {len(risks)} risks for RFP evaluation {evaluation_id}")
        
        # Also generate comprehensive risks for the entire RFP process
        comprehensive_result = generate_comprehensive_rfp_risks(rfp_id, response_id, evaluation_id)
        
        return {
            'evaluation_risks': len(risks),
            'comprehensive_risks': len(comprehensive_result.get('risks', []))
        }
        
    except Exception as e:
        logger.error(f"Failed to generate risks for RFP evaluation {evaluation_id}: {e}")
        raise

def generate_comprehensive_rfp_risks(rfp_id, response_id=None, evaluation_id=None):
    """
    Generate comprehensive risks for the entire RFP process
    """
    try:
        # Get comprehensive RFP data
        rfp_data = get_rfp_comprehensive_data(rfp_id, response_id, evaluation_id)
        
        # Generate risks using comprehensive service
        service = RiskAnalysisService()
        result = service.analyze_comprehensive_plan_data(
            entity='rfp_module',
            comprehensive_data=rfp_data
        )
        
        risks = result.get('risks', [])
        logger.info(f"Generated {len(risks)} comprehensive risks for RFP {rfp_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate comprehensive RFP risks: {e}")
        raise

def check_rfp_deadline_risks():
    """
    Check for RFPs nearing submission deadlines and generate risks
    """
    try:
        # Get RFPs with deadlines in next 7 days
        upcoming_deadlines = get_rfps_with_upcoming_deadlines(days=7)
        
        service = RiskAnalysisService()
        
        for rfp in upcoming_deadlines:
            try:
                result = service.analyze_entity_data_row(
                    entity='rfp_module',
                    table='rfp_requests',
                    row_id=rfp.rfp_id
                )
                
                # Filter for deadline-related risks
                deadline_risks = [r for r in result.get('risks', []) 
                                if 'deadline' in r['title'].lower() or 
                                   'submission' in r['title'].lower() or
                                   'time' in r['title'].lower()]
                
                if deadline_risks:
                    logger.info(f"Found {len(deadline_risks)} deadline risks for RFP {rfp.rfp_id}")
                    send_deadline_risk_alert(deadline_risks, rfp)
                    
            except Exception as e:
                logger.error(f"Failed to generate deadline risks for RFP {rfp.rfp_id}: {e}")
        
        return len(upcoming_deadlines)
        
    except Exception as e:
        logger.error(f"Failed to check RFP deadline risks: {e}")
        raise

# ============================================================================
# STEP 3: FRONTEND INTEGRATION
# ============================================================================

# In your Vue component (e.g., RFPManagement.vue):
"""
<template>
  <div class="rfp-management">
    <!-- Your existing RFP management content -->
    
    <!-- Risk Analysis Section -->
    <div class="risk-analysis-section">
      <h3>RFP Risk Analysis</h3>
      
      <!-- RFP Selection -->
      <div class="rfp-selection">
        <label>Select RFP for Risk Analysis:</label>
        <select v-model="selectedRFP" @change="loadRFPData">
          <option value="">Choose RFP...</option>
          <option 
            v-for="rfp in rfpOptions" 
            :key="rfp.id" 
            :value="rfp.id"
          >
            {{ rfp.display_text }}
          </option>
        </select>
        
        <button 
          @click="generateRFPRisks" 
          :disabled="!selectedRFP || isGeneratingRisks"
        >
          {{ isGeneratingRisks ? 'Analyzing...' : 'Analyze RFP Risks' }}
        </button>
        
        <button 
          @click="generateComprehensiveRisks" 
          :disabled="!selectedRFP || isGeneratingRisks"
          v-if="selectedRFP"
        >
          Comprehensive Analysis
        </button>
      </div>
      
      <!-- RFP Details -->
      <div class="rfp-details" v-if="selectedRFPData">
        <h4>RFP Information</h4>
        <div class="rfp-info">
          <div class="info-item">
            <span class="label">RFP ID:</span>
            <span class="value">{{ selectedRFPData.rfp_id }}</span>
          </div>
          <div class="info-item">
            <span class="label">Title:</span>
            <span class="value">{{ selectedRFPData.rfp_title }}</span>
          </div>
          <div class="info-item">
            <span class="label">Type:</span>
            <span class="value">{{ selectedRFPData.rfp_type }}</span>
          </div>
          <div class="info-item">
            <span class="label">Status:</span>
            <span class="value" :class="`status-${selectedRFPData.status.toLowerCase()}`">
              {{ selectedRFPData.status }}
            </span>
          </div>
          <div class="info-item">
            <span class="label">Budget:</span>
            <span class="value">${{ formatCurrency(selectedRFPData.budget) }}</span>
          </div>
          <div class="info-item">
            <span class="label">Submission Deadline:</span>
            <span class="value" :class="getDeadlineClass(selectedRFPData.submission_deadline)">
              {{ formatDate(selectedRFPData.submission_deadline) }}
            </span>
          </div>
          <div class="info-item">
            <span class="label">Department:</span>
            <span class="value">{{ selectedRFPData.department }}</span>
          </div>
        </div>
      </div>
      
      <!-- RFP Process Tabs -->
      <div class="rfp-process-tabs" v-if="selectedRFP">
        <div class="tab-nav">
          <button 
            v-for="tab in processTabs" 
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="{ active: activeTab === tab.key }"
          >
            {{ tab.label }}
            <span class="tab-count" v-if="tab.count > 0">({{ tab.count }})</span>
          </button>
        </div>
        
        <!-- RFP Request Risks -->
        <div v-if="activeTab === 'request'" class="tab-content">
          <h5>RFP Request Risks</h5>
          <div class="risk-list">
            <div 
              v-for="risk in requestRisks" 
              :key="risk.id"
              class="risk-item"
              :class="`priority-${risk.priority.toLowerCase()}`"
            >
              <div class="risk-header">
                <span class="risk-title">{{ risk.title }}</span>
                <span class="risk-priority">{{ risk.priority }}</span>
                <span class="risk-score">Score: {{ risk.score }}</span>
              </div>
              <div class="risk-description">{{ risk.description }}</div>
              <div class="risk-explanation">{{ risk.ai_explanation }}</div>
              <div class="risk-mitigations" v-if="risk.suggested_mitigations.length > 0">
                <h6>Recommended Actions:</h6>
                <ul>
                  <li v-for="mitigation in risk.suggested_mitigations" :key="mitigation">
                    {{ mitigation }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
        
        <!-- RFP Response Risks -->
        <div v-if="activeTab === 'responses'" class="tab-content">
          <h5>RFP Response Risks</h5>
          <div class="response-list">
            <div 
              v-for="response in responseData" 
              :key="response.id"
              class="response-item"
            >
              <div class="response-header">
                <span class="response-id">Response {{ response.id }}</span>
                <span class="vendor-id">Vendor: {{ response.data.vendor_id }}</span>
                <span class="proposed-amount">${{ formatCurrency(response.data.proposed_amount) }}</span>
                <button @click="generateResponseRisks(response.id)" class="btn-analyze">
                  Analyze Response Risks
                </button>
              </div>
              
              <div class="response-risks" v-if="responseRisks[response.id]">
                <div 
                  v-for="risk in responseRisks[response.id]" 
                  :key="risk.id"
                  class="risk-item small"
                  :class="`priority-${risk.priority.toLowerCase()}`"
                >
                  <span class="risk-title">{{ risk.title }}</span>
                  <span class="risk-priority">{{ risk.priority }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- RFP Evaluation Risks -->
        <div v-if="activeTab === 'evaluations'" class="tab-content">
          <h5>RFP Evaluation Risks</h5>
          <div class="evaluation-list">
            <div 
              v-for="evaluation in evaluationData" 
              :key="evaluation.id"
              class="evaluation-item"
            >
              <div class="evaluation-header">
                <span class="evaluation-id">Evaluation {{ evaluation.id }}</span>
                <span class="evaluator">Evaluator: {{ evaluation.data.evaluator_id }}</span>
                <span class="score">Score: {{ evaluation.data.overall_score }}/100</span>
                <button @click="generateEvaluationRisks(evaluation.id)" class="btn-analyze">
                  Analyze Evaluation Risks
                </button>
              </div>
              
              <div class="evaluation-risks" v-if="evaluationRisks[evaluation.id]">
                <div 
                  v-for="risk in evaluationRisks[evaluation.id]" 
                  :key="risk.id"
                  class="risk-item small"
                  :class="`priority-${risk.priority.toLowerCase()}`"
                >
                  <span class="risk-title">{{ risk.title }}</span>
                  <span class="risk-priority">{{ risk.priority }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- RFP Health Dashboard -->
      <div class="rfp-health-dashboard" v-if="selectedRFP">
        <h4>RFP Health Status</h4>
        <div class="health-metrics">
          <div class="metric">
            <span class="metric-label">Days to Deadline:</span>
            <span class="metric-value" :class="getDeadlineClass(selectedRFPData?.submission_deadline)">
              {{ getDaysToDeadline(selectedRFPData?.submission_deadline) }}
            </span>
          </div>
          <div class="metric">
            <span class="metric-label">Total Responses:</span>
            <span class="metric-value">{{ responseData.length }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Evaluations Completed:</span>
            <span class="metric-value">{{ completedEvaluations }}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Overall Risk Level:</span>
            <span class="metric-value" :class="getRiskLevelClass(overallRiskLevel)">
              {{ overallRiskLevel }}
            </span>
          </div>
        </div>
        
        <!-- Risk Summary -->
        <div class="risk-summary" v-if="allRisks.length > 0">
          <h5>Risk Summary</h5>
          <div class="summary-grid">
            <div class="summary-item critical">
              <span class="count">{{ riskCounts.critical }}</span>
              <span class="label">Critical</span>
            </div>
            <div class="summary-item high">
              <span class="count">{{ riskCounts.high }}</span>
              <span class="label">High</span>
            </div>
            <div class="summary-item medium">
              <span class="count">{{ riskCounts.medium }}</span>
              <span class="label">Medium</span>
            </div>
            <div class="summary-item low">
              <span class="count">{{ riskCounts.low }}</span>
              <span class="label">Low</span>
            </div>
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
      selectedRFP: '',
      rfpOptions: [],
      selectedRFPData: null,
      activeTab: 'request',
      processTabs: [
        { key: 'request', label: 'RFP Request', count: 0 },
        { key: 'responses', label: 'Responses', count: 0 },
        { key: 'evaluations', label: 'Evaluations', count: 0 }
      ],
      isGeneratingRisks: false,
      requestRisks: [],
      responseRisks: {},
      evaluationRisks: {},
      responseData: [],
      evaluationData: [],
      overallRiskLevel: 'Low'
    }
  },
  
  computed: {
    allRisks() {
      const risks = [...this.requestRisks];
      Object.values(this.responseRisks).forEach(responseRisks => {
        risks.push(...responseRisks);
      });
      Object.values(this.evaluationRisks).forEach(evaluationRisks => {
        risks.push(...evaluationRisks);
      });
      return risks;
    },
    
    riskCounts() {
      const counts = { critical: 0, high: 0, medium: 0, low: 0 };
      this.allRisks.forEach(risk => {
        counts[risk.priority.toLowerCase()]++;
      });
      return counts;
    },
    
    completedEvaluations() {
      return this.evaluationData.filter(eval => eval.data.status === 'COMPLETED').length;
    }
  },
  
  methods: {
    async loadRFPData() {
      if (!this.selectedRFP) return;
      
      try {
        // Load RFP details
        const rfpResponse = await this.$http.get('/api/risk-analysis/entity-dropdown/', {
          params: { action: 'rows', table: 'rfp_requests' }
        });
        
        const rfp = rfpResponse.data.rows.find(row => row.id === this.selectedRFP);
        if (rfp) {
          this.selectedRFPData = rfp.data;
        }
        
        // Load responses
        const responseResponse = await this.$http.get('/api/risk-analysis/entity-dropdown/', {
          params: { action: 'rows', table: 'rfp_responses' }
        });
        
        this.responseData = responseResponse.data.rows.filter(row => 
          row.data.rfp_id === this.selectedRFP
        );
        
        // Load evaluations
        const evaluationResponse = await this.$http.get('/api/risk-analysis/entity-dropdown/', {
          params: { action: 'rows', table: 'rfp_evaluations' }
        });
        
        this.evaluationData = evaluationResponse.data.rows.filter(row => 
          row.data.rfp_id === this.selectedRFP
        );
        
        // Update tab counts
        this.processTabs[1].count = this.responseData.length;
        this.processTabs[2].count = this.evaluationData.length;
        
      } catch (error) {
        console.error('Failed to load RFP data:', error);
      }
    },
    
    async generateRFPRisks() {
      this.isGeneratingRisks = true;
      
      try {
        const response = await this.$http.post('/api/risk-analysis/entity-risk-generation/', {
          entity: 'rfp_module',
          table: 'rfp_requests',
          row_id: this.selectedRFP
        });
        
        this.requestRisks = response.data.risks || [];
        this.updateOverallRiskLevel();
        this.processTabs[0].count = this.requestRisks.length;
        this.$toast.success(`Generated ${this.requestRisks.length} RFP request risks`);
        
      } catch (error) {
        console.error('Failed to generate RFP risks:', error);
        this.$toast.error('Failed to generate RFP risks');
      } finally {
        this.isGeneratingRisks = false;
      }
    },
    
    async generateResponseRisks(responseId) {
      try {
        const response = await this.$http.post('/api/risk-analysis/entity-risk-generation/', {
          entity: 'rfp_module',
          table: 'rfp_responses',
          row_id: responseId
        });
        
        this.responseRisks[responseId] = response.data.risks || [];
        this.updateOverallRiskLevel();
        this.$toast.success(`Generated ${this.responseRisks[responseId].length} response risks`);
        
      } catch (error) {
        console.error('Failed to generate response risks:', error);
        this.$toast.error('Failed to generate response risks');
      }
    },
    
    async generateEvaluationRisks(evaluationId) {
      try {
        const response = await this.$http.post('/api/risk-analysis/entity-risk-generation/', {
          entity: 'rfp_module',
          table: 'rfp_evaluations',
          row_id: evaluationId
        });
        
        this.evaluationRisks[evaluationId] = response.data.risks || [];
        this.updateOverallRiskLevel();
        this.$toast.success(`Generated ${this.evaluationRisks[evaluationId].length} evaluation risks`);
        
      } catch (error) {
        console.error('Failed to generate evaluation risks:', error);
        this.$toast.error('Failed to generate evaluation risks');
      }
    },
    
    async generateComprehensiveRisks() {
      this.isGeneratingRisks = true;
      
      try {
        const response = await this.$http.post('/api/risk-analysis/entity-risk-generation/', {
          entity: 'rfp_module',
          table: 'comprehensive_rfp_data',
          row_id: this.selectedRFP,
          comprehensive_data: {
            rfp_info: this.selectedRFPData,
            responses: this.responseData.map(r => r.data),
            evaluations: this.evaluationData.map(e => e.data)
          }
        });
        
        this.requestRisks = response.data.risks || [];
        this.updateOverallRiskLevel();
        this.$toast.success(`Generated ${this.requestRisks.length} comprehensive risks`);
        
      } catch (error) {
        console.error('Failed to generate comprehensive risks:', error);
        this.$toast.error('Failed to generate comprehensive risks');
      } finally {
        this.isGeneratingRisks = false;
      }
    },
    
    updateOverallRiskLevel() {
      if (this.allRisks.length === 0) {
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
    
    getDaysToDeadline(deadline) {
      if (!deadline) return null;
      
      const today = new Date();
      const deadlineDate = new Date(deadline);
      const diffTime = deadlineDate - today;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      return diffDays;
    },
    
    getDeadlineClass(deadline) {
      const days = this.getDaysToDeadline(deadline);
      if (days === null) return '';
      if (days < 3) return 'deadline-critical';
      if (days < 7) return 'deadline-warning';
      return 'deadline-good';
    },
    
    getRiskLevelClass(riskLevel) {
      return `risk-level-${riskLevel.toLowerCase()}`;
    },
    
    formatCurrency(value) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
      }).format(value);
    },
    
    formatDate(date) {
      if (!date) return '';
      return new Date(date).toLocaleDateString();
    }
  },
  
  async mounted() {
    // Load RFP options
    try {
      const response = await this.$http.get('/api/risk-analysis/entity-dropdown/', {
        params: { action: 'tables', entity: 'rfp_module' }
      });
      
      const rfpTable = response.data.tables.find(t => t.table_name === 'rfp_requests');
      if (rfpTable) {
        const rfpResponse = await this.$http.get('/api/risk-analysis/entity-dropdown/', {
          params: { action: 'rows', table: 'rfp_requests' }
        });
        this.rfpOptions = rfpResponse.data.rows;
      }
    } catch (error) {
      console.error('Failed to load RFP options:', error);
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

.rfp-selection {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.rfp-details {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: white;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.rfp-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
}

.info-item .label {
  font-weight: bold;
  color: #666;
}

.info-item .value {
  color: #333;
}

.status-active { color: #28a745; }
.status-closed { color: #dc3545; }
.status-pending { color: #ffc107; }

.deadline-critical { color: #dc3545; font-weight: bold; }
.deadline-warning { color: #ffc107; font-weight: bold; }
.deadline-good { color: #28a745; }

.rfp-process-tabs {
  margin-bottom: 2rem;
}

.tab-nav {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid #ddd;
}

.tab-nav button {
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
}

.tab-nav button.active {
  border-bottom-color: #007bff;
  color: #007bff;
}

.tab-count {
  background-color: #6c757d;
  color: white;
  padding: 0.2rem 0.4rem;
  border-radius: 10px;
  font-size: 0.8rem;
  margin-left: 0.5rem;
}

.tab-content {
  padding: 1rem;
  background-color: white;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.response-item, .evaluation-item {
  margin-bottom: 1rem;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f8f9fa;
}

.response-header, .evaluation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.btn-analyze {
  padding: 0.5rem 1rem;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.risk-item {
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 8px;
  border-left: 4px solid #ccc;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.risk-item.small {
  padding: 0.5rem;
  margin-bottom: 0.5rem;
}

.risk-item.small .risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.priority-critical { border-left-color: #dc3545; }
.priority-high { border-left-color: #fd7e14; }
.priority-medium { border-left-color: #ffc107; }
.priority-low { border-left-color: #28a745; }

.rfp-health-dashboard {
  margin-top: 2rem;
  padding: 1rem;
  background-color: white;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.health-metrics {
  display: flex;
  gap: 2rem;
  margin-bottom: 1rem;
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

.risk-level-critical { color: #dc3545; }
.risk-level-high { color: #fd7e14; }
.risk-level-medium { color: #ffc107; }
.risk-level-low { color: #28a745; }

.risk-summary {
  margin-top: 1rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.summary-item {
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  color: white;
}

.summary-item.critical { background-color: #dc3545; }
.summary-item.high { background-color: #fd7e14; }
.summary-item.medium { background-color: #ffc107; color: #000; }
.summary-item.low { background-color: #28a745; }

.summary-item .count {
  display: block;
  font-size: 2rem;
  font-weight: bold;
}

.summary-item .label {
  display: block;
  font-size: 0.9rem;
}
</style>
"""
