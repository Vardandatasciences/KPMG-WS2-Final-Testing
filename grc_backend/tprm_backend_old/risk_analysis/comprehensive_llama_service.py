"""
Comprehensive LLaMA Service extension for handling complete BCP/DRP plan data
"""
import json
import logging
import re
from typing import List
from .models import Risk
from .llama_service import LlamaService

logger = logging.getLogger(__name__)


class ComprehensiveLlamaService(LlamaService):
    """Extended LLaMA service for comprehensive plan analysis"""
    
    def create_risks_from_comprehensive_data(self, entity: str, plan_info: dict, extracted_details: dict = None, evaluation_data: dict = None) -> List[Risk]:
        """
        Generate risks from comprehensive plan data including plan info, extracted details, and evaluation data
        
        Args:
            entity: Module name (BCP_DRP)
            plan_info: Plan basic information
            extracted_details: OCR extracted details (BCP or DRP specific)
            evaluation_data: Evaluation scores and comments (optional)
            
        Returns:
            List of created Risk instances
        """
        try:
            if not self.ollama_url or not self.model_name:
                error_msg = "Llama service is not available. Please check Ollama configuration and ensure the service is running."
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Build comprehensive prompt
            prompt = self._build_comprehensive_bcp_drp_prompt(plan_info, extracted_details, evaluation_data)
            
            # Call Ollama API
            response = self._call_ollama(prompt)
            
            # Parse text and create risks directly
            risks = self._parse_text_and_create_risks_comprehensive(response, entity, plan_info)
            
            logger.info(f"Successfully created {len(risks)} risks from comprehensive {entity} plan data")
            return risks
            
        except Exception as e:
            error_msg = f"Failed to create risks from comprehensive {entity} data: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _build_comprehensive_bcp_drp_prompt(self, plan_info: dict, extracted_details: dict = None, evaluation_data: dict = None) -> str:
        """Build comprehensive BCP/DRP prompt using all available data"""
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        
        plan_type = plan_info.get('plan_type', 'BCP/DRP')
        plan_name = plan_info.get('plan_name', 'Unknown Plan')
        
        prompt = f"""Analyze this comprehensive BCP/DRP plan data and identify 4-6 specific risks. Today is {today}.

COMPREHENSIVE {plan_type} PLAN ANALYSIS for "{plan_name}"

=== PLAN INFORMATION ===
{json.dumps(plan_info, indent=2)}

=== EXTRACTED DETAILS ===
{json.dumps(extracted_details, indent=2) if extracted_details else "No extracted details available"}

=== EVALUATION DATA ===
{json.dumps(evaluation_data, indent=2) if evaluation_data else "No evaluation data available"}

Apply comprehensive BCP/DRP analysis considering:

**Plan-Level Risks:**
- Document recency and version control
- Plan criticality alignment with actual risk
- Status progression and approval workflow
- OCR extraction completeness and accuracy

**Extracted Details Risks:**
- Missing critical components (RTO/RPO, procedures, contacts)
- Inadequate scenario coverage
- Geographic correlation and dependencies
- Testing and maintenance schedules
- Communication and escalation procedures

**Evaluation-Level Risks (if available):**
- Low evaluation scores indicating gaps
- Evaluator comments highlighting concerns
- Recommendation alignment with plan quality
- Timeline delays in evaluation process

**Cross-Component Risks:**
- Inconsistencies between plan info and extracted details
- Evaluation scores not reflecting plan content quality
- Missing integration between components

Format each risk EXACTLY like this:

RISK 1:
TITLE: [Specific risk title based on comprehensive analysis]
DESCRIPTION: Comprehensive analysis reveals specific control gaps across plan information, extracted details, and evaluation data. Owner: [Relevant owner]. Evidence needed: [Specific evidence]. Review due: 2025-12-17.
LIKELIHOOD: [1-5]
IMPACT: [1-5]
EXPLANATION: Cross-analysis of plan data shows [specific findings from multiple data sources].
MITIGATIONS:
- [Specific actionable mitigation addressing plan-level issues]
- [Specific actionable mitigation addressing extracted details gaps]
- [Specific actionable mitigation addressing evaluation concerns]

Generate comprehensive, actionable risks based on the complete plan context:"""
        
        return prompt
    
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
