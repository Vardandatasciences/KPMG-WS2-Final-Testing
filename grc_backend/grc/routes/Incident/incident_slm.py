import json
import re
import random
import traceback
import os
from django.conf import settings
import time

# Phase 2 / Phase 3 utilities (reuse same helpers as risk_ai_doc)
from ...utils.document_preprocessor import calculate_document_hash
from ...utils.rag_system import (
    add_document_to_rag,
    retrieve_relevant_context,
    build_rag_prompt,
    is_rag_available,
    get_rag_stats,
)
from ...utils.model_router import (
    route_model,
    track_system_load,
    get_current_system_load,
)
from ...utils.request_queue import (
    process_with_queue,
    get_queue_status,
)

# Reuse AI provider configuration and JSON-call helpers from risk_ai_doc
from ..Risk.risk_ai_doc import (
    AI_PROVIDER,
    call_ollama_json,
    call_openai_json,
    _select_ollama_model_by_complexity,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL_DEFAULT,
    OLLAMA_MODEL_FAST,
    OLLAMA_MODEL_COMPLEX,
    OPENAI_API_KEY,
    OPENAI_API_URL,
    OPENAI_MODEL,
)

print("\n🤖 Incident SLM AI Provider Configuration:")
print(f"   Selected Provider: {AI_PROVIDER.upper()}")
if AI_PROVIDER == 'openai':
    print(f"   OpenAI model: {OPENAI_MODEL}")
elif AI_PROVIDER == 'ollama':
    print(f"   Ollama URL: {OLLAMA_BASE_URL}")
    print(f"   Default model: {OLLAMA_MODEL_DEFAULT}")
    print(f"   Fast model: {OLLAMA_MODEL_FAST}")
    print(f"   Complex model: {OLLAMA_MODEL_COMPLEX}")


class OpenAIIntegration:
    """AI integration class for incident analysis (OpenAI or Ollama) with Phase 2/3 helpers."""
    
    def __init__(self, api_key=None):
        """Initialize AI client based on provider (using shared helpers)."""
        self.provider = AI_PROVIDER
        self.is_available = False

        if self.provider == 'ollama':
            if not OLLAMA_BASE_URL:
                print("⚠️ Ollama URL not configured properly")
                print("   Please set OLLAMA_BASE_URL in your .env file")
                self.is_available = False
            else:
                self.is_available = True
                print("✅ Ollama integration initialized for incident analysis")
                print(f"   Using base URL: {OLLAMA_BASE_URL}")
            return

        # OpenAI path
        if api_key is None:
            api_key = OPENAI_API_KEY
        
        if not api_key or api_key == 'your-openai-api-key-here' or str(api_key).startswith('YOUR_OPE'):
            print("⚠️ OpenAI API key not configured properly")
            print("   Please set OPENAI_API_KEY in your .env file")
            self.is_available = False
        else:
            # We use shared call_openai_json wrapper instead of direct SDK client
            self.is_available = True
            print("✅ OpenAI integration initialized successfully for incident analysis")
            print(f"   Using model: {OPENAI_MODEL}")
    
    def generate_response(self, prompt, model=None, max_tokens=2000, temperature=0.3, document_hash: str | None = None):
        """Send request to AI provider and get response (JSON string), using Phase 2/3 utilities."""
        if not self.is_available:
            print("AI provider is not available")
            return None

        # Ollama branch
        if self.provider == 'ollama':
            try:
                selected_model = model or route_model(
                    task_type="incident_comprehensive",
                    text_length=len(prompt),
                    accuracy_required="high",
                    system_load=get_current_system_load(),
                    provider="ollama",
                )
                out_obj = call_ollama_json(
                    prompt,
                    model=selected_model,
                    document_hash=document_hash,
                )
                return json.dumps(out_obj)
            except Exception as e:
                print(f"❌ Ollama JSON call error (incident_slm): {type(e).__name__}: {e}")
                traceback.print_exc()
                return None

        # OpenAI branch
        try:
            selected_model = model or route_model(
                task_type="incident_comprehensive",
                text_length=len(prompt),
                accuracy_required="high",
                system_load=get_current_system_load(),
                provider="openai",
            )

            out_obj = call_openai_json(
                prompt,
                document_hash=document_hash,
            )
            return json.dumps(out_obj)
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            print(f"❌ AI JSON call error (incident_slm): {error_type}: {error_message}")
            traceback.print_exc()
            return None

