import json
import logging
from django.conf import settings
from django.utils import timezone
from django.db import models
from typing import Dict, List, Tuple, Optional
from .models import Risk
from .llama_service import LlamaService
from .entity_service import EntityDataService
# VendorRiskService import removed - using RiskAnalysisService methods instead

logger = logging.getLogger(__name__)    


class RiskAnalysisService:
    """
    Service for risk analysis operations - Microservice approach
    
    INTEGRATION GUIDE FOR OTHER MODULES:
    ====================================
    
    This is the MAIN SERVICE CLASS that other modules should use for risk generation.
    It provides the standardized interface for analyzing entity data and generating risks.
    
    USAGE FROM YOUR MODULE:
    ----------------------
    
    # Import the service
    from risk_analysis_vendor.services import RiskAnalysisService
    
    # Create service instance
    risk_service = RiskAnalysisService()
    
    # Generate risks for your module's data
    result = risk_service.analyze_entity_data_row(
        entity='your_module_name',      # e.g., 'vendor_management', 'sla_module'
        table='your_table_name',        # e.g., 'vendor_profiles', 'contracts'
        row_id='your_row_id'           # e.g., '123', 'ABC-456'
    )
    
    # Process the results
    risks = result.get('risks', [])
    for risk in risks:
        print(f"Risk: {risk['title']} - Priority: {risk['priority']}")
    
    # For comprehensive data analysis (multiple related tables):
    result = risk_service.analyze_comprehensive_plan_data(
        entity='your_module_name',
        comprehensive_data={
            'main_info': {...},
            'related_data': {...},
            'additional_data': {...}
        }
    )
    
    See INTEGRATION_GUIDE.md for complete integration examples!
    """
    
    def __init__(self):
        self.llama_service = LlamaService()
        self.entity_service = EntityDataService()
    
    def analyze_module_data(self, module_data) -> List[Risk]:
        """
        Analyze module data and create risks directly from Llama (legacy method)
        
        Args:
            module_data: Legacy module data object (deprecated - use entity-data-row approach)
            
        Returns:
            List of created Risk instances
        """
        try:
            # Create risks directly using the simple approach
            created_risks = self.llama_service.create_risks_directly(module_data)
            
            logger.info(f"Created {len(created_risks)} risks from module data {module_data.id}")
            return created_risks
            
        except Exception as e:
            logger.error(f"Error analyzing module data: {str(e)}")
            raise
    
    def analyze_entity_data_row(self, entity: str, table: str, row_id: str) -> Dict:
        """
        Main microservice function to analyze entity data row and return standardized risk response
        
        INTEGRATION GUIDE FOR OTHER MODULES:
        ====================================
        
        This is the PRIMARY METHOD that other modules should call to generate risks.
        It handles the complete workflow from data retrieval to risk generation.
        
        WORKFLOW:
        1. Validates input parameters (entity, table, row_id)
        2. Retrieves full row data using EntityDataService
        3. Generates risks using LLaMA AI service
        4. Returns standardized risk response format
        
        Args:
            entity: logical module name (e.g., 'vendor_management', 'sla_module', 'contract_module')
            table: mapped DB table name (e.g., 'vendor_profiles', 'contracts', 'sla_agreements')
            row_id: primary key of the row to analyze (e.g., '123', 'VENDOR-456')
            
        Returns:
            Standardized risk response dictionary:
            {
                "risks": [
                    {
                        "id": "R-0105",
                        "title": "Risk Title",
                        "description": "Risk description",
                        "likelihood": 4,
                        "impact": 5,
                        "exposure_rating": 3,
                        "score": 80,
                        "priority": "Critical",
                        "ai_explanation": "AI-generated explanation...",
                        "suggested_mitigations": ["Mitigation 1", "Mitigation 2"]
                    }
                ]
            }
        
        EXAMPLE USAGE:
        --------------
        # In your module's code:
        from risk_analysis_vendor.services import RiskAnalysisService
        
        service = RiskAnalysisService()
        result = service.analyze_entity_data_row(
            entity='vendor_management',
            table='vendor_profiles',
            row_id='123'
        )
        
        risks = result.get('risks', [])
        print(f"Generated {len(risks)} risks")
        for risk in risks:
            print(f"- {risk['title']} ({risk['priority']})")
        """
        try:
            # Validate input parameters
            if not all([entity, table, row_id]):
                raise ValueError("entity, table, and row_id are required")
            
            # Get full row data using entity service
            row_data = self.entity_service.get_full_row_data(table, row_id)
            
            # Generate risks using LLaMA service
            created_risks = self.llama_service.create_risks_from_entity_data_row(
                entity=entity,
                table_name=table,
                row_data=row_data
            )
            
            # Convert Risk objects to standardized format
            risks_response = []
            for risk in created_risks:
                risk_dict = {
                    "id": risk.id,
                    "title": risk.title,
                    "description": risk.description,
                    "likelihood": risk.likelihood,
                    "impact": risk.impact,
                    "exposure_rating": risk.exposure_rating,
                    "score": risk.score,
                    "priority": risk.priority,
                    "ai_explanation": risk.ai_explanation,
                    "suggested_mitigations": risk.suggested_mitigations or [],
                    "entity": risk.entity,
                    "data": risk.data,
                    "row": risk.row
                }
                risks_response.append(risk_dict)
            
            logger.info(f"Generated {len(risks_response)} risks for {entity} {table} row {row_id}")
            
            return {
                "risks": risks_response
            }
            
        except Exception as e:
            logger.error(f"Error analyzing entity data row {entity}/{table}/{row_id}: {str(e)}")
            raise
    
    
    def get_heatmap_data(self, module_name: str = None) -> List[Dict]:
        """Get heatmap data dynamically from risk records"""
        try:
            heatmap_data = Risk.get_heatmap_data(module_name)
            logger.info(f"Generated heatmap data for {len(heatmap_data)} cells")
            return heatmap_data
        except Exception as e:
            logger.error(f"Error generating heatmap data: {str(e)}")
            raise
    
    def get_risk_statistics(self, module_name: str = None) -> Dict:
        """Get risk statistics for dashboard"""
        try:
            # For now, get all risks since we're not using module filtering
            risks = Risk.objects.all()
            
            total_risks = risks.count()
            
            if total_risks == 0:
                return {
                    'total_risks': 0,
                    'critical_risks': 0,
                    'high_risks': 0,
                    'medium_risks': 0,
                    'low_risks': 0,
                    'open_risks': 0,
                    'average_score': 0
                }
            
            stats = {
                'total_risks': total_risks,
                'critical_risks': risks.filter(priority='Critical').count(),
                'high_risks': risks.filter(priority='High').count(),
                'medium_risks': risks.filter(priority='Medium').count(),
                'low_risks': risks.filter(priority='Low').count(),
                'open_risks': risks.filter(status='Open').count(),
                'average_score': risks.aggregate(avg_score=models.Avg('score'))['avg_score'] or 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting risk statistics: {str(e)}")
            return {}
    
    def generate_vendor_risks(self, approval_id: str) -> Dict:
        """
        Generate vendor risks from questionnaire approval (synchronous)
        
        Args:
            approval_id: The approval request ID that was just approved
            
        Returns:
            Standardized risk response dictionary
        """
        try:
            logger.info(f"🔵 [RISK GENERATION] Starting generate_vendor_risks for approval: {approval_id}")
            print(f"🔵 [RISK GENERATION] Starting generate_vendor_risks for approval: {approval_id}")
            
            # Get vendor data from approval request
            # Use tprm connection for consistency
            from django.db import connections as db_connections
            if 'tprm' in db_connections.databases:
                db_connection = db_connections['tprm']
            else:
                db_connection = db_connections['default']
            
            logger.info(f"🔵 [RISK GENERATION] Using database connection: {db_connection.settings_dict.get('NAME', 'unknown')}")
            print(f"🔵 [RISK GENERATION] Using database connection: {db_connection.settings_dict.get('NAME', 'unknown')}")
            
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT request_data FROM approval_requests 
                    WHERE approval_id = %s
                """, [approval_id])
                
                result = cursor.fetchone()
                if not result:
                    error_msg = f'Approval request {approval_id} not found'
                    logger.error(f"❌ [RISK GENERATION] {error_msg}")
                    print(f"❌ [RISK GENERATION] {error_msg}")
                    return {
                        'status': 'error',
                        'error': error_msg
                    }
                
                request_data = result[0]
                if isinstance(request_data, str):
                    import json
                    request_data = json.loads(request_data)
                
                logger.info(f"🔵 [RISK GENERATION] Retrieved approval request data for {approval_id}")
                print(f"🔵 [RISK GENERATION] Retrieved approval request data for {approval_id}")
                
                # Extract vendor information
                rd = request_data.get('request_data', request_data)
                vendor_id = rd.get('vendor_id')
                approval_type = rd.get('approval_type', '').lower()
                
                logger.info(f"🔵 [RISK GENERATION] Extracted approval_type: {approval_type}, initial vendor_id: {vendor_id}")
                print(f"🔵 [RISK GENERATION] Extracted approval_type: {approval_type}, initial vendor_id: {vendor_id}")
                
                # For response_approval, check vendor_information
                if not vendor_id and approval_type == 'response_approval' and 'vendor_information' in rd:
                    vendor_info = rd['vendor_information']
                    if isinstance(vendor_info, dict):
                        vendor_id = vendor_info.get('vendor_id') or vendor_info.get('id')
                        logger.info(f"🔵 [RISK GENERATION] Found vendor_id from vendor_information: {vendor_id}")
                        print(f"🔵 [RISK GENERATION] Found vendor_id from vendor_information: {vendor_id}")
                
                # For response_approval, also check assignment_summary
                if not vendor_id and approval_type == 'response_approval' and 'assignment_summary' in rd:
                    assignment_summary = rd['assignment_summary']
                    if isinstance(assignment_summary, dict):
                        vendor_id = assignment_summary.get('vendor_id') or assignment_summary.get('vendor_temp_id')
                        logger.info(f"🔵 [RISK GENERATION] Found vendor_id from assignment_summary: {vendor_id}")
                        print(f"🔵 [RISK GENERATION] Found vendor_id from assignment_summary: {vendor_id}")
                
                # Also check vendor_data for response approvals
                if not vendor_id and approval_type == 'response_approval' and 'vendor_data' in rd:
                    vendor_data = rd['vendor_data']
                    if isinstance(vendor_data, dict):
                        vendor_id = vendor_data.get('vendor_id') or vendor_data.get('id')
                        logger.info(f"🔵 [RISK GENERATION] Found vendor_id from vendor_data: {vendor_id}")
                        print(f"🔵 [RISK GENERATION] Found vendor_id from vendor_data: {vendor_id}")
                
                if not vendor_id:
                    error_msg = f'No vendor_id found in approval request {approval_id} (approval_type: {approval_type})'
                    logger.error(f"❌ [RISK GENERATION] {error_msg}")
                    print(f"❌ [RISK GENERATION] {error_msg}")
                    print(f"❌ [RISK GENERATION] Available keys in rd: {list(rd.keys())}")
                    return {
                        'status': 'error',
                        'error': error_msg
                    }
                
                logger.info(f"✅ [RISK GENERATION] Using vendor_id: {vendor_id} for risk generation")
                print(f"✅ [RISK GENERATION] Using vendor_id: {vendor_id} for risk generation")
                
                # Try to generate risks using the existing risk analysis service
                try:
                    logger.info(f"🔵 [RISK GENERATION] Attempting to analyze entity data row for vendor {vendor_id}")
                    print(f"🔵 [RISK GENERATION] Attempting to analyze entity data row for vendor {vendor_id}")
                    risk_result = self.analyze_entity_data_row(
                        entity='vendor_management',
                        table='temp_vendor',
                        row_id=str(vendor_id)
                    )
                    logger.info(f"✅ [RISK GENERATION] Successfully analyzed entity data row, got {len(risk_result.get('risks', []))} risks")
                    print(f"✅ [RISK GENERATION] Successfully analyzed entity data row, got {len(risk_result.get('risks', []))} risks")
                except Exception as e:
                    import traceback
                    error_trace = traceback.format_exc()
                    logger.warning(f"⚠️ [RISK GENERATION] LLaMA API failed for vendor {vendor_id}, creating basic risks: {str(e)}")
                    logger.warning(f"⚠️ [RISK GENERATION] LLaMA error traceback: {error_trace}")
                    print(f"⚠️ [RISK GENERATION] LLaMA API failed for vendor {vendor_id}, creating basic risks: {str(e)}")
                    print(f"⚠️ [RISK GENERATION] LLaMA error traceback: {error_trace}")
                    # Create basic risks when LLaMA API is not available
                    risk_result = self._create_basic_vendor_risks(vendor_id, approval_id)
                    logger.info(f"✅ [RISK GENERATION] Created basic risks, got {len(risk_result.get('risks', []))} risks")
                    print(f"✅ [RISK GENERATION] Created basic risks, got {len(risk_result.get('risks', []))} risks")
                
                # Process and save the risks
                risks_created = 0
                if risk_result.get('risks'):
                    logger.info(f"🔵 [RISK GENERATION] Processing {len(risk_result['risks'])} risks for saving")
                    print(f"🔵 [RISK GENERATION] Processing {len(risk_result['risks'])} risks for saving")
                    
                    for idx, risk_data in enumerate(risk_result['risks']):
                        try:
                            # Create risk record in database
                            risk = Risk.objects.create(
                                title=risk_data.get('title', 'Vendor Risk'),
                                description=risk_data.get('description', ''),
                                likelihood=risk_data.get('likelihood', 1),
                                impact=risk_data.get('impact', 1),
                                exposure_rating=risk_data.get('exposure_rating', 1),
                                score=risk_data.get('score', 0),
                                priority=risk_data.get('priority', 'Low'),
                                ai_explanation=risk_data.get('ai_explanation', ''),
                                suggested_mitigations=json.dumps(risk_data.get('suggested_mitigations', [])),
                                entity='vendor_management',
                                data='temp_vendor',
                                row=str(vendor_id),
                                status='Open',  # Default status for new risks
                                created_at=timezone.now(),
                                updated_at=timezone.now()
                            )
                            risks_created += 1
                            logger.debug(f"✅ [RISK GENERATION] Created risk {idx + 1}/{len(risk_result['risks'])}: {risk.title}")
                        except Exception as risk_error:
                            import traceback
                            logger.error(f"❌ [RISK GENERATION] Failed to create risk {idx + 1}: {str(risk_error)}")
                            logger.error(f"❌ [RISK GENERATION] Risk creation traceback: {traceback.format_exc()}")
                            print(f"❌ [RISK GENERATION] Failed to create risk {idx + 1}: {str(risk_error)}")
                
                logger.info(f"✅ [RISK GENERATION] Generated {risks_created} vendor risks for approval {approval_id}")
                print(f"✅ [RISK GENERATION] Generated {risks_created} vendor risks for approval {approval_id}")
                return {
                    'status': 'success',
                    'approval_id': approval_id,
                    'vendor_id': vendor_id,
                    'risks_created': risks_created,
                    'risks': risk_result.get('risks', [])
                }
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"❌ [RISK GENERATION] Error generating vendor risks for approval {approval_id}: {str(e)}")
            logger.error(f"❌ [RISK GENERATION] Error traceback: {error_trace}")
            print(f"❌ [RISK GENERATION] Error generating vendor risks for approval {approval_id}: {str(e)}")
            print(f"❌ [RISK GENERATION] Error traceback: {error_trace}")
            return {
                'status': 'error',
                'approval_id': approval_id,
                'error': str(e)
            }
    
    def _create_basic_vendor_risks(self, vendor_id: int, approval_id: str) -> Dict:
        """
        Create basic vendor risks when LLaMA API is not available
        """
        try:
            logger.info(f"🔵 [RISK GENERATION] Creating basic vendor risks for vendor {vendor_id}")
            print(f"🔵 [RISK GENERATION] Creating basic vendor risks for vendor {vendor_id}")
            
            # Get vendor data for context
            # Use tprm connection for consistency
            from django.db import connections as db_connections
            if 'tprm' in db_connections.databases:
                db_connection = db_connections['tprm']
            else:
                db_connection = db_connections['default']
            
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT company_name, business_type, industry_sector, risk_level, 
                           is_critical_vendor, has_data_access, has_system_access
                    FROM temp_vendor WHERE id = %s
                """, [vendor_id])
                
                vendor_data = cursor.fetchone()
                if not vendor_data:
                    return {'risks': []}
                
                company_name, business_type, industry_sector, risk_level, is_critical, has_data_access, has_system_access = vendor_data
                
                # Create basic risks based on vendor characteristics
                basic_risks = []
                
                # Risk 1: Data Access Risk
                if has_data_access:
                    basic_risks.append({
                        'title': 'Data Access Security Risk',
                        'description': f'{company_name} has access to sensitive data. Potential risk of data breach or unauthorized access.',
                        'likelihood': 3,
                        'impact': 4,
                        'exposure_rating': 3,
                        'score': 75,
                        'priority': 'High',
                        'ai_explanation': 'Generated based on data access permissions',
                        'suggested_mitigations': [
                            'Implement data access controls',
                            'Regular access reviews',
                            'Data encryption requirements'
                        ]
                    })
                
                # Risk 2: System Access Risk
                if has_system_access:
                    basic_risks.append({
                        'title': 'System Integration Risk',
                        'description': f'{company_name} has system access. Risk of system compromise or unauthorized system changes.',
                        'likelihood': 2,
                        'impact': 4,
                        'exposure_rating': 3,
                        'score': 60,
                        'priority': 'Medium',
                        'ai_explanation': 'Generated based on system access permissions',
                        'suggested_mitigations': [
                            'Implement system access controls',
                            'Regular system access audits',
                            'Multi-factor authentication'
                        ]
                    })
                
                # Risk 3: Critical Vendor Risk
                if is_critical:
                    basic_risks.append({
                        'title': 'Critical Vendor Dependency Risk',
                        'description': f'{company_name} is marked as a critical vendor. Business continuity risk if vendor fails.',
                        'likelihood': 2,
                        'impact': 5,
                        'exposure_rating': 4,
                        'score': 80,
                        'priority': 'High',
                        'ai_explanation': 'Generated based on critical vendor status',
                        'suggested_mitigations': [
                            'Develop backup vendor strategy',
                            'Regular vendor performance monitoring',
                            'Business continuity planning'
                        ]
                    })
                
                # Risk 4: Industry Sector Risk
                if industry_sector:
                    basic_risks.append({
                        'title': f'{industry_sector} Industry Risk',
                        'description': f'{company_name} operates in {industry_sector} sector. Industry-specific risks may apply.',
                        'likelihood': 3,
                        'impact': 3,
                        'exposure_rating': 3,
                        'score': 60,
                        'priority': 'Medium',
                        'ai_explanation': 'Generated based on industry sector',
                        'suggested_mitigations': [
                            'Industry-specific compliance requirements',
                            'Sector risk assessment',
                            'Industry best practices implementation'
                        ]
                    })
                
                # Risk 5: General Vendor Risk
                basic_risks.append({
                    'title': 'General Vendor Management Risk',
                    'description': f'General risks associated with vendor {company_name} including performance, compliance, and relationship risks.',
                    'likelihood': 3,
                    'impact': 3,
                    'exposure_rating': 3,
                    'score': 60,
                    'priority': 'Medium',
                    'ai_explanation': 'Generated as general vendor risk',
                    'suggested_mitigations': [
                        'Regular vendor performance reviews',
                        'Compliance monitoring',
                        'Contract management'
                    ]
                })
                
                logger.info(f"Created {len(basic_risks)} basic risks for vendor {vendor_id}")
                return {'risks': basic_risks}
                
        except Exception as e:
            logger.error(f"Error creating basic vendor risks for vendor {vendor_id}: {str(e)}")
            return {'risks': []}
    
    def generate_vendor_risks_async(self, approval_id: str) -> Dict:
        """
        Generate vendor risks from questionnaire approval (asynchronous using threading)
        
        This method returns immediately and runs the risk generation in a background thread.
        Perfect for providing non-blocking user experience without requiring Redis/Celery.
        
        Args:
            approval_id: The approval request ID that was just approved
            
        Returns:
            Immediate response dictionary with thread status
        """
        try:
            logger.info(f"🔵 [RISK GENERATION] Starting async vendor risk generation for approval: {approval_id}")
            print(f"🔵 [RISK GENERATION] Starting async vendor risk generation for approval: {approval_id}")
            
            from .threading_service import trigger_vendor_risk_generation_async
            logger.info(f"✅ [RISK GENERATION] Successfully imported trigger_vendor_risk_generation_async")
            print(f"✅ [RISK GENERATION] Successfully imported trigger_vendor_risk_generation_async")
            
            result = trigger_vendor_risk_generation_async(approval_id)
            logger.info(f"✅ [RISK GENERATION] Started async vendor risk generation for approval {approval_id}: {result}")
            print(f"✅ [RISK GENERATION] Started async vendor risk generation for approval {approval_id}: {result}")
            return result
            
        except ImportError as import_error:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"❌ [RISK GENERATION] Import error starting async vendor risk generation for approval {approval_id}: {str(import_error)}")
            logger.error(f"❌ [RISK GENERATION] Import traceback: {error_trace}")
            print(f"❌ [RISK GENERATION] Import error starting async vendor risk generation for approval {approval_id}: {str(import_error)}")
            print(f"❌ [RISK GENERATION] Import traceback: {error_trace}")
            return {
                'status': 'error',
                'approval_id': approval_id,
                'error': f"Import error: {str(import_error)}",
                'message': 'Failed to import threading service'
            }
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"❌ [RISK GENERATION] Error starting async vendor risk generation for approval {approval_id}: {str(e)}")
            logger.error(f"❌ [RISK GENERATION] Error traceback: {error_trace}")
            print(f"❌ [RISK GENERATION] Error starting async vendor risk generation for approval {approval_id}: {str(e)}")
            print(f"❌ [RISK GENERATION] Error traceback: {error_trace}")
            return {
                'status': 'error',
                'approval_id': approval_id,
                'error': str(e),
                'message': 'Failed to start background risk generation'
            }
    
    def get_vendor_risk_generation_status(self, approval_id: str) -> Optional[Dict]:
        """
        Get status of vendor risk generation thread
        
        Args:
            approval_id: The approval request ID
            
        Returns:
            Dict with status or None if not found
        """
        try:
            from .threading_service import get_risk_generation_status
            return get_risk_generation_status(approval_id)
        except Exception as e:
            logger.error(f"Error getting risk generation status for {approval_id}: {str(e)}")
            return None
