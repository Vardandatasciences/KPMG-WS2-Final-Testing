"""
CONTRACT MODULE INTEGRATION EXAMPLE
===================================

This file shows how to integrate the Risk Analysis module with a Contract Management module.
Use this as a template for your Contract module integration.

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
    'contract_module': ['contracts', 'contract_amendments', 'contract_compliance'],
    # ... other modules
}

self.entity_display_names = {
    'contract_module': 'Contract Management',
    # ... other modules  
}

self.entity_llama_mapping = {
    'contract_module': 'Contract',
    # ... other modules
}

# In get_rows_for_table method, add:
elif table_name == 'contracts':
    return self._get_contracts()
elif table_name == 'contract_amendments':
    return self._get_contract_amendments()
elif table_name == 'contract_compliance':
    return self._get_contract_compliance()

# Add these methods to EntityDataService class:
def _get_contracts(self) -> List[Dict]:
    try:
        from contract_module.models import Contract
        contracts = Contract.objects.all().values(
            'contract_id', 'contract_name', 'contract_type', 'status', 
            'start_date', 'end_date', 'value', 'vendor_id'
        )
        
        result = []
        for contract in contracts:
            display_text = f"Contract {contract['contract_id']} - {contract['contract_name']} ({contract['contract_type']})"
            result.append({
                'id': contract['contract_id'],
                'display_text': display_text,
                'data': contract
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching contracts: {e}")
        return []

def _get_contract_amendments(self) -> List[Dict]:
    try:
        from contract_module.models import ContractAmendment
        amendments = ContractAmendment.objects.all().values(
            'amendment_id', 'contract_id', 'amendment_type', 'status', 'effective_date'
        )
        
        result = []
        for amendment in amendments:
            display_text = f"Amendment {amendment['amendment_id']} - Contract {amendment['contract_id']} ({amendment['amendment_type']})"
            result.append({
                'id': amendment['amendment_id'],
                'display_text': display_text,
                'data': amendment
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching contract amendments: {e}")
        return []
"""

# ============================================================================
# STEP 2: INTEGRATE IN YOUR CONTRACT VIEWS
# ============================================================================

# In your contract_module/views.py:
from risk_analysis.services import RiskAnalysisService
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

