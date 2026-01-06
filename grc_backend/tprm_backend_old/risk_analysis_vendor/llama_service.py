import requests
import json
import logging
import re
from django.conf import settings
from django.utils import timezone
from datetime import date
from typing import List
from .models import Risk

logger = logging.getLogger(__name__)


class LlamaService:
    """Simple service for Llama 2 integration - Direct text to database approach"""
    
    def __init__(self):
        try:
            # Get Ollama configuration from settings
            self.ollama_url = getattr(settings, 'OLLAMA_URL', 'http://localhost:11434')
            self.model_name = getattr(settings, 'LLAMA_MODEL_NAME', 'llama2:latest')
            
            # Test connection to Ollama
            self._test_connection()
            logger.info(f"LlamaService initialized successfully with model: {self.model_name}")
            
        except Exception as e:
            logger.warning(f"LlamaService initialization failed: {e}")
            self.ollama_url = None
            self.model_name = None
    
    def _test_connection(self):
        """Test connection to Ollama service"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                if self.model_name not in model_names:
                    logger.warning(f"Model {self.model_name} not found in available models: {model_names}")
            else:
                raise Exception(f"Ollama API returned status code: {response.status_code}")
        except Exception as e:
            raise Exception(f"Failed to connect to Ollama at {self.ollama_url}: {str(e)}")
    
    def create_risks_directly(self, module_data) -> List[Risk]:
        """
        Simple approach: Generate risks directly from Llama text output
        
        Args:
            module_data: Legacy module data object (deprecated - use entity-data-row approach)
            
        Returns:
            List of created Risk instances
        """
        try:
            if not self.ollama_url or not self.model_name:
                error_msg = "Llama service is not available. Please check Ollama configuration and ensure the service is running."
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Generate the simple prompt
            prompt = self._build_simple_prompt(module_data)
            
            # Call Ollama API
            response = self._call_ollama(prompt)
            
            # Parse text and create risks directly
            risks = self._parse_text_and_create_risks(response, module_data)
            
            logger.info(f"Successfully created {len(risks)} risks directly for module {module_data.module_id.name}")
            return risks
            
        except Exception as e:
            error_msg = f"Failed to create risks using Llama: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def create_risks_from_entity_data_row(self, entity: str, table_name: str, row_data: dict, module_data: dict = None) -> List[Risk]:
        """
        Generate risks from specific entity, table, and row data
        
        Args:
            entity: Module name (Vendor, RFP, Contract, SLA)
            table_name: Database table name
            row_data: Specific row data from the table
            
        Returns:
            List of created Risk instances
        """
        try:
            if not self.ollama_url or not self.model_name:
                error_msg = "Llama service is not available. Please check Ollama configuration and ensure the service is running."
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # Build prompt for specific entity-data-row
            prompt = self._build_entity_row_prompt(entity, table_name, row_data)
            
            # Call Ollama API
            response = self._call_ollama(prompt)
            
            # Parse text and create risks directly
            if module_data is None:
                module_data = {
                    'entity': entity,
                    'data': table_name,
                    'row': '0'
                }
            risks = self._parse_text_and_create_risks(response, module_data)
            
            logger.info(f"Successfully created {len(risks)} risks for {entity} from {table_name}")
            return risks
            
        except Exception as e:
            error_msg = f"Failed to create risks for {entity} from {table_name}: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with the given prompt"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Balanced for good analysis
                    "top_p": 0.9,       # Good diversity
                    "max_tokens": 3000,  # Enough for detailed analysis
                    "num_predict": 3000
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=None
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API returned status code: {response.status_code}")
            
            result = response.json()
            return result.get('response', '')
            
        except Exception as e:
            raise Exception(f"Failed to call Ollama API: {str(e)}")
    
    def _build_simple_prompt(self, module_data) -> str:
        """Build simple prompt for risk analysis (legacy method - use entity-data-row approach)"""
        data_payload = module_data.data_payload
        today = date.today().strftime('%Y-%m-%d')
        
        # Use default prompt for legacy module data
        return self._build_default_prompt(module_data.module_id, data_payload, today)
    
    def _build_entity_row_prompt(self, entity: str, table_name: str, row_data: dict) -> str:
        """Build prompt for entity-row specific risk analysis"""
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        
        # Get entity display name
        entity_display_names = {
            'Vendor': 'Vendor Management',
            'RFP': 'Request for Proposal', 
            'Contract': 'Contract Management',
            'SLA': 'Service Legal Agreement'
        }
        
        entity_display = entity_display_names.get(entity, entity)
        
        return self._build_default_entity_row_prompt(entity_display, table_name, row_data, today)
    
    
    def _build_default_entity_row_prompt(self, entity_display: str, table_name: str, row_data: dict, today: str) -> str:
        """Build default prompt for other entity row data"""
        prompt = f"""Analyze this {entity_display} {table_name} record and identify 2-3 specific risks. Today is {today}.

