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
            # Check if Ollama service is available
            print(f"=== OLLAMA DEBUG: Checking Ollama availability - is_available: {self.is_available}, url: {self.ollama_url}, model: {self.model_name} ===")
            if not self.is_available or not self.ollama_url or not self.model_name:
                error_msg = f"Llama service is not available for comprehensive {entity} analysis. Please check Ollama configuration and ensure the service is running."
                print(f"=== OLLAMA DEBUG: {error_msg} ===")
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Build comprehensive prompt
            prompt = self._build_comprehensive_contract_prompt(plan_info, extracted_details, evaluation_data)
            
            # Call Ollama API
            print(f"=== OLLAMA DEBUG: Calling Ollama API with prompt length: {len(prompt)} ===")
            response = self._call_ollama(prompt)
            
            # Parse text and create risks directly
            risks = self._parse_text_and_create_risks_comprehensive(response, entity, plan_info)
            
            print(f"=== OLLAMA DEBUG: Successfully created {len(risks)} risks from comprehensive {entity} plan data ===")
            logger.info(f"Successfully created {len(risks)} risks from comprehensive {entity} plan data")
            return risks
            
        except Exception as e:
            error_msg = f"Failed to create risks from comprehensive {entity} data: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _build_comprehensive_contract_prompt(self, plan_info: dict, extracted_details: dict = None, evaluation_data: dict = None) -> str:
        """Build optimized contract prompt for faster processing"""
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        
        # Extract key contract information
        contract_title = plan_info.get('contract_title', 'Unknown Contract')
        contract_type = plan_info.get('contract_type', 'Unknown')
        contract_value = plan_info.get('contract_value', 0)
        vendor_name = plan_info.get('vendor_name', 'Unknown Vendor')
        start_date = plan_info.get('start_date', '')
        end_date = plan_info.get('end_date', '')
        
        prompt = f"""Analyze this contract and identify 3-4 key risks. Today is {today}.

CONTRACT: {contract_title}
TYPE: {contract_type}
VALUE: ${contract_value:,}
VENDOR: {vendor_name}
DURATION: {start_date} to {end_date}

Identify risks in these areas:
1. Financial exposure and payment terms
2. Vendor dependency and service delivery
3. Contract duration and flexibility
4. Compliance and regulatory requirements

Format each risk as:

RISK 1:
TITLE: [Specific risk title based on comprehensive analysis]
DESCRIPTION: Comprehensive analysis reveals specific control gaps across plan information, extracted details, and evaluation data. Owner: [Relevant owner]. Evidence needed: [Specific evidence]. Review due: 2025-12-17.
LIKELIHOOD: [1-5]
IMPACT: [1-5]
EXPOSURE: [1-5]
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
            
            # Determine the correct table name based on entity
            table_name = 'vendor_contracts' if entity == 'contract_module' else 'comprehensive_plan_data'
            
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
                data=table_name,
                row=str(plan_info.get('contract_id') or plan_info.get('plan_id') or plan_info.get('id') or 'unknown')
            )
            
            return risk
            
        except Exception as e:
            logger.error(f"Error creating comprehensive risk from block: {e}")
            return None
