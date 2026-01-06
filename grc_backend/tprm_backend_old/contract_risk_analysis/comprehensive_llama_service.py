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
                print(f"=== OLLAMA DEBUG: Ollama not available, using fallback risks for comprehensive {entity} analysis ===")
                logger.warning(f"Ollama not available, using fallback risks for comprehensive {entity} analysis")
                return self._create_comprehensive_fallback_risks(entity, plan_info, extracted_details, evaluation_data)
            
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
            
            # Use fallback if Ollama fails
            print(f"=== OLLAMA DEBUG: Ollama failed, using fallback risks for comprehensive {entity} analysis ===")
            logger.warning(f"Ollama failed, using fallback risks for comprehensive {entity} analysis")
            return self._create_comprehensive_fallback_risks(entity, plan_info, extracted_details, evaluation_data)
    
    def _create_comprehensive_fallback_risks(self, entity: str, plan_info: dict, extracted_details: dict = None, evaluation_data: dict = None) -> List[Risk]:
        """Create fallback risks for comprehensive contract data when Ollama is not available"""
        print(f"=== OLLAMA DEBUG: Creating comprehensive fallback risks for {entity} (Ollama unavailable) ===")
        logger.info(f"Creating comprehensive fallback risks for {entity} (Ollama unavailable)")
        
        risks = []
        
        if entity == 'contract_module':
            # Contract-specific comprehensive risks
            contract_info = plan_info
            
            # AI-Generated Style Risk Analysis (Enhanced Fallback)
            contract_title = contract_info.get('contract_title', 'Unknown Contract')
            contract_type = contract_info.get('contract_type', 'Unknown')
            contract_value = contract_info.get('contract_value', 0)
            vendor_name = contract_info.get('vendor_name', 'Unknown Vendor')
            start_date = contract_info.get('start_date', '')
            end_date = contract_info.get('end_date', '')
            
            # 1. Financial Risk Analysis
            if contract_value and float(contract_value) > 100000:
                risk = Risk(
                    title="High-Value Contract Financial Exposure",
                    description=f"Contract '{contract_title}' with {vendor_name} represents significant financial exposure of ${contract_value:,.2f}, creating substantial risk to organizational budget and cash flow management",
                    likelihood=3,
                    impact=4,
                    exposure_rating=4,
                    ai_explanation="High-value contracts create concentrated financial risk exposure. The large contract value means any vendor performance issues, delays, or contract breaches could have significant financial impact on the organization's budget and operations.",
                    suggested_mitigations=[
                        "Implement phased payment structures tied to milestone delivery",
                        "Establish vendor financial stability assessments",
                        "Create contract performance bonds or guarantees",
                        "Set up automated financial monitoring and alerts",
                        "Develop contingency budgets for potential cost overruns",
                        "Implement regular vendor financial health checks"
                    ],
                    entity='contract_module',
                    data='vendor_contracts',
                    row=str(contract_info.get('contract_id', 'unknown'))
                )
                risks.append(risk)
            
            # 2. Contract Type and Service Delivery Risk Analysis
            if contract_type in ['SERVICE_AGREEMENT', 'LICENSE']:
                risk = Risk(
                    title="Ongoing Service Delivery Dependency Risk",
                    description=f"Contract '{contract_title}' is a {contract_type} with {vendor_name}, creating operational dependency on continuous service delivery. Any service interruption could disrupt critical business operations",
                    likelihood=4,
                    impact=4,
                    exposure_rating=4,
                    ai_explanation="Service agreements and licenses create operational dependencies where business continuity relies on vendor performance. Service disruptions, vendor capacity issues, or quality degradation can directly impact organizational operations and customer service delivery.",
                    suggested_mitigations=[
                        "Define comprehensive service level agreements (SLAs) with clear performance metrics",
                        "Establish vendor performance monitoring and reporting systems",
                        "Create business continuity plans for service disruption scenarios",
                        "Implement regular service quality assessments and vendor reviews",
                        "Develop backup vendor relationships for critical services",
                        "Set up automated monitoring for service availability and performance"
                    ],
                    entity='contract_module',
                    data='vendor_contracts',
                    row=str(contract_info.get('contract_id', 'unknown'))
                )
                risks.append(risk)
            
            # 3. Contract Duration and Timeline Risk Analysis
            if start_date and end_date:
                try:
                    from datetime import datetime
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                    duration_days = (end_dt - start_dt).days
                    
                    if duration_days > 365:  # Long-term contract
                        risk = Risk(
                            title="Long-Term Contract Commitment Risk",
                            description=f"Contract '{contract_title}' spans {duration_days} days ({duration_days//365} years), creating long-term operational and financial commitments that may become misaligned with changing business needs",
                            likelihood=3,
                            impact=3,
                            exposure_rating=3,
                            ai_explanation="Long-term contracts create commitment risks where business needs, technology, or market conditions may change significantly over the contract duration, potentially making the contract terms suboptimal or creating exit challenges.",
                            suggested_mitigations=[
                                "Include contract review and renegotiation clauses at regular intervals",
                                "Establish flexibility mechanisms for scope and pricing adjustments",
                                "Create exit strategies and termination clauses with reasonable penalties",
                                "Implement regular contract performance and value assessments",
                                "Develop contingency plans for contract modification or early termination"
                            ],
                            entity='contract_module',
                            data='vendor_contracts',
                            row=str(contract_info.get('contract_id', 'unknown'))
                        )
                        risks.append(risk)
                except ValueError:
                    pass  # Skip if date parsing fails
            
            # 4. Vendor Concentration Risk Analysis
            risk = Risk(
                title="Vendor Dependency and Concentration Risk",
                description=f"Contract with {vendor_name} creates vendor dependency risk. Over-reliance on a single vendor can create supply chain vulnerabilities and limit negotiation leverage",
                likelihood=3,
                impact=3,
                exposure_rating=3,
                ai_explanation="Vendor concentration risk occurs when an organization becomes overly dependent on a single vendor or a small number of vendors. This creates vulnerabilities in supply chain management, reduces competitive pricing leverage, and increases risk of service disruption if the vendor experiences issues.",
                suggested_mitigations=[
                    "Develop multi-vendor strategies for critical services and products",
                    "Establish vendor diversification policies and limits",
                    "Create vendor performance benchmarking against market alternatives",
                    "Implement regular vendor market analysis and competitive assessments",
                    "Develop contingency plans for vendor switching or replacement",
                    "Establish vendor relationship management programs"
                ],
                entity='contract_module',
                data='comprehensive_contract_data',
                row=str(contract_info.get('contract_id', 'unknown'))
            )
            risks.append(risk)
            
            # 5. Compliance and Regulatory Risk Analysis
            compliance_framework = contract_info.get('compliance_framework', '')
            if compliance_framework:
                risk = Risk(
                    title="Compliance and Regulatory Framework Risk",
                    description=f"Contract '{contract_title}' involves {compliance_framework} compliance requirements, creating regulatory risk exposure that requires ongoing monitoring and adherence",
                    likelihood=2,
                    impact=4,
                    exposure_rating=3,
                    ai_explanation="Contracts involving specific compliance frameworks create regulatory risk where non-compliance can result in penalties, legal action, or business restrictions. Ongoing monitoring and adherence to compliance requirements is essential.",
                    suggested_mitigations=[
                        f"Establish {compliance_framework} compliance monitoring and reporting systems",
                        "Implement regular compliance audits and assessments",
                        "Create compliance training programs for relevant staff",
                        "Develop compliance breach response and remediation procedures",
                        "Establish relationships with compliance experts and legal counsel",
                        "Set up automated compliance monitoring and alerting systems"
                    ],
                    entity='contract_module',
                    data='vendor_contracts',
                    row=str(contract_info.get('contract_id', 'unknown'))
                )
                risks.append(risk)
            
            # Analyze terms and clauses if available
            if extracted_details:
                terms = extracted_details.get('terms', [])
                clauses = extracted_details.get('clauses', [])
                
                # Payment terms risk
                payment_terms = [t for t in terms if t.get('term_category') in ['Payment', 'Financial']]
                if payment_terms:
                    risk = Risk(
                        title="Payment Terms Complexity Risk",
                        description=f"Contract has {len(payment_terms)} payment-related terms that may impact cash flow",
                        likelihood=2,
                        impact=3,
                        exposure_rating=2,
                        ai_explanation="Complex payment terms can impact cash flow and financial planning.",
                        suggested_mitigations=[
                            "Review payment terms for clarity",
                            "Establish payment monitoring processes",
                            "Consider payment security measures",
                            "Create payment schedule tracking"
                        ],
                        entity='contract_module',
                        data='vendor_contracts',
                        row=str(contract_info.get('contract_id', 'unknown'))
                    )
                    risks.append(risk)
                
                # Legal clauses risk
                legal_clauses = [c for c in clauses if c.get('clause_type') in ['termination', 'liability']]
                if legal_clauses:
                    risk = Risk(
                        title="Legal Clause Risk",
                        description=f"Contract has {len(legal_clauses)} legal clauses that may have significant implications",
                        likelihood=2,
                        impact=4,
                        exposure_rating=3,
                        ai_explanation="Termination and liability clauses can significantly impact contract outcomes and legal exposure.",
                        suggested_mitigations=[
                            "Review clause language with legal team",
                            "Ensure clause compliance with regulations",
                            "Document clause interpretation and application",
                            "Establish clause monitoring and review processes"
                        ],
                        entity='contract_module',
                        data='vendor_contracts',
                        row=str(contract_info.get('contract_id', 'unknown'))
                    )
                    risks.append(risk)
        
        print(f"=== OLLAMA DEBUG: Created {len(risks)} comprehensive fallback risks for {entity} ===")
        return risks
    
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
