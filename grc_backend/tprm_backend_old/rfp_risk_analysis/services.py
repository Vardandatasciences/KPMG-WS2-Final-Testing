import json
import logging
from django.conf import settings
from django.utils import timezone
from django.db import models
from typing import Dict, List, Tuple, Optional
from .models import Risk
from .llama_service import LlamaService
from .comprehensive_llama_service import ComprehensiveLlamaService
from .entity_service import EntityDataService

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
    from risk_analysis.services import RiskAnalysisService
    
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
    
    See INTEGRATION_GUIDE.md for complete examples and BCP/DRP integration patterns!
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
        from risk_analysis.services import RiskAnalysisService
        
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
    
    def analyze_comprehensive_plan_data(self, entity: str, comprehensive_data: Dict) -> Dict:
        """
        Analyze comprehensive plan data including plan info, extracted details, and evaluation data
        
        Args:
            entity: logical module name (e.g., bcp_drp_module)
            comprehensive_data: Complete plan data structure
            
        Returns:
            Standardized risk response dictionary with risks array
        """
        try:
            # Validate comprehensive data structure
            if not comprehensive_data or 'plan_info' not in comprehensive_data:
                raise ValueError("comprehensive_data must contain plan_info")
            
            plan_info = comprehensive_data.get('plan_info', {})
            extracted_details = comprehensive_data.get('extracted_details')
            evaluation_data = comprehensive_data.get('evaluation_data')
            
            # Generate risks using comprehensive LLaMA service
            from .comprehensive_llama_service import ComprehensiveLlamaService
            comprehensive_llama_service = ComprehensiveLlamaService()
            created_risks = comprehensive_llama_service.create_risks_from_comprehensive_data(
                entity=entity,
                plan_info=plan_info,
                extracted_details=extracted_details,
                evaluation_data=evaluation_data
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
            
            plan_id = plan_info.get('plan_id', 'unknown')
            logger.info(f"Generated {len(risks_response)} risks for comprehensive {entity} plan {plan_id}")
            
            return {
                "risks": risks_response
            }
            
        except Exception as e:
            logger.error(f"Error analyzing comprehensive plan data for {entity}: {str(e)}")
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