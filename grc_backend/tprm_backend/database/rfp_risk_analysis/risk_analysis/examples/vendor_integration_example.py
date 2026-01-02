"""
VENDOR MODULE INTEGRATION EXAMPLE
=================================

This file shows how to integrate the Risk Analysis module with a Vendor Management module.
Use this as a template for your vendor module integration.

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
    'vendor_management': ['vendor_profiles', 'vendor_assessments', 'vendor_contracts'],
    # ... other modules
}

self.entity_display_names = {
    'vendor_management': 'Vendor Management',
    # ... other modules  
}

self.entity_llama_mapping = {
    'vendor_management': 'Vendor',
    # ... other modules
}

# In get_rows_for_table method, add:
elif table_name == 'vendor_profiles':
    return self._get_vendor_profiles()
elif table_name == 'vendor_assessments':
    return self._get_vendor_assessments()
elif table_name == 'vendor_contracts':
    return self._get_vendor_contracts()

# Add these methods to EntityDataService class:
def _get_vendor_profiles(self) -> List[Dict]:
    try:
        from vendor_module.models import VendorProfile
        profiles = VendorProfile.objects.all().values(
            'vendor_id', 'vendor_name', 'vendor_type', 'status', 'risk_level'
        )
        
        result = []
        for profile in profiles:
            display_text = f"Vendor {profile['vendor_id']} - {profile['vendor_name']} ({profile['vendor_type']})"
            result.append({
                'id': profile['vendor_id'],
                'display_text': display_text,
                'data': profile
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching vendor profiles: {e}")
        return []

def _get_vendor_assessments(self) -> List[Dict]:
    try:
        from vendor_module.models import VendorAssessment
        assessments = VendorAssessment.objects.all().values(
            'assessment_id', 'vendor_id', 'assessment_type', 'status', 'score'
        )
        
        result = []
        for assessment in assessments:
            display_text = f"Assessment {assessment['assessment_id']} - Vendor {assessment['vendor_id']} (Score: {assessment['score']})"
            result.append({
                'id': assessment['assessment_id'],
                'display_text': display_text,
                'data': assessment
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching vendor assessments: {e}")
        return []
"""

# ============================================================================
# STEP 2: INTEGRATE IN YOUR VENDOR VIEWS
# ============================================================================

# In your vendor_module/views.py:
from risk_analysis.services import RiskAnalysisService
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

def save_vendor_assessment(request, vendor_id):
    """
    Example: Save vendor assessment and generate risks
    """
    try:
        # Your existing save logic here...
        assessment_data = request.data
        assessment = save_assessment_to_database(assessment_data)
        
        # Generate risks after successful save
        if assessment.status == 'COMPLETED':
            try:
                # Generate risks using background task for better performance
                task = generate_risks_for_vendor_assessment.delay(
                    vendor_id=vendor_id,
                    assessment_id=assessment.assessment_id
                )
                
                response_data = {
                    'assessment_id': assessment.assessment_id,
                    'status': 'completed',
                    'risk_generation_task': task.id,
                    'message': 'Assessment saved and risk generation started'
                }
                
            except Exception as e:
                logger.error(f"Failed to start risk generation: {e}")
                response_data = {
                    'assessment_id': assessment.assessment_id,
                    'status': 'completed',
                    'message': 'Assessment saved (risk generation failed)'
                }
        else:
            response_data = {
                'assessment_id': assessment.assessment_id,
                'status': assessment.status,
                'message': 'Assessment saved'
            }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error saving vendor assessment: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@shared_task
def generate_risks_for_vendor_assessment(vendor_id, assessment_id):
    """
    Background task to generate risks for vendor assessment
    """
    try:
        service = RiskAnalysisService()
        
        # Generate risks for the vendor assessment
        result = service.analyze_entity_data_row(
            entity='vendor_management',
            table='vendor_assessments',
            row_id=assessment_id
        )
        
        risks = result.get('risks', [])
        logger.info(f"Generated {len(risks)} risks for vendor assessment {assessment_id}")
        
        # You can also generate risks for the vendor profile itself
        vendor_result = service.analyze_entity_data_row(
            entity='vendor_management',
            table='vendor_profiles',
            row_id=vendor_id
        )
        
        vendor_risks = vendor_result.get('risks', [])
        logger.info(f"Generated {len(vendor_risks)} risks for vendor profile {vendor_id}")
        
        return {
            'assessment_risks': len(risks),
            'vendor_risks': len(vendor_risks),
            'total_risks': len(risks) + len(vendor_risks)
        }
        
    except Exception as e:
        logger.error(f"Failed to generate risks for vendor {vendor_id}: {e}")
        raise

def generate_comprehensive_vendor_risks(vendor_id):
    """
    Generate comprehensive risks using multiple vendor data sources
    """
    try:
        # Get comprehensive vendor data
        vendor_data = get_vendor_comprehensive_data(vendor_id)
        
        # Generate risks using comprehensive service
        service = RiskAnalysisService()
        result = service.analyze_comprehensive_plan_data(
            entity='vendor_management',
            comprehensive_data=vendor_data
        )
        
        risks = result.get('risks', [])
        logger.info(f"Generated {len(risks)} comprehensive risks for vendor {vendor_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate comprehensive vendor risks: {e}")
        raise

# ============================================================================
# STEP 3: FRONTEND INTEGRATION
# ============================================================================