def analyze_incident_comprehensive(incident_title, incident_description):
    """
    Comprehensive incident analysis for GRC banking system with extensive banking-specific analysis.
    
    Args:
        incident_title (str): Title of the incident
        incident_description (str): Detailed description of the incident
    
    Returns:
        dict: JSON object containing comprehensive incident analysis
    """
    try:
        # Initialize AI integration
        print("🔄 Using AI for incident analysis (with Phase 2+3 optimizations)")
        openai_client = OpenAIIntegration()
        
        if not openai_client.is_available:
            print("⚠️ AI provider not available, falling back to comprehensive fallback analysis")
            return generate_comprehensive_fallback_analysis(incident_title, incident_description)

        # Phase 2: calculate document hash for caching / RAG
        document_hash = calculate_document_hash(f"{incident_title}\n{incident_description}")
        print(f"📝 Incident (comprehensive) document hash: {document_hash[:16]}...")

        # Phase 3: optional RAG context from previous incidents / analyses
        rag_context = None
        if is_rag_available():
            try:
                query_text = f"Incident: {incident_title}\n\n{incident_description}"
                rag_context = retrieve_relevant_context(query_text, n_results=3)
                if rag_context:
                    print(f"   📚 Phase 3 RAG (incident_slm): Retrieved {len(rag_context)} relevant chunks")
            except Exception as e:
                print(f"   ⚠️  RAG retrieval failed in incident_slm: {e}")

        # Create a comprehensive prompt for banking GRC incident analysis
        base_prompt = f"""Analyze the following security incident for a banking GRC system and provide a comprehensive JSON response.

**INCIDENT DETAILS:**
- Title: {incident_title}
- Description: {incident_description}

**REQUIRED JSON STRUCTURE:**
{{
  "riskPriority": "<P0/P1/P2/P3>",
  "criticality": "<Critical/High/Medium/Low>",
  "costOfIncident": <single_numeric_value>,
  "costJustification": "<detailed explanation of cost calculation>",
  "possibleDamage": "<detailed banking-specific impact analysis>",
  "systemsInvolved": ["<system1>", "<system2>", "..."],
  "initialImpactAssessment": "<technical and business impact details>",
  "mitigationSteps": ["<step1>", "<step2>", "..."],
  "comments": "<expert analysis with regulatory context>",
  "violatedPolicies": ["<policy1>", "<policy2>", "..."],
  "procedureControlFailures": ["<control1>", "<control2>", "..."],
  "lessonsLearned": ["<lesson1>", "<lesson2>", "..."]
}}

**CLASSIFICATION GUIDELINES:**

**Risk Priority:**
- P0: Critical banking operations down, >10K customers affected, >$1M regulatory penalty
- P1: Significant impact, 1K-10K customers affected, $100K-$1M penalty
- P2: Limited impact, <1K customers affected
- P3: Minor impact, internal only

**Criticality:**
- Critical: Core banking systems, payment rails, transaction processing
- High: Trading platforms, risk management, customer-facing apps
- Medium: Internal applications, reporting systems
- Low: Development/test environments

**Banking Context to Consider:**
- Regulatory frameworks: FFIEC, OCC, FRB, FDIC, CFPB
- Compliance requirements: GLBA, BSA/AML, SOX, PCI DSS, NYDFS Cybersecurity, Basel III
- Banking systems: Core Banking, Payment Processing, Digital Banking, Trading Systems, Risk Management, Compliance Systems, ATM Networks, Wire Transfer Systems

**Analysis Requirements:**
1. **costOfIncident**: Provide ONLY a single numeric value (no currency symbols, no ranges) representing total estimated cost in USD. Examples: 50000, 250000, 1500000
2. **costJustification**: Provide detailed breakdown explaining: regulatory fines estimate, operational costs (downtime, recovery), remediation costs (technical fixes, security improvements), customer compensation, reputational damage costs, legal fees, and how you arrived at the total number
3. Possible damage should cover: operational disruption, customer impact, regulatory penalties, reputational harm
4. Systems involved should list specific banking infrastructure components
5. Mitigation steps should include: immediate containment, customer communication, regulatory notification, forensics, recovery
6. Violated policies should reference specific banking security/compliance policies
7. Control failures should identify which security controls failed
8. Lessons learned should provide actionable recommendations

**CRITICAL:** The costOfIncident MUST be a pure numeric value (integer) without any currency symbols, commas, or text. Example: 250000 NOT "$250,000" or "250000 USD"
        
Provide ONLY the JSON response, no additional text."""

        # Phase 3: weave RAG context into the prompt if available
        if rag_context:
            prompt = build_rag_prompt(
                user_query=base_prompt,
                retrieved_context=rag_context,
                base_prompt=None,
            )
        else:
            prompt = base_prompt

        # Process the incident using AI (with routing + caching)
        print(f"📊 Analyzing incident: {incident_title}")

        def _do_analysis():
            start_time = time.time()
            response_local = openai_client.generate_response(
                prompt,
                model=None,  # let integration + router pick
                max_tokens=2000,
                temperature=0.3,
                document_hash=document_hash,
            )
            processing_time = time.time() - start_time
            track_system_load(processing_time, len(f"{incident_title}\n{incident_description}"))
            print(f"⏱️ Incident SLM processing_time={processing_time:.2f}s")
            return response_local

        # Use queue for very large descriptions
        if len(incident_description) > 5000:
            request_id = f"incident_slm_{hash(incident_title + incident_description)}"
            print(f"📋 Large incident description detected, using Phase 3 queuing (request_id={request_id})...")
            response = process_with_queue(request_id, _do_analysis)
        else:
            response = _do_analysis()
        
        # Check if response is None (API error)
        if response is None:
            print("❌ OpenAI request failed, falling back to comprehensive fallback analysis")
            return generate_comprehensive_fallback_analysis(incident_title, incident_description)
       
        # Parse the JSON from the response
        try:
            print(f"✅ Received response from OpenAI")
            
            # OpenAI with json_object format should return clean JSON, but let's still clean it
            json_text = response.strip()
            
            # Remove markdown code blocks if present (shouldn't be with json_object format, but just in case)
            if json_text.startswith("```json"):
                json_text = json_text[7:]
            if json_text.startswith("```"):
                json_text = json_text[3:]
            if json_text.endswith("```"):
                json_text = json_text[:-3]
            json_text = json_text.strip()
            
            # Parse JSON
            incident_analysis = json.loads(json_text)
            
            # Validate all required fields are present
            required_fields = [
                'riskPriority', 'criticality', 'costOfIncident', 'costJustification', 'possibleDamage', 
                             'systemsInvolved', 'initialImpactAssessment', 'mitigationSteps', 
                'comments', 'violatedPolicies', 'procedureControlFailures', 'lessonsLearned'
            ]
            
            missing_fields = [field for field in required_fields if field not in incident_analysis]
            
            if missing_fields:
                print(f"⚠️ Missing required fields in AI response: {missing_fields}")
                print("Falling back to comprehensive fallback analysis")
                return generate_comprehensive_fallback_analysis(incident_title, incident_description)
            
            # Ensure list fields are actually lists
            list_fields = ['systemsInvolved', 'mitigationSteps', 'violatedPolicies', 
                          'procedureControlFailures', 'lessonsLearned']
            for field in list_fields:
                if not isinstance(incident_analysis.get(field), list):
                    # Convert to list if it's a string
                    if isinstance(incident_analysis.get(field), str):
                        incident_analysis[field] = [incident_analysis[field]]
                    else:
                        print(f"⚠️ Field {field} is not a list, falling back")
                        return generate_comprehensive_fallback_analysis(incident_title, incident_description)
            
            print(f"✅ Successfully parsed comprehensive banking GRC incident analysis")

            # Phase 3: add incident + analysis to RAG for future context
            if is_rag_available():
                try:
                    add_document_to_rag(
                        document_text=f"Incident Title: {incident_title}\n\nDescription: {incident_description}\n\nAnalysis: {json.dumps(incident_analysis)}",
                        document_id=f"incident_slm_{document_hash[:16]}",
                        metadata={
                            "type": "incident_analysis",
                            "source": "incident_slm",
                            "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        },
                    )
                    print("✅ Phase 3 RAG (incident_slm): Incident analysis added to knowledge base")
                except Exception as e:
                    print(f"⚠️  Phase 3 RAG (incident_slm): Failed to add document: {e}")

            return incident_analysis
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Response text: {response[:500]}...")  # Print first 500 chars for debugging
            return generate_comprehensive_fallback_analysis(incident_title, incident_description)
        except Exception as e:
            print(f"❌ Error processing response: {e}")
            traceback.print_exc()
            return generate_comprehensive_fallback_analysis(incident_title, incident_description)

    except Exception as e:
        print(f"❌ Error with OpenAI processing: {e}")
        traceback.print_exc()
        return generate_comprehensive_fallback_analysis(incident_title, incident_description)

def generate_comprehensive_fallback_analysis(incident_title, incident_description):
    """Generate a comprehensive fallback analysis when the AI model is unavailable."""
    # Extract some keywords from the incident for basic categorization
    description_lower = (incident_title + " " + incident_description).lower()
    
    # Default values
    risk_priority = "P1"
    criticality = "Medium"
    cost_estimate = 150000
    cost_justification = "Estimated based on typical incident response costs including system recovery, investigation, and remediation efforts."
    systems = ["Core Banking System", "Network Infrastructure"]
    
    # Basic categorization based on keywords and assign appropriate values
    if any(word in description_lower for word in ["breach", "leak", "exposed", "data", "sensitive", "customer"]):
        risk_priority = "P0"
        criticality = "Critical"
        cost_estimate = 2500000
        cost_justification = "Data breach incident cost breakdown: Regulatory fines ($1,000,000 - GDPR/PCI DSS violations), Forensic investigation and remediation ($500,000), Customer notification and credit monitoring ($300,000), Legal fees and settlements ($400,000), Reputational damage and customer loss ($300,000). Total estimated impact: $2,500,000"
        systems = ["Core Banking System", "Customer Database", "Online Banking Platform", "Data Warehouse"]
        possible_damage = "Massive customer data exposure, regulatory penalties up to $50M, severe reputational damage, potential class-action lawsuits, loss of customer trust, and business continuity threats."
        violated_policies = ["Data Protection Policy", "Customer Privacy Policy", "Information Security Policy", "Incident Response Policy"]
        control_failures = ["Data encryption controls", "Access control mechanisms", "Data loss prevention systems", "Network segmentation controls"]
        
    elif any(word in description_lower for word in ["malware", "virus", "ransomware", "trojan", "attack"]):
        risk_priority = "P0"
        criticality = "Critical"
        cost_estimate = 800000
        cost_justification = "Malware/Ransomware incident breakdown: System recovery and restoration ($250,000), Business downtime and lost revenue ($200,000), Incident response and forensics ($150,000), Security infrastructure upgrades ($100,000), Ransom payment consideration ($50,000), Staff overtime and emergency response ($50,000). Total: $800,000"
        systems = ["Core Banking System", "ATM Network", "Payment Processing System", "Email System"]
        possible_damage = "System disruption, potential data encryption, business operations halt, customer service interruption, and recovery costs."
        violated_policies = ["Malware Protection Policy", "System Security Policy", "Business Continuity Policy"]
        control_failures = ["Antivirus protection", "Email filtering systems", "Network intrusion detection", "Endpoint protection controls"]
        
    elif any(word in description_lower for word in ["phish", "social engineering", "fraud", "impersonation"]):
        risk_priority = "P1"
        criticality = "High"
        cost_estimate = 350000
        cost_justification = "Phishing/Social engineering costs: Direct financial fraud losses ($100,000), Account recovery and customer reimbursement ($80,000), Enhanced security training programs ($50,000), Additional authentication controls ($70,000), Investigation and legal costs ($50,000). Total: $350,000"
        systems = ["Email System", "Online Banking Platform", "Employee Workstations", "Authentication System"]
        possible_damage = "Credential theft, unauthorized access to customer accounts, potential financial fraud, and employee security awareness gaps."
        violated_policies = ["Email Security Policy", "Authentication Policy", "Employee Training Policy", "Fraud Prevention Policy"]
        control_failures = ["Email security controls", "Multi-factor authentication", "User awareness training", "Fraud detection systems"]
        
    elif any(word in description_lower for word in ["unauthorized", "access", "privilege", "credential", "insider"]):
        risk_priority = "P1"
        criticality = "High"
        cost_estimate = 450000
        cost_justification = "Unauthorized access incident costs: Forensic investigation ($100,000), Data integrity verification ($80,000), Access control system overhaul ($120,000), Legal and regulatory notifications ($70,000), Potential regulatory fines ($50,000), Internal investigation and HR costs ($30,000). Total: $450,000"
        systems = ["Core Banking System", "Privileged Access Management", "Active Directory", "Database Systems"]
        possible_damage = "Unauthorized access to sensitive data, privilege escalation, potential data theft, and insider threat materialization."
        violated_policies = ["Access Control Policy", "Privileged Access Policy", "Identity Management Policy", "Segregation of Duties Policy"]
        control_failures = ["Access control systems", "Privilege management controls", "User access reviews", "Segregation of duties controls"]
        
    elif any(word in description_lower for word in ["compliance", "regulatory", "audit", "violation"]):
        risk_priority = "P1"
        criticality = "High"
        cost_estimate = 1200000
        cost_justification = "Regulatory compliance violation costs: Direct regulatory fines ($500,000), Compliance audit and remediation ($250,000), Enhanced monitoring and reporting systems ($200,000), Legal and consulting fees ($150,000), Process improvements and training ($100,000). Total: $1,200,000"
        systems = ["Compliance Management System", "Audit Trail System", "Reporting System", "Document Management"]
        possible_damage = "Regulatory fines, enforcement actions, audit findings, reputational damage, and increased regulatory scrutiny."
        violated_policies = ["Regulatory Compliance Policy", "Audit Policy", "Documentation Policy", "Reporting Policy"]
        control_failures = ["Compliance monitoring controls", "Audit trail mechanisms", "Regulatory reporting controls", "Documentation controls"]
        
    else:
        # Default case
        possible_damage = "Potential operational disruption, security compromise, and moderate business impact requiring immediate attention."
        violated_policies = ["Information Security Policy", "Incident Response Policy", "Risk Management Policy"]
        control_failures = ["Security monitoring controls", "Incident detection systems", "Risk assessment procedures"]
    
    return {
        "riskPriority": risk_priority,
        "criticality": criticality,
        "costOfIncident": cost_estimate,
        "costJustification": cost_justification,
        "possibleDamage": possible_damage,
        "systemsInvolved": systems,
        "initialImpactAssessment": f"Incident '{incident_title}' has been identified with potential impact on critical banking operations. Immediate containment and investigation required to determine full scope and prevent escalation.",
        "mitigationSteps": [
            "Step 1: Activate incident response team and establish command center",
            "Step 2: Isolate affected systems to prevent further compromise or spread",
            "Step 3: Preserve evidence and maintain chain of custody for forensic analysis",
            "Step 4: Assess immediate business impact and implement business continuity measures",
            "Step 5: Notify key stakeholders including senior management and legal team",
            "Step 6: Conduct preliminary investigation to determine root cause and scope",
            "Step 7: Implement temporary controls and workarounds to restore operations",
            "Step 8: Engage external experts if specialized skills are required",
            "Step 9: Prepare regulatory notifications if required by compliance obligations",
            "Step 10: Document all actions taken and maintain incident timeline",
            "Step 11: Conduct post-incident review and implement lessons learned",
            "Step 12: Update security controls and procedures to prevent recurrence"
        ],
        "comments": f"This incident requires immediate attention due to its potential impact on banking operations. The analysis is based on the incident title '{incident_title}' and available description. Further investigation may reveal additional complexities requiring escalated response measures.",
        "violatedPolicies": violated_policies,
        "procedureControlFailures": control_failures,
        "lessonsLearned": [
            "Importance of rapid incident detection and response capabilities",
            "Need for regular security awareness training and testing",
            "Critical role of backup and recovery procedures in business continuity",
            "Value of comprehensive incident documentation for future reference",
            "Necessity of regular security control testing and validation",
            "Importance of clear communication channels during incident response",
            "Need for regular review and update of incident response procedures",
            "Critical importance of stakeholder notification and regulatory compliance"
        ]
    }