{table_name.upper()} Record Data:
{json.dumps(row_data, indent=2)}

Format each risk EXACTLY like this:

RISK 1:
TITLE: [Specific risk title based on the record]
DESCRIPTION: [Detailed risk description with control gaps and specific findings from the record]
LIKELIHOOD: [1-5]
IMPACT: [1-5]
EXPLANATION: [Why this risk exists based on the record data]
MITIGATIONS:
- [Specific actionable mitigation 1]
- [Specific actionable mitigation 2]
- [Specific actionable mitigation 3]

Generate specific risks based on the actual record data provided:"""
        
        return prompt
    
    def _build_default_prompt(self, module, data_payload: dict, today: str) -> str:
        """Build default prompt for other modules"""
        prompt = f"""Analyze this {module.get_name_display()} data and identify 2-3 specific risks. Today is {today}.

Module Data:
{json.dumps(data_payload, indent=2)}

Format each risk EXACTLY like this:

RISK 1:
TITLE: [Specific risk title]
DESCRIPTION: [Detailed risk description]
LIKELIHOOD: [1-5]
IMPACT: [1-5]
EXPLANATION: [Why this risk exists based on the data]
MITIGATIONS:
- [Specific actionable mitigation 1]
- [Specific actionable mitigation 2]
- [Specific actionable mitigation 3]

