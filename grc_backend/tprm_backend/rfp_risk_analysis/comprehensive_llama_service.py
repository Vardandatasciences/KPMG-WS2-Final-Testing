"""
Comprehensive LLaMA Service extension for RFP module.
BCP/DRP comprehensive risk generation is handled by risk_analysis module.
"""
import logging
import re
from typing import List
from .models import Risk
from .llama_service import LlamaService

logger = logging.getLogger(__name__)


class ComprehensiveLlamaService(LlamaService):
    """Extended LLaMA service for comprehensive plan analysis (RFP only). BCP/DRP uses risk_analysis."""

    def create_risks_from_comprehensive_data(self, entity: str, plan_info: dict, extracted_details: dict = None, evaluation_data: dict = None) -> List[Risk]:
        """
        Generate risks from comprehensive plan data. BCP/DRP is handled by risk_analysis.

        Args:
            entity: Module name (RFP only; use risk_analysis for BCP_DRP / bcp_drp_module)
            plan_info: Plan basic information
            extracted_details: OCR extracted details (optional)
            evaluation_data: Evaluation scores and comments (optional)

        Returns:
            List of created Risk instances
        """
        if entity in ('BCP_DRP', 'bcp_drp_module'):
            raise ValueError(
                "BCP/DRP comprehensive risk generation is handled by the risk_analysis module. "
                "Use risk_analysis.services.RiskAnalysisService.analyze_comprehensive_plan_data "
                "or risk_analysis.tasks.generate_comprehensive_risks_task."
            )
        # RFP comprehensive not implemented here; raise if ever needed
        raise NotImplementedError(
            "Comprehensive risk generation in rfp_risk_analysis is only supported for BCP/DRP, "
            "which is handled by risk_analysis. Use risk_analysis for BCP/DRP comprehensive analysis."
        )

    def _parse_text_and_create_risks_comprehensive(self, llama_response: str, entity: str, plan_info: dict) -> List[Risk]:
        """Parse Llama text response and create Risk objects from comprehensive analysis"""
        try:
            logger.info(f"Parsing comprehensive Llama response for {entity} (first 500 chars): {llama_response[:500]}")
            
            risks_created = []
            
            # Split by "RISK X:" pattern
            risk_blocks = re.split(r'RISK \d+:', llama_response)[1:]  # Skip first empty part
            
            for i, block in enumerate(risk_blocks, 1):
                try:
                    risk = self._create_risk_from_block_comprehensive(block, entity, plan_info, i)
                    if risk:
                        risks_created.append(risk)
                        logger.info(f"Created comprehensive risk {i}: {risk.title}")
                except Exception as e:
                    logger.error(f"Error creating comprehensive risk {i}: {e}")
                    continue
            
            return risks_created
            
        except Exception as e:
            logger.error(f"Error parsing comprehensive Llama response: {e}")
            raise Exception(f"Failed to parse comprehensive Llama response: {e}")
    
    def _create_risk_from_block_comprehensive(self, block: str, entity: str, plan_info: dict, risk_number: int) -> Risk:
        """Create a Risk object from a comprehensive analysis text block"""
        try:
            # Extract information using simple text parsing
            title = self._extract_field(block, 'TITLE:', '\n') or f"Comprehensive Risk {risk_number} - {entity}"
            description = self._extract_field(block, 'DESCRIPTION:', '\n') or "Risk identified from comprehensive plan analysis"
            likelihood_str = self._extract_field(block, 'LIKELIHOOD:', '\n') or "3"
            impact_str = self._extract_field(block, 'IMPACT:', '\n') or "4"
            exposure_str = self._extract_field(block, 'EXPOSURE:', '\n') or "3"
            explanation = self._extract_field(block, 'EXPLANATION:', '\n') or "AI-generated comprehensive risk analysis"
            
            # Convert to integers
            try:
                likelihood = int(likelihood_str.strip())
                likelihood = max(1, min(5, likelihood))  # Ensure 1-5 range
            except:
                likelihood = 3
            
            try:
                impact = int(impact_str.strip())
                impact = max(1, min(5, impact))  # Ensure 1-5 range
            except:
                impact = 4
            
            try:
                exposure = int(exposure_str.strip())
                exposure = max(1, min(5, exposure))  # Ensure 1-5 range
            except:
                exposure = 3
            
            # Extract mitigations
            mitigations = self._extract_mitigations(block)
            
            # Calculate score and priority
            # New formula: Likelihood × Impact × Exposure × 1.33
            score = int(likelihood * impact * exposure * 1.33)
            score = min(100, score)  # Ensure it stays within 0-100 range
            
            if score >= 80:
                priority = 'Critical'
            elif score >= 60:
                priority = 'High'
            elif score >= 40:
                priority = 'Medium'
            else:
                priority = 'Low'
            
            # Create comprehensive description with source info
            plan_name = plan_info.get('plan_name', 'Unknown Plan')
            plan_type = plan_info.get('plan_type', 'BCP/DRP')
            source_info = f"[{entity} - {plan_type} Plan: {plan_name}]"
            
            # Create the Risk object directly with entity-data-row tracking
            risk = Risk.objects.create(
                title=title[:255],  # Ensure it fits in the field
                description=f"{source_info} {description}",
                likelihood=likelihood,
                impact=impact,
                exposure_rating=exposure,
                score=score,
                priority=priority,
                risk_type='Current',
                ai_explanation=f"Comprehensive Analysis: {explanation}",
                suggested_mitigations=mitigations,
                entity=entity,
                data='comprehensive_plan_data',
                row=str(plan_info.get('plan_id') or plan_info.get('id') or 'unknown')
            )
            
            return risk
            
        except Exception as e:
            logger.error(f"Error creating comprehensive risk from block: {e}")
            return None