def save_contract(request):
    """
    Example: Save contract and generate risks
    """
    try:
        # Your existing save logic here...
        contract_data = request.data
        contract = save_contract_to_database(contract_data)
        
        # Generate risks after contract is saved
        try:
            # Generate risks for the contract
            task = generate_risks_for_contract.delay(
                contract_id=contract.contract_id
            )
            
            response_data = {
                'contract_id': contract.contract_id,
                'status': 'saved',
                'risk_generation_task': task.id,
                'message': 'Contract saved and risk analysis started'
            }
            
        except Exception as e:
            logger.error(f"Failed to start risk generation: {e}")
            response_data = {
                'contract_id': contract.contract_id,
                'status': 'saved',
                'message': 'Contract saved (risk analysis failed)'
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error saving contract: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def save_contract_amendment(request, contract_id):
    """
    Example: Save contract amendment and generate risks
    """
    try:
        # Your existing save logic here...
        amendment_data = request.data
        amendment = save_amendment_to_database(amendment_data, contract_id)
        
        # Generate risks after amendment is saved
        try:
            # Generate risks for the amendment
            task = generate_risks_for_contract_amendment.delay(
                contract_id=contract_id,
                amendment_id=amendment.amendment_id
            )
            
            response_data = {
                'amendment_id': amendment.amendment_id,
                'contract_id': contract_id,
                'status': 'saved',
                'risk_generation_task': task.id,
                'message': 'Amendment saved and risk analysis started'
            }
            
        except Exception as e:
            logger.error(f"Failed to start risk generation: {e}")
            response_data = {
                'amendment_id': amendment.amendment_id,
                'contract_id': contract_id,
                'status': 'saved',
                'message': 'Amendment saved (risk analysis failed)'
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error saving contract amendment: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@shared_task
def generate_risks_for_contract(contract_id):
    """
    Background task to generate risks for contract
    """
    try:
        service = RiskAnalysisService()
        
        # Generate risks for the contract
        result = service.analyze_entity_data_row(
            entity='contract_module',
            table='contracts',
            row_id=contract_id
        )
        
        risks = result.get('risks', [])
        logger.info(f"Generated {len(risks)} risks for contract {contract_id}")
        
        # Check for critical risks and send alerts
        critical_risks = [r for r in risks if r['priority'] == 'Critical']
        if critical_risks:
            send_contract_risk_alert(critical_risks, contract_id)
        
        return {
            'contract_risks': len(risks),
            'critical_risks': len(critical_risks)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate risks for contract {contract_id}: {e}")
        raise

@shared_task
def generate_risks_for_contract_amendment(contract_id, amendment_id):
    """
    Background task to generate risks for contract amendment
    """
    try:
        service = RiskAnalysisService()
        
        # Generate risks for the amendment
        result = service.analyze_entity_data_row(
            entity='contract_module',
            table='contract_amendments',
            row_id=amendment_id
        )
        
        risks = result.get('risks', [])
        logger.info(f"Generated {len(risks)} risks for contract amendment {amendment_id}")
        
        return {
            'amendment_risks': len(risks)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate risks for contract amendment {amendment_id}: {e}")
        raise

def generate_comprehensive_contract_risks(contract_id):
    """
    Generate comprehensive risks using multiple contract data sources
    """
    try:
        # Get comprehensive contract data
        contract_data = get_contract_comprehensive_data(contract_id)
        
        # Generate risks using comprehensive service
        service = RiskAnalysisService()
        result = service.analyze_comprehensive_plan_data(
            entity='contract_module',
            comprehensive_data=contract_data
        )
        
        risks = result.get('risks', [])
        logger.info(f"Generated {len(risks)} comprehensive risks for contract {contract_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate comprehensive contract risks: {e}")
        raise

def check_contract_expiration_risks():
    """
    Check for contracts nearing expiration and generate risks
    """
    try:
        # Get contracts expiring in next 90 days
        expiring_contracts = get_expiring_contracts(days=90)
        
        service = RiskAnalysisService()
        
        for contract in expiring_contracts:
            try:
                result = service.analyze_entity_data_row(
                    entity='contract_module',
                    table='contracts',
                    row_id=contract.contract_id
                )
                
                # Filter for expiration-related risks
                expiration_risks = [r for r in result.get('risks', []) 
                                  if 'expiration' in r['title'].lower() or 
                                     'renewal' in r['title'].lower()]
                
                if expiration_risks:
                    logger.info(f"Found {len(expiration_risks)} expiration risks for contract {contract.contract_id}")
                    send_expiration_risk_alert(expiration_risks, contract)
                    
            except Exception as e:
                logger.error(f"Failed to generate expiration risks for contract {contract.contract_id}: {e}")
        
        return len(expiring_contracts)
        
    except Exception as e:
        logger.error(f"Failed to check contract expiration risks: {e}")
        raise

# ============================================================================
# STEP 3: FRONTEND INTEGRATION
# ============================================================================

# In your Vue component (e.g., ContractManagement.vue):
"""
<template>
  <div class="contract-management">
    <!-- Your existing contract management content -->
    
    <!-- Risk Analysis Section -->
    <div class="risk-analysis-section">
      <h3>Contract Risk Analysis</h3>
      
      <!-- Contract Selection -->
      <div class="contract-selection">
        <label>Select Contract for Risk Analysis:</label>
        <select v-model="selectedContract" @change="loadContractData">
          <option value="">Choose Contract...</option>
          <option 
            v-for="contract in contractOptions" 
            :key="contract.id" 
            :value="contract.id"
          >
            {{ contract.display_text }}
          </option>
        </select>
        
        <button 
          @click="generateContractRisks" 
          :disabled="!selectedContract || isGeneratingRisks"
        >
          {{ isGeneratingRisks ? 'Analyzing...' : 'Analyze Contract Risks' }}
        </button>
        
        <button 
          @click="generateComprehensiveRisks" 
          :disabled="!selectedContract || isGeneratingRisks"
          v-if="selectedContract"
        >
          Comprehensive Analysis
        </button>
      </div>
      
      <!-- Contract Details -->
      <div class="contract-details" v-if="selectedContractData">
        <h4>Contract Information</h4>
        <div class="contract-info">
          <div class="info-item">
            <span class="label">Contract ID:</span>
            <span class="value">{{ selectedContractData.contract_id }}</span>
          </div>
          <div class="info-item">
            <span class="label">Type:</span>
            <span class="value">{{ selectedContractData.contract_type }}</span>
          </div>
          <div class="info-item">
            <span class="label">Status:</span>
            <span class="value" :class="`status-${selectedContractData.status.toLowerCase()}`">
              {{ selectedContractData.status }}
            </span>
          </div>
          <div class="info-item">
            <span class="label">Value:</span>
            <span class="value">${{ formatCurrency(selectedContractData.value) }}</span>
          </div>
          <div class="info-item">
            <span class="label">End Date:</span>
            <span class="value" :class="getExpirationClass(selectedContractData.end_date)">
              {{ formatDate(selectedContractData.end_date) }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- Risk Results -->
      <div class="risk-results" v-if="generatedRisks.length > 0">
        <h4>Contract Risk Analysis Results ({{ generatedRisks.length }})</h4>
        
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
        
        <!-- Risk Categories -->
        <div class="risk-categories">
          <div class="category-section" v-if="expirationRisks.length > 0">
            <h5>Expiration & Renewal Risks ({{ expirationRisks.length }})</h5>
            <div class="risk-list">
              <div 
                v-for="risk in expirationRisks" 
                :key="risk.id"
                class="risk-item expiration-risk"
              >
                <div class="risk-header">
                  <span class="risk-title">{{ risk.title }}</span>
                  <span class="risk-priority">{{ risk.priority }}</span>
                </div>
                <div class="risk-description">{{ risk.description }}</div>
                <div class="risk-mitigations">
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
          
          <div class="category-section" v-if="complianceRisks.length > 0">
            <h5>Compliance Risks ({{ complianceRisks.length }})</h5>
            <div class="risk-list">
              <div 
                v-for="risk in complianceRisks" 
                :key="risk.id"
                class="risk-item compliance-risk"
              >
                <div class="risk-header">
                  <span class="risk-title">{{ risk.title }}</span>
                  <span class="risk-priority">{{ risk.priority }}</span>
                </div>
                <div class="risk-description">{{ risk.description }}</div>
                <div class="risk-mitigations">
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
          
          <div class="category-section" v-if="otherRisks.length > 0">
            <h5>Other Risks ({{ otherRisks.length }})</h5>
            <div class="risk-list">
              <div 
                v-for="risk in otherRisks" 
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
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Contract Health Dashboard -->
      <div class="contract-health-dashboard" v-if="selectedContract">
        <h4>Contract Health Status</h4>
        <div class="health-metrics">
          <div class="metric">
            <span class="metric-label">Days to Expiration:</span>
            <span class="metric-value" :class="getExpirationClass(selectedContractData?.end_date)">
              {{ getDaysToExpiration(selectedContractData?.end_date) }}
            </span>
          </div>
          <div class="metric">
            <span class="metric-label">Overall Risk Level:</span>
            <span class="metric-value" :class="getRiskLevelClass(overallRiskLevel)">
              {{ overallRiskLevel }}
            </span>
          </div>
          <div class="metric">
            <span class="metric-label">Compliance Status:</span>
            <span class="metric-value" :class="getComplianceClass(complianceStatus)">
              {{ complianceStatus }}
            </span>
          </div>
        </div>
        
        <!-- Action Items -->
        <div class="action-items" v-if="actionItems.length > 0">
          <h5>Recommended Actions</h5>
          <ul>
            <li v-for="action in actionItems" :key="action.id" class="action-item">
              <span class="action-priority" :class="action.priority">{{ action.priority }}</span>
              <span class="action-text">{{ action.description }}</span>
              <span class="action-deadline">{{ action.deadline }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      selectedContract: '',
      contractOptions: [],
      selectedContractData: null,
      isGeneratingRisks: false,
      generatedRisks: [],
      overallRiskLevel: 'Low',
      complianceStatus: 'Compliant',
      actionItems: []
    }
  },
  
  computed: {
    riskCounts() {
      const counts = { critical: 0, high: 0, medium: 0, low: 0 };
      this.generatedRisks.forEach(risk => {
        counts[risk.priority.toLowerCase()]++;
      });
      return counts;
    },
    
    expirationRisks() {
      return this.generatedRisks.filter(risk => 
        risk.title.toLowerCase().includes('expiration') ||
        risk.title.toLowerCase().includes('renewal') ||
        risk.title.toLowerCase().includes('expiry')
      );
    },
    
    complianceRisks() {
      return this.generatedRisks.filter(risk => 
        risk.title.toLowerCase().includes('compliance') ||
        risk.title.toLowerCase().includes('regulatory') ||
        risk.title.toLowerCase().includes('audit')
      );
    },
    
    otherRisks() {
      return this.generatedRisks.filter(risk => 
        !this.expirationRisks.includes(risk) && 
        !this.complianceRisks.includes(risk)
      );
    }
  },
  
  methods: {
    async loadContractData() {
      if (!this.selectedContract) return;
      
      try {
        const response = await this.$http.get('/api/risk-analysis/entity-dropdown/', {
          params: { action: 'rows', table: 'contracts' }
        });
        
        const contract = response.data.rows.find(row => row.id === this.selectedContract);
        if (contract) {
          this.selectedContractData = contract.data;
        }
      } catch (error) {
        console.error('Failed to load contract data:', error);
      }
    },
    
    async generateContractRisks() {
      this.isGeneratingRisks = true;
      
      try {
        const response = await this.$http.post('/api/risk-analysis/entity-risk-generation/', {
          entity: 'contract_module',
          table: 'contracts',
          row_id: this.selectedContract
        });
        
        this.generatedRisks = response.data.risks || [];
        this.updateContractHealth();
        this.generateActionItems();
        this.$toast.success(`Generated ${this.generatedRisks.length} contract risks`);
        
      } catch (error) {
        console.error('Failed to generate contract risks:', error);
        this.$toast.error('Failed to generate contract risks');
      } finally {
        this.isGeneratingRisks = false;
      }
    },
    
    async generateComprehensiveRisks() {
      this.isGeneratingRisks = true;
      
      try {
        const response = await this.$http.post('/api/risk-analysis/entity-risk-generation/', {
          entity: 'contract_module',
          table: 'comprehensive_contract_data',
          row_id: this.selectedContract,
          comprehensive_data: {
            contract_info: this.selectedContractData,
            amendment_history: await this.getAmendmentHistory(),
            compliance_data: await this.getComplianceData(),
            performance_data: await this.getPerformanceData()
          }
        });
        
        this.generatedRisks = response.data.risks || [];
        this.updateContractHealth();
        this.generateActionItems();
        this.$toast.success(`Generated ${this.generatedRisks.length} comprehensive risks`);
        
      } catch (error) {
        console.error('Failed to generate comprehensive risks:', error);
        this.$toast.error('Failed to generate comprehensive risks');
      } finally {
        this.isGeneratingRisks = false;
      }
    },
    
    updateContractHealth() {
      // Update overall risk level
      if (this.riskCounts.critical > 0) {
        this.overallRiskLevel = 'Critical';
      } else if (this.riskCounts.high > 2) {
        this.overallRiskLevel = 'High';
      } else if (this.riskCounts.high > 0 || this.riskCounts.medium > 3) {
        this.overallRiskLevel = 'Medium';
      } else {
        this.overallRiskLevel = 'Low';
      }
      
      // Update compliance status
      if (this.complianceRisks.length > 0) {
        this.complianceStatus = 'Non-Compliant';
      } else {
        this.complianceStatus = 'Compliant';
      }
    },
    
    generateActionItems() {
      this.actionItems = [];
      
      // Add expiration-related actions
      if (this.getDaysToExpiration(this.selectedContractData?.end_date) < 90) {
        this.actionItems.push({
          id: 'renewal',
          priority: 'High',
          description: 'Contract renewal required within 90 days',
          deadline: this.formatDate(this.selectedContractData?.end_date)
        });
      }
      
      // Add compliance actions
      this.complianceRisks.forEach(risk => {
        if (risk.priority === 'Critical' || risk.priority === 'High') {
          this.actionItems.push({
            id: `compliance-${risk.id}`,
            priority: risk.priority,
            description: `Address compliance risk: ${risk.title}`,
            deadline: '30 days'
          });
        }
      });
    },
    
    getDaysToExpiration(endDate) {
      if (!endDate) return null;
      
      const today = new Date();
      const expiration = new Date(endDate);
      const diffTime = expiration - today;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      return diffDays;
    },
    
    getExpirationClass(endDate) {
      const days = this.getDaysToExpiration(endDate);
      if (days === null) return '';
      if (days < 30) return 'expiration-critical';
      if (days < 90) return 'expiration-warning';
      return 'expiration-good';
    },
    
    getRiskLevelClass(riskLevel) {
      return `risk-level-${riskLevel.toLowerCase()}`;
    },
    
    getComplianceClass(status) {
      return `compliance-${status.toLowerCase().replace('-', '')}`;
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
    // Load contract options
    try {
      const response = await this.$http.get('/api/risk-analysis/entity-dropdown/', {
        params: { action: 'tables', entity: 'contract_module' }
      });
      
      const contractTable = response.data.tables.find(t => t.table_name === 'contracts');
      if (contractTable) {
        const contractResponse = await this.$http.get('/api/risk-analysis/entity-dropdown/', {
          params: { action: 'rows', table: 'contracts' }
        });
        this.contractOptions = contractResponse.data.rows;
      }
    } catch (error) {
      console.error('Failed to load contract options:', error);
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

.contract-selection {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.contract-details {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: white;
  border-radius: 8px;
  border: 1px solid #ddd;
}

.contract-info {
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
.status-expired { color: #dc3545; }
.status-pending { color: #ffc107; }

.expiration-critical { color: #dc3545; font-weight: bold; }
.expiration-warning { color: #ffc107; font-weight: bold; }
.expiration-good { color: #28a745; }

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

.risk-categories {
  margin-top: 1rem;
}

.category-section {
  margin-bottom: 2rem;
}

.category-section h5 {
  color: #333;
  border-bottom: 2px solid #ddd;
  padding-bottom: 0.5rem;
  margin-bottom: 1rem;
}

.risk-item {
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 8px;
  border-left: 4px solid #ccc;
  background-color: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.expiration-risk { border-left-color: #ffc107; }
.compliance-risk { border-left-color: #17a2b8; }

.priority-critical { border-left-color: #dc3545; }
.priority-high { border-left-color: #fd7e14; }
.priority-medium { border-left-color: #ffc107; }
.priority-low { border-left-color: #28a745; }

.risk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.risk-title {
  font-weight: bold;
  font-size: 1.1rem;
}

.risk-priority {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
}

.contract-health-dashboard {
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

.compliance-compliant { color: #28a745; }
.compliance-noncompliant { color: #dc3545; }

.action-items {
  margin-top: 1rem;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.action-priority {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: bold;
  color: white;
}

.action-priority.High { background-color: #dc3545; }
.action-priority.Medium { background-color: #ffc107; color: #000; }
.action-priority.Low { background-color: #28a745; }
</style>
"""
