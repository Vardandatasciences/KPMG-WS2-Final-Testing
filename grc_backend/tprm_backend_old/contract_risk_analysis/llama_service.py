import requests
import json
import logging
import re
from django.conf import settings
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
            self.model_name = getattr(settings, 'LLAMA_MODEL_NAME', 'llama3.2:1b')
            
            # Test connection to Ollama
            self._test_connection()
            self.is_available = True
            print(f"=== OLLAMA DEBUG: LlamaService initialized successfully with model: {self.model_name} ===")
            logger.info(f"LlamaService initialized successfully with model: {self.model_name}")
            
        except Exception as e:
            print(f"=== OLLAMA DEBUG: LlamaService initialization failed: {e} ===")
            logger.warning(f"LlamaService initialization failed: {e}")
            self.ollama_url = None
            self.model_name = None
            self.is_available = False
    
    def _test_connection(self):
        """Test connection to Ollama service"""
        try:
            # No timeout to avoid hanging during risk analysis
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                if self.model_name not in model_names:
                    logger.warning(f"Model {self.model_name} not found in available models: {model_names}")
            else:
                raise Exception(f"Ollama API returned status code: {response.status_code}")
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection refused to Ollama at {self.ollama_url}: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"Timeout connecting to Ollama at {self.ollama_url}: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed to Ollama at {self.ollama_url}: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to connect to Ollama at {self.ollama_url}: {str(e)}")
    
    def _create_fallback_risks(self, entity: str, table_name: str, row_data: dict) -> List[Risk]:
        """Create fallback risks when Ollama is not available"""
        logger.info(f"Creating fallback risks for {entity} {table_name} (Ollama unavailable)")
        
        fallback_risks = []
        
        # Generate basic risks based on entity type
        if entity == 'contract_module':
            fallback_risks = self._create_contract_fallback_risks(table_name, row_data)
        
        return fallback_risks
    
    def _create_contract_fallback_risks(self, table_name: str, row_data: dict) -> List[Risk]:
        """Create fallback risks for contract data"""
        risks = []
        
        if table_name == 'vendor_contracts':
            # Contract-specific fallback risks
            contract_value = row_data.get('contract_value', 0)
            contract_type = row_data.get('contract_type', 'Unknown')
            
            # High-value contract risk
            if contract_value and float(contract_value) > 100000:
                risk = Risk(
                    title="High-Value Contract Risk",
                    description=f"Contract value of ${contract_value:,.2f} represents significant financial exposure",
                    likelihood=3,
                    impact=4,
                    exposure_rating=3,
                    ai_explanation="High-value contracts require enhanced monitoring and risk management due to significant financial exposure.",
                    suggested_mitigations=[
                        "Implement enhanced contract monitoring",
                        "Establish regular vendor performance reviews",
                        "Consider contract insurance or guarantees"
                    ],
                    entity='contract_module',
                    data='vendor_contracts',
                    row=str(row_data.get('contract_id', 'unknown'))
                )
                risks.append(risk)
            
            # Contract type specific risk
            if contract_type in ['SERVICE_AGREEMENT', 'LICENSE']:
                risk = Risk(
                    title="Service Delivery Risk",
                    description=f"{contract_type} contracts may have service delivery dependencies",
                    likelihood=2,
                    impact=3,
                    exposure_rating=2,
                    ai_explanation="Service agreements and licenses often involve ongoing service delivery with potential for disruption.",
                    suggested_mitigations=[
                        "Define clear service level agreements",
                        "Establish vendor performance metrics",
                        "Create contingency plans for service disruption"
                    ],
                    entity='contract_module',
                    data='vendor_contracts',
                    row=str(row_data.get('contract_id', 'unknown'))
                )
                risks.append(risk)
        
        elif table_name == 'contract_terms':
            # Terms-specific fallback risks
            term_category = row_data.get('term_category', 'Unknown')
            
            if term_category in ['Payment', 'Financial']:
                risk = Risk(
                    title="Payment Terms Risk",
                    description="Payment-related terms may have financial implications",
                    likelihood=2,
                    impact=3,
                    exposure_rating=2,
                    ai_explanation="Payment terms can impact cash flow and financial planning.",
                    suggested_mitigations=[
                        "Review payment terms for clarity",
                        "Establish payment monitoring processes",
                        "Consider payment security measures"
                    ],
                    entity='contract_module',
                    data='contract_terms',
                    row=str(row_data.get('term_id', 'unknown'))
                )
                risks.append(risk)
        
        elif table_name == 'contract_clauses':
            # Clauses-specific fallback risks
            clause_type = row_data.get('clause_type', 'Unknown')
            
            if clause_type in ['termination', 'liability']:
                risk = Risk(
                    title="Legal Clause Risk",
                    description=f"{clause_type.title()} clauses may have legal implications",
                    likelihood=2,
                    impact=4,
                    exposure_rating=3,
                    ai_explanation="Termination and liability clauses can significantly impact contract outcomes and legal exposure.",
                    suggested_mitigations=[
                        "Review clause language with legal team",
                        "Ensure clause compliance with regulations",
                        "Document clause interpretation and application"
                    ],
                    entity='contract_module',
                    data='contract_clauses',
                    row=str(row_data.get('clause_id', 'unknown'))
                )
                risks.append(risk)
        
        return risks
    
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
    
    def create_risks_from_entity_data_row(self, entity: str, table_name: str, row_data: dict) -> List[Risk]:
        """
        Generate risks from specific entity, table, and row data
        
        Args:
            entity: Module name (Vendor, RFP, Contract, SLA, BCP_DRP)
            table_name: Database table name
            row_data: Specific row data from the table
            
        Returns:
            List of created Risk instances
        """
        try:
            # Check if Ollama service is available
            if not self.is_available or not self.ollama_url or not self.model_name:
                logger.warning("Llama service is not available. Using fallback risk generation.")
                return self._create_fallback_risks(entity, table_name, row_data)
            
            # Build prompt for specific entity-data-row
            prompt = self._build_entity_row_prompt(entity, table_name, row_data)
            
            # Call Ollama API
            response = self._call_ollama(prompt)
            
            # Parse text and create risks directly
            risks = self._parse_text_and_create_risks_simple(response, entity, table_name, row_data)
            
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
                    "temperature": 0.2,  # Lower temperature for faster, more consistent responses
                    "top_p": 0.8,       # Reduced diversity for speed
                    "max_tokens": 1500,  # Reduced token limit for faster processing
                    "num_predict": 1500
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload
                # No timeout to allow comprehensive risk analysis
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API returned status code: {response.status_code}")
            
            result = response.json()
            return result.get('response', '')
            
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"Connection refused to Ollama at {self.ollama_url}: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"Timeout calling Ollama at {self.ollama_url}: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed to Ollama at {self.ollama_url}: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to call Ollama API: {str(e)}")
    
    def _build_simple_prompt(self, module_data) -> str:
        """Build simple prompt for risk analysis (legacy method - use entity-data-row approach)"""
        data_payload = module_data.data_payload
        today = date.today().strftime('%Y-%m-%d')
        
        # Default to BCP/DRP prompt since this is legacy code
        return self._build_bcp_drp_prompt(data_payload, today)
    
    def _build_bcp_drp_prompt(self, data_payload: dict, today: str) -> str:
        """Build BCP/DRP specific prompt"""
        prompt = f"""Analyze this BCP/DRP plan and identify 3-5 specific risks. Today is {today}.

Apply BCP/DRP heuristics:
- Test recency: >90 days = High likelihood, 60-90 days = Medium likelihood
- Missing critical scenarios = Additional risk
- Same geography/utility for sites = Correlation risk
- <3 contacts = Single point of failure
- Aggressive RTO/RPO without validation = Backup risk

BCP/DRP Plan Data:
{json.dumps(data_payload, indent=2)}

Format each risk EXACTLY like this:

RISK 1:
TITLE: Insufficient Disaster Recovery Testing
DESCRIPTION: The last DR test was conducted over 90 days ago, increasing the risk of failure during an actual disaster. Control gaps include missing quarterly testing schedule and no automated procedures. Owner: IT Operations Manager. Evidence needed: Review test logs and validate procedures. Review due: 2025-12-17.
LIKELIHOOD: 4
IMPACT: 4
EXPOSURE: 4
EXPLANATION: BCP/DRP heuristic applied - test recency >90 days adds +2 likelihood. Missing scenario coverage increases risk.
MITIGATIONS:
- Establish quarterly disaster recovery testing schedule
- Implement automated testing procedures where feasible
- Document all test procedures and results comprehensively
- Create escalation procedures for failed tests

RISK 2:
TITLE: [Next risk title]
DESCRIPTION: [Next risk description with control gaps, owner, evidence, review date]
LIKELIHOOD: [1-5]
IMPACT: [1-5]
EXPOSURE: [1-5]
EXPLANATION: [Specific BCP/DRP analysis]
MITIGATIONS:
- [Specific actionable mitigation 1]
- [Specific actionable mitigation 2]
- [Specific actionable mitigation 3]

Generate specific, actionable risks based on the actual plan data:"""
        
        return prompt
    
    def _build_entity_row_prompt(self, entity: str, table_name: str, row_data: dict) -> str:
        """Build prompt for entity-row specific risk analysis"""
        from datetime import date
        today = date.today().strftime('%Y-%m-%d')
        
        # Get entity display name
        entity_display_names = {
            'Vendor': 'Vendor Management',
            'RFP': 'Request for Proposal', 
            'Contract': 'Contract Management',
            'SLA': 'Service Legal Agreement',
            'BCP_DRP': 'Business Continuity and Disaster Recovery'
        }
        
        entity_display = entity_display_names.get(entity, entity)
        
        if entity == 'BCP_DRP':
            return self._build_bcp_drp_row_prompt(table_name, row_data, today)
        else:
            return self._build_default_entity_row_prompt(entity_display, table_name, row_data, today)
    
    def _build_bcp_drp_row_prompt(self, table_name: str, row_data: dict, today: str) -> str:
        """Build BCP/DRP specific prompt for row data"""
        if 'plans' in table_name.lower():
            return self._build_bcp_drp_plan_prompt(row_data, today)
        elif 'evaluations' in table_name.lower():
            return self._build_bcp_drp_evaluation_prompt(row_data, today)
        else:
            # Default BCP/DRP prompt for other tables
            return self._build_bcp_drp_generic_prompt(table_name, row_data, today)
    
    def _build_bcp_drp_plan_prompt(self, row_data: dict, today: str) -> str:
        """Build specific prompt for BCP/DRP plans"""
        prompt = f"""Analyze this BCP/DRP Plan record and identify 3-5 specific risks. Today is {today}.

Apply BCP/DRP Plan heuristics:
- Document recency: Plans older than 12 months = High risk
- Missing critical scenarios: Natural disasters, cyber attacks, pandemic = Additional risk
- Geographic redundancy: Same location for primary/backup = Correlation risk
- Contact redundancy: <3 emergency contacts = Single point of failure
- RTO/RPO validation: Aggressive targets without testing = Backup risk
- Version control: Multiple versions without clear current = Confusion risk

BCP/DRP Plan Record Data:
{json.dumps(row_data, indent=2)}

Focus on these plan-specific risk areas:
1. Plan currency and maintenance
2. Scenario coverage gaps
3. Recovery target feasibility
4. Geographic and infrastructure dependencies
5. Contact and communication adequacy

Format each risk EXACTLY like this:

RISK 1:
TITLE: [Specific plan-related risk title]
DESCRIPTION: The BCP/DRP plan analysis reveals specific control gaps. Owner: Plan Owner/Business Unit. Evidence needed: Review plan documentation and test results. Review due: 2025-12-17.
LIKELIHOOD: [1-5]
IMPACT: [1-5]
EXPOSURE: [1-5]
EXPLANATION: Plan analysis shows [specific findings from the plan data such as outdated procedures, missing scenarios, unrealistic RTOs].
MITIGATIONS:
- [Plan-specific mitigation like "Update plan documentation"]
- [Testing mitigation like "Conduct tabletop exercise"]
- [Infrastructure mitigation like "Validate recovery procedures"]

Generate specific, actionable risks based on the actual plan data:"""
        
        return prompt
    
    def _build_bcp_drp_evaluation_prompt(self, row_data: dict, today: str) -> str:
        """Build specific prompt for BCP/DRP evaluations"""
        prompt = f"""Analyze this BCP/DRP Evaluation record and identify 3-5 specific risks. Today is {today}.

Apply BCP/DRP Evaluation heuristics:
- Low scores (<70): High risk areas requiring attention
- Missing evaluations: Overdue or skipped evaluations = Process risk
- Inconsistent scoring: Large gaps between categories = Review quality risk
- Delayed recommendations: Overdue actions = Implementation risk
- Evaluator expertise: Unqualified evaluators = Assessment quality risk

BCP/DRP Evaluation Record Data:
{json.dumps(row_data, indent=2)}

Focus on these evaluation-specific risk areas:
1. Evaluation completeness and timeliness
2. Score adequacy and consistency
3. Recommendation implementation gaps
4. Evaluator competency and independence
5. Follow-up and remediation tracking

Format each risk EXACTLY like this:

RISK 1:
TITLE: [Specific evaluation-related risk title]
DESCRIPTION: The BCP/DRP evaluation analysis reveals specific assessment gaps. Owner: Evaluation Manager/Risk Officer. Evidence needed: Review evaluation criteria and scoring rationale. Review due: 2025-12-17.
LIKELIHOOD: [1-5]
IMPACT: [1-5]
EXPOSURE: [1-5]
EXPLANATION: Evaluation analysis shows [specific findings from the evaluation data such as low scores, missing assessments, delayed recommendations].
MITIGATIONS:
- [Evaluation-specific mitigation like "Re-evaluate low-scoring areas"]
- [Process mitigation like "Implement evaluation tracking system"]
- [Quality mitigation like "Provide evaluator training"]

Generate specific, actionable risks based on the actual evaluation data:"""
        
        return prompt
    
    def _build_bcp_drp_generic_prompt(self, table_name: str, row_data: dict, today: str) -> str:
        """Build generic BCP/DRP prompt for other table types"""
        prompt = f"""Analyze this BCP/DRP {table_name} record and identify 3-5 specific risks. Today is {today}.

Apply general BCP/DRP heuristics:
- Data completeness: Missing critical fields = Information risk
- Process compliance: Non-standard procedures = Compliance risk
- Timeline adherence: Overdue items = Operational risk
- Resource adequacy: Insufficient resources = Capacity risk

{table_name.upper()} Record Data:
{json.dumps(row_data, indent=2)}

Format each risk EXACTLY like this:

RISK 1:
TITLE: [Specific risk title based on the record]
DESCRIPTION: The analysis of {table_name} record reveals specific control gaps. Owner: [Relevant owner]. Evidence needed: [Specific evidence]. Review due: 2025-12-17.
LIKELIHOOD: [1-5]
IMPACT: [1-5]
EXPOSURE: [1-5]
EXPLANATION: Analysis of {table_name} record shows [specific findings from the data].
MITIGATIONS:
- [Specific actionable mitigation 1]
- [Specific actionable mitigation 2]
- [Specific actionable mitigation 3]

Generate specific, actionable risks based on the actual record data:"""
        
        return prompt
    
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
EXPOSURE: [1-5]
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
EXPOSURE: [1-5]
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
            
            # Create the Risk object directly (legacy method - module_id removed)
            risk = Risk.objects.create(
                title=title[:255],  # Ensure it fits in the field
                description=description,
                likelihood=likelihood,
                impact=impact,
                exposure_rating=exposure,
                score=score,
                priority=priority,
                risk_type='Current',
                ai_explanation=explanation,
                suggested_mitigations=mitigations,
                entity='legacy_module',
                data='legacy_data',
                row='legacy'
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