Generate specific risks based on the actual data provided:"""
        
        return prompt
    
    def _parse_text_and_create_risks(self, llama_response: str, module_data) -> List[Risk]:
        """Parse Llama text response and create Risk objects directly"""
        try:
            logger.info(f"Parsing Llama response (first 500 chars): {llama_response[:500]}")
            
            risks_created = []
            
            # Split by "RISK X:" pattern
            risk_blocks = re.split(r'RISK \d+:', llama_response)[1:]  # Skip first empty part
            
            for i, block in enumerate(risk_blocks, 1):
                try:
                    risk = self._create_risk_from_block(block, module_data, i)
                    if risk:
                        risks_created.append(risk)
                        logger.info(f"Created risk {i}: {risk.title}")
                except Exception as e:
                    logger.error(f"Error creating risk {i}: {e}")
                    continue
            
            return risks_created
            
        except Exception as e:
            logger.error(f"Error parsing Llama response: {e}")
            raise Exception(f"Failed to parse Llama response: {e}")
    
    def _create_risk_from_block(self, block: str, module_data, risk_number: int) -> Risk:
        """Create a Risk object from a text block"""
        try:
            # Extract information using simple text parsing
            title = self._extract_field(block, 'TITLE:', '\n') or f"Risk {risk_number}"
            description = self._extract_field(block, 'DESCRIPTION:', '\n') or "Risk identified from analysis"
            likelihood_str = self._extract_field(block, 'LIKELIHOOD:', '\n') or "3"
            impact_str = self._extract_field(block, 'IMPACT:', '\n') or "4"
            exposure_str = self._extract_field(block, 'EXPOSURE:', '\n') or "3"
            explanation = self._extract_field(block, 'EXPLANATION:', '\n') or "AI-generated risk analysis"
            
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
            
            # Create the Risk object with proper metadata
            risk = Risk.objects.create(
                title=title[:255],  # Ensure it fits in the field
                description=description,
                likelihood=likelihood,
                impact=impact,
                exposure_rating=exposure,
                score=score,
                priority=priority,
                risk_type='Current',
                status='Open',  # Default status for new risks
                ai_explanation=explanation,
                suggested_mitigations=mitigations,
                entity=module_data.get('entity', 'vendor_management'),
                data=module_data.get('data', 'temp_vendor'),
                row=module_data.get('row', '0'),
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            
            return risk
            
        except Exception as e:
            logger.error(f"Error creating risk from block: {e}")
            return None
    
    def _extract_field(self, text: str, start_marker: str, end_marker: str) -> str:
        """Extract text between two markers"""
        start_pos = text.find(start_marker)
        if start_pos == -1:
            return ""
        
        start_pos += len(start_marker)
        end_pos = text.find(end_marker, start_pos)
        
        if end_pos == -1:
            # If no end marker found, take rest of text up to next field or end
            next_field_pos = float('inf')
            for field in ['TITLE:', 'DESCRIPTION:', 'LIKELIHOOD:', 'IMPACT:', 'EXPOSURE:', 'EXPLANATION:', 'MITIGATIONS:']:
                field_pos = text.find(field, start_pos)
                if field_pos != -1 and field_pos < next_field_pos:
                    next_field_pos = field_pos
            
            if next_field_pos != float('inf'):
                end_pos = next_field_pos
            else:
                end_pos = len(text)
        
        return text[start_pos:end_pos].strip()
    
    def _extract_mitigations(self, block: str) -> List[str]:
        """Extract mitigation bullet points"""
        mitigations = []
        
        # Find MITIGATIONS: section
        mitigations_pos = block.find('MITIGATIONS:')
        if mitigations_pos == -1:
            return ["Implement appropriate risk controls", "Monitor and review regularly", "Document procedures"]
        
        # Get text after MITIGATIONS:
        mitigations_text = block[mitigations_pos + len('MITIGATIONS:'):].strip()
        
        # Split by lines and find bullet points
        lines = mitigations_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('- '):
                mitigations.append(line[2:].strip())
            elif line.startswith('• '):
                mitigations.append(line[2:].strip())
            elif line.startswith('* '):
                mitigations.append(line[2:].strip())
            elif line and not line.startswith('RISK') and len(mitigations) == 0:
                # If no bullet points found, treat first non-empty line as mitigation
                mitigations.append(line)
        
        # Ensure we have at least some mitigations
        if not mitigations:
            mitigations = [
                "Implement appropriate risk controls",
                "Establish monitoring procedures", 
                "Review and update regularly"
            ]
        
        return mitigations[:5]  # Limit to 5 mitigations
    
    def _parse_text_and_create_risks_simple(self, llama_response: str, entity: str, table_name: str, row_data: dict) -> List[Risk]:
        """Parse Llama text response and create Risk objects directly without ModuleData dependency"""
        try:
            logger.info(f"Parsing Llama response for {entity} {table_name} (first 500 chars): {llama_response[:500]}")
            
            risks_created = []
            
            # Split by "RISK X:" pattern
            risk_blocks = re.split(r'RISK \d+:', llama_response)[1:]  # Skip first empty part
            
            for i, block in enumerate(risk_blocks, 1):
                try:
                    risk = self._create_risk_from_block_simple(block, entity, table_name, row_data, i)
                    if risk:
                        risks_created.append(risk)
                        logger.info(f"Created risk {i}: {risk.title}")
                except Exception as e:
                    logger.error(f"Error creating risk {i}: {e}")
                    continue
            
            return risks_created
            
        except Exception as e:
            logger.error(f"Error parsing Llama response: {e}")
            raise Exception(f"Failed to parse Llama response: {e}")
    
    def _create_risk_from_block_simple(self, block: str, entity: str, table_name: str, row_data: dict, risk_number: int) -> Risk:
        """Create a Risk object from a text block without ModuleData dependency"""
        try:
            # Extract information using simple text parsing
            title = self._extract_field(block, 'TITLE:', '\n') or f"Risk {risk_number} - {entity}"
            description = self._extract_field(block, 'DESCRIPTION:', '\n') or "Risk identified from analysis"
            likelihood_str = self._extract_field(block, 'LIKELIHOOD:', '\n') or "3"
            impact_str = self._extract_field(block, 'IMPACT:', '\n') or "4"
            exposure_str = self._extract_field(block, 'EXPOSURE:', '\n') or "3"
            explanation = self._extract_field(block, 'EXPLANATION:', '\n') or "AI-generated risk analysis"
            
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
            
            # Create the Risk object directly with entity-data-row tracking
            risk = Risk.objects.create(
                title=title[:255],  # Ensure it fits in the field
                description=f"[{entity} - {table_name}] {description}",  # Include source info in description
                likelihood=likelihood,
                impact=impact,
                exposure_rating=exposure,
                score=score,
                priority=priority,
                risk_type='Current',
                ai_explanation=f"Source: {entity} {table_name} | {explanation}",
                suggested_mitigations=mitigations,
                entity=entity,
                data=table_name,
                row=str(row_data.get('id') or row_data.get('plan_id') or row_data.get('evaluation_id') or 'unknown')
            )
            
            return risk
            
        except Exception as e:
            logger.error(f"Error creating risk from block: {e}")
            return None