# In your Vue component (e.g., VendorAssessment.vue):
"""
<template>
  <div class="vendor-assessment">
    <!-- Your existing assessment form -->
    
    <!-- Risk Generation Section -->
    <div class="risk-generation-section" v-if="showRiskSection">
      <h3>Risk Analysis</h3>
      
      <div class="risk-controls">
        <button @click="generateRisks" :disabled="isGeneratingRisks">
          {{ isGeneratingRisks ? 'Generating Risks...' : 'Generate Risks' }}
        </button>
        
        <button @click="viewAllRisks" v-if="hasRisks">
          View All Vendor Risks
        </button>
      </div>
      
      <!-- Risk Results -->
      <div class="risk-results" v-if="generatedRisks.length > 0">
        <h4>Generated Risks ({{ generatedRisks.length }})</h4>
        <div class="risk-list">
          <div 
            v-for="risk in generatedRisks" 
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
              <h5>Suggested Mitigations:</h5>
              <ul>
                <li v-for="mitigation in risk.suggested_mitigations" :key="mitigation">
                  {{ mitigation }}
                </li>
              </ul>
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
      vendorId: null,
      assessmentId: null,
      isGeneratingRisks: false,
      generatedRisks: [],
      hasRisks: false
    }
  },
  
  methods: {
    async generateRisks() {
      if (!this.vendorId) {
        this.$toast.error('Vendor ID is required');
        return;
      }
      
      this.isGeneratingRisks = true;
      
      try {
        // Generate risks for vendor assessment
        const response = await this.$http.post('/api/risk-analysis/entity-risk-generation/', {
          entity: 'vendor_management',
          table: 'vendor_assessments',
          row_id: this.assessmentId
        });
        
        this.generatedRisks = response.data.risks || [];
        this.hasRisks = this.generatedRisks.length > 0;
        
        if (this.generatedRisks.length > 0) {
          this.$toast.success(`Generated ${this.generatedRisks.length} risks successfully`);
        } else {
          this.$toast.info('No risks were generated for this assessment');
        }
        
      } catch (error) {
        console.error('Failed to generate risks:', error);
        this.$toast.error('Failed to generate risks');
      } finally {
        this.isGeneratingRisks = false;
      }
    },
    
    async viewAllRisks() {
      // Navigate to risk analytics page or open modal
      this.$router.push({
        name: 'RiskAnalytics',
        query: { entity: 'vendor_management', entity_id: this.vendorId }
      });
    },
    
    async loadVendorRisks() {
      // Load existing risks for this vendor
      try {
        const response = await this.$http.get('/api/risk-analysis/risks/', {
          params: {
            entity: 'vendor_management',
            entity_id: this.vendorId
          }
        });
        
        this.existingRisks = response.data.results || [];
      } catch (error) {
        console.error('Failed to load vendor risks:', error);
      }
    }
  },
  
  mounted() {
    this.vendorId = this.$route.params.vendorId;
    this.assessmentId = this.$route.params.assessmentId;
    this.loadVendorRisks();
  }
}
</script>

<style scoped>
.risk-generation-section {
  margin-top: 2rem;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.risk-controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.risk-item {
  margin-bottom: 1rem;
  padding: 1rem;
  border-radius: 4px;
  border-left: 4px solid #ccc;
}

.priority-critical {
  border-left-color: #dc3545;
  background-color: #f8d7da;
}

.priority-high {
  border-left-color: #fd7e14;
  background-color: #fff3cd;
}

.priority-medium {
  border-left-color: #ffc107;
  background-color: #fff3cd;
}

.priority-low {
  border-left-color: #28a745;
  background-color: #d4edda;
}

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

.risk-score {
  font-size: 0.9rem;
  color: #666;
}
</style>
"""

# ============================================================================
# STEP 4: API INTEGRATION EXAMPLES
# ============================================================================

# Test your integration with these API calls:

"""
# Test entity dropdown
curl "http://localhost:8000/api/risk-analysis/entity-dropdown/?action=entities"
curl "http://localhost:8000/api/risk-analysis/entity-dropdown/?action=tables&entity=vendor_management"
curl "http://localhost:8000/api/risk-analysis/entity-dropdown/?action=rows&table=vendor_profiles"

# Test risk generation
curl -X POST "http://localhost:8000/api/risk-analysis/entity-risk-generation/" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "vendor_management",
    "table": "vendor_profiles",
    "row_id": "123"
  }'

# Test comprehensive risk generation
curl -X POST "http://localhost:8000/api/risk-analysis/entity-risk-generation/" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "vendor_management",
    "table": "comprehensive_vendor_data",
    "row_id": "123",
    "comprehensive_data": {
      "vendor_info": {...},
      "assessment_data": {...},
      "contract_data": {...}
    }
  }'
"""

# ============================================================================
# STEP 5: MONITORING AND LOGGING
# ============================================================================

# Add logging to track risk generation:
"""
import logging

logger = logging.getLogger(__name__)

# In your risk generation functions:
logger.info(f"Starting risk generation for vendor {vendor_id}")
logger.info(f"Generated {len(risks)} risks for vendor assessment {assessment_id}")
logger.error(f"Failed to generate risks for vendor {vendor_id}: {error}")

# Monitor risk generation tasks:
from celery.result import AsyncResult

def check_risk_generation_status(task_id):
    task_result = AsyncResult(task_id)
    return {
        'status': task_result.status,
        'ready': task_result.ready(),
        'result': task_result.result if task_result.ready() else None
    }
"""
