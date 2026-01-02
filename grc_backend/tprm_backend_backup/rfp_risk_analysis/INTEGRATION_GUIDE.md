# Risk Analysis Module Integration Guide

## Overview
This guide helps other module teams (Vendor, SLA, Contract, RFP) integrate the Risk Analysis module into their systems. The integration follows the **entity-data-row approach** that was successfully implemented with the BCP/DRP module.

## Integration Architecture

### Entity-Data-Row Approach
The risk analysis module uses a standardized approach where:
1. **Entity**: Logical module name (e.g., `vendor_management`, `sla_module`)
2. **Table**: Database table name containing your module's data
3. **Row**: Specific record ID from your table

This approach allows each module to integrate without modifying the risk analysis core code.

## Prerequisites: Llama Model Installation

Before integrating with the Risk Analysis module, you need to set up the Llama AI model for risk generation.

### Step 1: Install Ollama

**For Windows:**
1. Download Ollama from [https://ollama.ai/download](https://ollama.ai/download)
2. Run the installer (`OllamaSetup.exe`)
3. Ollama will automatically start as a service on port 11434

**For macOS:**
```bash
# Using Homebrew
brew install ollama

# Or download from https://ollama.ai/download
```

**For Linux:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama
```

### Step 2: Download Llama Model

After installing Ollama, download the Llama model:

```bash
# Download Llama 3.2 (3B parameters - recommended for most systems)
ollama pull llama3.2:3b

# Alternative: Llama 3.2 (1B parameters - for resource-constrained systems)
ollama pull llama3.2:1b

# Alternative: Llama 2 (7B parameters - for high-performance systems)
ollama pull llama2:7b
```

### Step 3: Verify Installation

Test that Ollama and the model are working:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test the model
ollama run llama3.2:3b "Hello, can you analyze risks?"
```

### Step 4: Configure Django Settings

Add Ollama configuration to your Django `settings.py`:

```python
# Ollama Configuration for Risk Analysis
OLLAMA_URL = 'http://localhost:11434'
LLAMA_MODEL_NAME = 'llama3.2:3b'  # or 'llama3.2:1b', 'llama2:7b'

# Optional: Custom timeout settings
OLLAMA_TIMEOUT = 300  # 5 minutes for complex analysis
```

### Step 5: Install Python Dependencies

Ensure your `requirements.txt` includes the necessary packages:

```txt
Django>=5.0.0
djangorestframework>=3.14.0
requests>=2.31.0
# ... other dependencies
```

### Troubleshooting

**Common Issues:**

1. **Ollama not responding:**
   - Check if Ollama service is running: `ollama ps`
   - Restart Ollama service if needed

2. **Model not found:**
   - Verify model is downloaded: `ollama list`
   - Re-download if needed: `ollama pull llama3.2:3b`

3. **Connection errors:**
   - Ensure port 11434 is not blocked by firewall
   - Check OLLAMA_URL setting matches your Ollama installation

4. **Memory issues:**
   - Use smaller model: `llama3.2:1b` instead of `llama3.2:3b`
   - Ensure system has sufficient RAM (4GB+ recommended)

## Integration Steps

### Step 1: Update Entity Mappings
Edit `backend/risk_analysis/entity_service.py` and add your module's tables:

```python
# In EntityDataService.__init__(), update entity_table_mappings:
self.entity_table_mappings = {
    'vendor_management': ['vendor_profiles', 'vendor_assessments'],  # ADD YOUR TABLES
    'rfp_module': ['rfp_requests', 'rfp_responses'],                 # ADD YOUR TABLES
    'contract_module': ['contracts', 'contract_amendments'],         # ADD YOUR TABLES
    'sla_module': ['sla_agreements', 'sla_performance'],             # ADD YOUR TABLES
    'bcp_drp_module': ['bcp_drp_plans', 'bcp_drp_evaluations']      # EXISTING
}

# Update entity display names:
self.entity_display_names = {
    'vendor_management': 'Vendor Management',
    'rfp_module': 'RFP Module', 
    'contract_module': 'Contract Module',
    'sla_module': 'SLA Module',
    'bcp_drp_module': 'BCP/DRP Module'
}

# Update LLaMA service mapping:
self.entity_llama_mapping = {
    'vendor_management': 'Vendor',      # For AI prompt generation
    'rfp_module': 'RFP',
    'contract_module': 'Contract', 
    'sla_module': 'SLA',
    'bcp_drp_module': 'BCP_DRP'
}
```

### Step 2: Add Data Retrieval Methods
In `backend/risk_analysis/entity_service.py`, add methods to fetch your module's data:

```python
def get_rows_for_table(self, table_name: str, limit: int = 100) -> List[Dict]:
    """Get list of rows from a specific table for selection"""
    try:
        if table_name == 'bcp_drp_plans':
            return self._get_bcp_drp_plans()
        elif table_name == 'bcp_drp_evaluations':
            return self._get_bcp_drp_evaluations()
        # ADD YOUR MODULE METHODS HERE:
        elif table_name == 'vendor_profiles':
            return self._get_vendor_profiles()
        elif table_name == 'contracts':
            return self._get_contracts()
        # ... add more as needed
        else:
            raise ValueError(f"Table '{table_name}' not supported")

def _get_vendor_profiles(self) -> List[Dict]:
    """Example: Get vendor profiles for risk analysis"""
    try:
        # Import your module's models
        from vendor_module.models import VendorProfile  # REPLACE WITH YOUR MODEL
        
        # Use Django ORM to get data
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
```

### Step 3: Integrate in Your Module's Views
In your module's views (e.g., `vendor_module/views.py`), add risk generation:

```python
from risk_analysis.services import RiskAnalysisService

def save_vendor_assessment(request):
    """Example: Save vendor assessment and generate risks"""
    # Your existing save logic here...
    
    # After successful save, generate risks
    if assessment.status == 'COMPLETED':
        try:
            risk_service = RiskAnalysisService()
            
            # Generate risks for this specific vendor assessment
            result = risk_service.analyze_entity_data_row(
                entity='vendor_management',
                table='vendor_assessments', 
                row_id=assessment.assessment_id
            )
            
            # Handle the response
            risks = result.get('risks', [])
            logger.info(f"Generated {len(risks)} risks for vendor assessment {assessment.assessment_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate risks: {e}")
            # Don't fail the main operation if risk generation fails
```

### Step 4: Add Frontend Integration
In your module's frontend, add risk analytics integration:

```javascript
// Example: Add to your Vue component
methods: {
    async generateRisks(vendorId) {
        try {
            const response = await this.$http.post('/api/risk-analysis/entity-risk-generation/', {
                entity: 'vendor_management',
                table: 'vendor_profiles',
                row_id: vendorId
            });
            
            const risks = response.data.risks;
            this.showRiskResults(risks);
        } catch (error) {
            console.error('Failed to generate risks:', error);
        }
    },
    
    async showRiskResults(risks) {
        // Display risks in a modal or new page
        // You can reuse the RiskAnalytics.vue component
    }
}
```

## API Endpoints Available

### 1. Entity Dropdown API
```
GET /api/risk-analysis/entity-dropdown/?action=entities
GET /api/risk-analysis/entity-dropdown/?action=tables&entity=vendor_management
GET /api/risk-analysis/entity-dropdown/?action=rows&table=vendor_profiles
```

### 2. Risk Generation API
```
POST /api/risk-analysis/entity-risk-generation/
{
    "entity": "vendor_management",
    "table": "vendor_profiles", 
    "row_id": "123"
}
```

### 3. Dashboard API
```
GET /api/risk-analysis/dashboard/
```

## BCP/DRP Integration Examples

### Example 1: Plan Evaluation Integration
The BCP/DRP module generates risks when an evaluation is completed:

```python
# In bcpdrp/views.py (lines 1440-1500)
def save_evaluation(request, plan_id):
    # ... save evaluation logic ...
    
    # Generate comprehensive risks after evaluation save
    if evaluation_data.get('is_final_submission', False):
        try:
            # Use background task for comprehensive risk generation
            task = generate_comprehensive_risks_for_evaluation.delay(
                plan_id=plan_id,
                evaluation_id=evaluation.evaluation_id
            )
            
            response_data['risk_generation'] = {
                'task_id': task.id,
                'status': 'started',
                'message': 'Comprehensive risk generation started in background'
            }
        except Exception as e:
            logger.warning(f"Background task system not available: {e}")
```

### Example 2: Entity Service Implementation
The BCP/DRP integration shows how to implement data retrieval:

```python
# In risk_analysis/entity_service.py (lines 111-167)
def _get_bcp_drp_plans(self) -> List[Dict]:
    """Get BCP/DRP plans using direct database access"""
    try:
        # Use Django ORM to get plans directly from database
        plans = Plan.objects.all().values(
            'plan_id', 'plan_name', 'plan_type', 'strategy_name', 
            'version', 'status', 'criticality', 'document_date'
        )
        
        result = []
        for plan in plans:
            display_text = f"Plan {plan['plan_id']} - {plan['plan_name']} ({plan['plan_type']})"
            result.append({
                'id': plan['plan_id'],
                'display_text': display_text,
                'data': plan
            })
        
        return result
    except Exception as e:
        logger.error(f"Error fetching BCP/DRP plans: {e}")
        return []
```

## Testing Your Integration

### 1. Test Entity Dropdown
```bash
# Test if your entity appears
curl "http://localhost:8000/api/risk-analysis/entity-dropdown/?action=entities"

# Test if your tables appear
curl "http://localhost:8000/api/risk-analysis/entity-dropdown/?action=tables&entity=vendor_management"

# Test if your data appears
curl "http://localhost:8000/api/risk-analysis/entity-dropdown/?action=rows&table=vendor_profiles"
```

### 2. Test Risk Generation
```bash
curl -X POST "http://localhost:8000/api/risk-analysis/entity-risk-generation/" \
  -H "Content-Type: application/json" \
  -d '{
    "entity": "vendor_management",
    "table": "vendor_profiles",
    "row_id": "123"
  }'
```

## Common Patterns

### Pattern 1: Background Risk Generation
Use Celery tasks for heavy risk generation:

```python
from celery import shared_task
from risk_analysis.services import RiskAnalysisService

@shared_task
def generate_risks_for_vendor_assessment(vendor_id):
    """Background task to generate risks for vendor assessment"""
    try:
        service = RiskAnalysisService()
        result = service.analyze_entity_data_row(
            entity='vendor_management',
            table='vendor_assessments',
            row_id=vendor_id
        )
        return result
    except Exception as e:
        logger.error(f"Failed to generate risks for vendor {vendor_id}: {e}")
        raise
```

### Pattern 2: Comprehensive Data Analysis
For complex modules with multiple related tables:

```python
def generate_comprehensive_risks(vendor_id):
    """Generate risks using multiple related data sources"""
    try:
        # Get comprehensive vendor data
        vendor_data = get_vendor_comprehensive_data(vendor_id)
        
        # Generate risks using comprehensive service
        service = RiskAnalysisService()
        result = service.analyze_comprehensive_plan_data(
            entity='vendor_management',
            comprehensive_data=vendor_data
        )
        
        return result
    except Exception as e:
        logger.error(f"Failed to generate comprehensive risks: {e}")
        raise
```

## Current System Configuration

The BCP/DRP system is currently configured with:
- **Ollama Version**: Latest stable
- **Model**: `llama3.2:3b` (3 billion parameters)
- **Host**: `http://localhost:11434`
- **Performance**: Optimized for risk analysis with specialized prompts
- **Response Time**: ~30-60 seconds per risk generation request

## Model Performance Notes

**Llama 3.2:3b** provides the best balance of:
- **Accuracy**: High-quality risk analysis with detailed explanations
- **Speed**: Reasonable response times for interactive use
- **Resource Usage**: Moderate memory requirements (4-8GB RAM recommended)
- **Reliability**: Stable performance for production workloads

## Troubleshooting

### Common Issues

1. **Entity not found**: Make sure you've added your entity to `entity_table_mappings`
2. **Table not found**: Ensure your table name is added to the entity's table list
3. **Data not loading**: Check your `_get_*` methods are properly implemented
4. **Import errors**: Make sure your module models are importable

### Debug Steps

1. Check logs for error messages
2. Test entity dropdown endpoints manually
3. Verify your Django models are accessible
4. Test with a simple row first

## Support

For integration support:
1. Check the BCP/DRP integration examples in this codebase
2. Review the entity_service.py implementation
3. Test with the provided API endpoints
4. Follow the established patterns in this guide

## Next Steps

After integration:
1. Test thoroughly with your module's data
2. Add frontend components for risk display
3. Configure risk notifications/alerts
4. Set up monitoring for risk generation tasks
