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

# Shared AI adapters for cross-module migration
from ...ai.adapters import (
    AI_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL_COMPLEX,
    OLLAMA_MODEL_DEFAULT,
    OLLAMA_MODEL_FAST,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    legacy_call_ollama_json as call_ollama_json,
    legacy_call_openai_json as call_openai_json,
)
from ...ai.service import get_ai_service
from ...ai.types import AIRequestOptions
from .risk_ai_doc import (
    _select_ollama_model_by_complexity,
    OPENAI_API_URL,
)
from ...debug_utils import debug_print

debug_print("\n🤖 Risk SLM AI Provider Configuration:")
debug_print(f"   Selected Provider: {AI_PROVIDER.upper()}")
if AI_PROVIDER == 'openai':
    debug_print(f"   OpenAI model: {OPENAI_MODEL}")
elif AI_PROVIDER == 'ollama':
    debug_print(f"   Ollama URL: {OLLAMA_BASE_URL}")
    debug_print(f"   Default model: {OLLAMA_MODEL_DEFAULT}")
    debug_print(f"   Fast model: {OLLAMA_MODEL_FAST}")
    debug_print(f"   Complex model: {OLLAMA_MODEL_COMPLEX}")


class OpenAIIntegration:
    """AI integration class for risk analysis (OpenAI or Ollama) with Phase 2/3 helpers."""
    
    def __init__(self, api_key=None):
        """Initialize AI client based on provider (using shared helpers)."""
        self.provider = AI_PROVIDER
        self.is_available = False

        if self.provider == 'ollama':
            if not OLLAMA_BASE_URL:
                debug_print("⚠️ Ollama URL not configured properly")
                debug_print("   Please set OLLAMA_BASE_URL in your .env file")
                self.is_available = False
            else:
                self.is_available = True
                debug_print("✅ Ollama integration initialized for risk analysis")
                debug_print(f"   Using base URL: {OLLAMA_BASE_URL}")
            return

        # OpenAI path
        if api_key is None:
            api_key = OPENAI_API_KEY
        
        if not api_key or api_key == 'your-openai-api-key-here' or str(api_key).startswith('YOUR_OPE'):
            debug_print("⚠️ OpenAI API key not configured properly")
            debug_print("   Please set OPENAI_API_KEY in your .env file")
            self.is_available = False
        else:
            # We use shared call_openai_json wrapper instead of direct SDK client
            self.is_available = True
            debug_print("✅ OpenAI integration initialized successfully for risk analysis")
            debug_print(f"   Using model: {OPENAI_MODEL}")
    
    def generate_response(self, prompt, model=None, max_tokens=2000, temperature=0.3, document_hash: str | None = None):
        """Send request to AI provider and get response (JSON string), using Phase 2/3 utilities."""
        if not self.is_available:
            debug_print("AI provider is not available")
            return None

        # Ollama branch
        if self.provider == 'ollama':
            try:
                selected_model = model or route_model(
                    task_type="incident_analysis",
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
                debug_print(f"❌ Ollama JSON call error: {type(e).__name__}: {e}")
                traceback.print_exc()
                return None

        # OpenAI branch
        try:
            selected_model = model or route_model(
                task_type="incident_analysis",
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
            debug_print(f"❌ AI JSON call error: {error_type}: {error_message}")
            traceback.print_exc()
            return None

def analyze_security_incident(incident_description):
    """
    Analyze security incidents for risk assessment with comprehensive analysis.
    Can be used for both incident analysis and pure risk analysis scenarios.
    """
    try:
        print(f"[ROUTE-SLM] analyze_security_incident: len={len(incident_description)}")
        debug_print("🔄 Using centralized AI service for risk analysis")
        ai_service = get_ai_service()

        # Phase 2: calculate document hash for caching / RAG
        document_hash = calculate_document_hash(incident_description)
        debug_print(f"📝 Document hash: {document_hash[:16]}...")

        # Phase 3: optional RAG context from previous analyses / documents
        rag_context = None
        if is_rag_available():
            try:
                rag_context = retrieve_relevant_context(incident_description, n_results=3)
                if rag_context:
                    debug_print(f"   📚 Phase 3 RAG (risk SLM): Retrieved {len(rag_context)} relevant chunks")
            except Exception as e:
                debug_print(f"   ⚠️  RAG retrieval failed in slm_service: {e}")
        rag_context_text = ""
        if rag_context:
            rag_context_text = json.dumps(rag_context, ensure_ascii=True)

        # Process the incident using AI (with routing + caching)
        debug_print(f"📊 Analyzing risk for description: {incident_description[:100]}...")

        def _do_analysis():
            start_time = time.time()
            response_local = ai_service.run_task(
                "risk.analyze_security_incident",
                payload={
                    "incident_description": incident_description,
                    "rag_context": rag_context_text,
                },
                options=AIRequestOptions(
                    task_name="risk.analyze_security_incident",
                    document_hash=document_hash,
                    use_cache=True,
                    metadata={
                        "rag_chunks_used": len(rag_context or []),
                    },
                ),
            )
            processing_time = time.time() - start_time
            track_system_load(processing_time, len(incident_description))
            debug_print(f"⏱️ Risk SLM processing_time={processing_time:.2f}s, text_len={len(incident_description)}")
            print(f"[ROUTE-SLM] risk.analyze_security_incident DONE: time={processing_time:.2f}s")
            return response_local

        # Simple queue usage for very large descriptions
        if len(incident_description) > 5000:
            request_id = f"risk_slm_{hash(incident_description)}"
            debug_print(f"📋 Large description detected, using Phase 3 queuing (request_id={request_id})...")
            response = process_with_queue(request_id, _do_analysis)
        else:
            response = _do_analysis()
        
        # Check if response is None (API error)
        if response is None:
            debug_print("❌ AI request failed, falling back to comprehensive fallback analysis")
            return generate_fallback_analysis(incident_description)

        if isinstance(response, dict):
            analysis = response
            debug_print(f"✅ Successfully parsed comprehensive banking GRC risk analysis")

            # Phase 3: add description + analysis to RAG for future context
            if is_rag_available():
                try:
                    add_document_to_rag(
                        document_text=f"Risk/Incident: {incident_description}\n\nAnalysis: {json.dumps(analysis)}",
                        document_id=f"risk_slm_{document_hash[:16]}",
                        metadata={
                            "type": "risk_analysis",
                            "source": "risk_slm_service",
                            "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        },
                    )
                    debug_print("✅ Phase 3 RAG (risk SLM): Analysis added to knowledge base")
                except Exception as e:
                    debug_print(f"⚠️  Phase 3 RAG (risk SLM): Failed to add document: {e}")

            return analysis

        debug_print("❌ Centralized AI task did not return JSON, falling back to generated analysis")
        return generate_fallback_analysis(incident_description)
            
    except Exception as e:
        debug_print(f"❌ Error with centralized AI processing: {e}")
        traceback.print_exc()
        # Fall back to a generated response if the model fails
        return generate_fallback_analysis(incident_description)


def analyze_risk_comprehensive(risk_title, risk_description):
    """
    Comprehensive risk analysis specifically designed for Create Risk AI functionality.
    Returns analysis tailored for risk register fields.
    """
    try:
        print(f"[ROUTE-SLM] analyze_risk_comprehensive: title={risk_title[:50]}...")
        debug_print("🔄 Using centralized AI service for comprehensive risk analysis")
        
        # Combine title and description for analysis
        combined_text = f"Risk Title: {risk_title}\n\nRisk Description: {risk_description}"
        
        # Use the same underlying analysis but with risk-focused context
        analysis = analyze_security_incident(combined_text)
        
        if analysis:
            # Map fields to risk-specific names and add risk-specific justifications
            risk_analysis = {
                'criticality': analysis.get('criticality', 'Medium'),
                'criticalityJustification': analysis.get('criticalityJustification', 
                    'Risk criticality assessed based on potential business impact, regulatory implications, and operational disruption. Follows enterprise risk management guidelines.'),
                
                'riskLikelihood': analysis.get('riskLikelihood', 5),
                'riskLikelihoodJustification': analysis.get('riskLikelihoodJustification',
                    'Likelihood assessment considering historical data, current controls, threat environment, and operational factors. Rating follows risk assessment methodology.'),
                
                'riskImpact': analysis.get('riskImpact', 5),
                'riskImpactJustification': analysis.get('riskImpactJustification',
                    'Impact evaluation covers financial, operational, reputational, and compliance consequences. Severity rating based on business criticality and regulatory requirements.'),
                
                'possibleDamage': analysis.get('possibleDamage', 'Potential operational disruption, financial impact, and regulatory exposure depending on risk materialization.'),
                'possibleDamageJustification': analysis.get('possibleDamageJustification',
                    'Damage assessment considers direct and indirect impacts including operational costs, revenue effects, compliance penalties, and reputation damage.'),
                
                'riskMitigation': analysis.get('riskMitigation', [
                    'Implement appropriate controls based on risk assessment',
                    'Regular monitoring and review of risk indicators',
                    'Develop contingency plans for risk materialization',
                    'Ensure adequate insurance coverage where applicable'
                ]),
                'riskMitigationJustification': analysis.get('riskMitigationJustification',
                    'Mitigation strategies selected based on cost-benefit analysis, control effectiveness, and alignment with risk appetite. Implementation prioritized by risk exposure.'),
                
                'category': analysis.get('category', 'Operational'),
                'categoryJustification': analysis.get('categoryJustification',
                    'Risk category determined by primary impact domain and business function affected. Classification aligns with enterprise risk taxonomy.'),
                
                'businessImpact': analysis.get('businessImpact', 'Moderate impact on business operations depending on risk scenario and existing controls.'),
                'businessImpactJustification': analysis.get('businessImpactJustification',
                    'Business impact assessment covering revenue effects, operational continuity, customer relationships, and strategic objectives. Based on business impact analysis methodology.')
            }
            
            debug_print(f"✅ Risk comprehensive analysis completed successfully")
            return risk_analysis
        else:
            debug_print(f"❌ Risk analysis failed, returning fallback")
            return generate_risk_fallback_analysis(risk_title, risk_description)
            
    except Exception as e:
        debug_print(f"❌ Error in comprehensive risk analysis: {e}")
        traceback.print_exc()
        return generate_risk_fallback_analysis(risk_title, risk_description)

def parse_ai_response(response):
    """
    Parse AI response with robust error handling for different formats.
    Works with both OpenAI-style and Ollama-backed responses (as long as the
    integration returns a JSON string matching the expected schema).

    Returns parsed JSON object or None if parsing fails.
    """
    try:
        debug_print(f"✅ Received response from AI provider")
        
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

        # ------------------------------------------------------------------
        # NORMALIZE FIELD NAMES / STRUCTURE FROM DIFFERENT AI PROVIDERS
        # ------------------------------------------------------------------
        # 1) Some models (like your current Ollama prompt) return a nested
        #    "Justifications": {"Likelihood": "...", "Impact": "..."} block
        #    instead of flat riskLikelihoodJustification / riskImpactJustification.
        justifications = incident_analysis.get("Justifications") or incident_analysis.get("justifications")
        if isinstance(justifications, dict):
            if "Likelihood" in justifications and "riskLikelihoodJustification" not in incident_analysis:
                incident_analysis["riskLikelihoodJustification"] = justifications["Likelihood"]
            if "Impact" in justifications and "riskImpactJustification" not in incident_analysis:
                incident_analysis["riskImpactJustification"] = justifications["Impact"]

        # 2) Be tolerant to minor key typos that the model can produce
        #    e.g. "riskIImpactJustification" → "riskImpactJustification"
        if "riskIImpactJustification" in incident_analysis and "riskImpactJustification" not in incident_analysis:
            incident_analysis["riskImpactJustification"] = incident_analysis["riskIImpactJustification"]
        
        # Validate all required fields are present.
        # If some are missing, fill them with sensible defaults instead of discarding
        # the whole AI response.
        required_fields = [
            'riskLikelihood',
            'riskImpact',
            'riskLikelihoodJustification',
            'riskImpactJustification',
            'criticality',
            'category',
            'riskMitigation',
        ]
        missing_fields = [field for field in required_fields if field not in incident_analysis]

        if missing_fields:
            debug_print(f"⚠️ Missing required fields in AI response: {missing_fields} – filling with defaults")

            # Default values mirror the logic used in generate_fallback_analysis
            if 'criticality' in missing_fields:
                incident_analysis['criticality'] = incident_analysis.get('criticality', 'Significant')

            if 'category' in missing_fields:
                incident_analysis['category'] = incident_analysis.get('category', 'IT Security')

            # If scores are missing, default both to 5 so downstream code always has values.
            if 'riskLikelihood' in missing_fields:
                incident_analysis['riskLikelihood'] = incident_analysis.get('riskLikelihood', 5)

            if 'riskImpact' in missing_fields:
                incident_analysis['riskImpact'] = incident_analysis.get('riskImpact', 5)

            if 'riskLikelihoodJustification' in missing_fields:
                incident_analysis['riskLikelihoodJustification'] = incident_analysis.get(
                    'riskLikelihoodJustification',
                    "General security incident with moderate likelihood based on current threat landscape. "
                    "Score of 5 reflects balanced assessment.",
                )

            if 'riskImpactJustification' in missing_fields:
                incident_analysis['riskImpactJustification'] = incident_analysis.get(
                    'riskImpactJustification',
                    "Potential impact is moderate considering banking sector criticality and customer data "
                    "sensitivity. Score of 5 reflects standard risk level.",
                )

            if 'riskMitigation' in missing_fields:
                # Ensure we always have at least a few generic mitigation steps
                incident_analysis['riskMitigation'] = [
                    "Step 1: Isolate affected systems to prevent further compromise",
                    "Step 2: Initiate incident response procedures according to the security policy",
                    "Step 3: Notify relevant stakeholders and regulatory bodies if required",
                    "Step 4: Perform forensic analysis to determine the extent of the breach",
                    "Step 5: Implement remediation actions to address the vulnerability",
                    "Step 6: Update security controls to prevent similar incidents",
                    "Step 7: Conduct post-incident review and update documentation",
                ]
        
        # Ensure likelihood and impact are present and integers between 1-10
        if 'riskLikelihood' not in incident_analysis:
            incident_analysis['riskLikelihood'] = 5

        if 'riskImpact' not in incident_analysis:
            incident_analysis['riskImpact'] = 5

        try:
            likelihood = int(incident_analysis.get('riskLikelihood', 5))
            incident_analysis['riskLikelihood'] = max(1, min(10, likelihood))
        except (ValueError, TypeError):
            debug_print(f"⚠️ Invalid riskLikelihood value, using default 5")
            incident_analysis['riskLikelihood'] = 5

        try:
            impact = int(incident_analysis.get('riskImpact', 5))
            incident_analysis['riskImpact'] = max(1, min(10, impact))
        except (ValueError, TypeError):
            debug_print(f"⚠️ Invalid riskImpact value, using default 5")
            incident_analysis['riskImpact'] = 5
        
        # Ensure list fields are actually lists
        list_fields = ['riskMitigation']
        for field in list_fields:
            if field in incident_analysis:
                if not isinstance(incident_analysis[field], list):
                    # Convert to list if it's a string
                    if isinstance(incident_analysis[field], str):
                        incident_analysis[field] = [incident_analysis[field]]
                    else:
                        debug_print(f"⚠️ Field {field} is not a list, converting to empty list")
                        incident_analysis[field] = []
        
        debug_print(
            f"✅ Successfully parsed risk analysis with likelihood={incident_analysis.get('riskLikelihood')}, "
            f"impact={incident_analysis.get('riskImpact')}"
        )
        return incident_analysis
        
    except json.JSONDecodeError as e:
        debug_print(f"❌ JSON parsing error: {e}")
        debug_print(f"Response text: {response[:500]}...")  # Print first 500 chars for debugging
        return None
    except Exception as e:
        debug_print(f"❌ Unexpected error during parsing: {e}")
        traceback.print_exc()
        return None

def generate_fallback_analysis(incident_description):
    """Generate a fallback analysis when the AI model is unavailable."""
    # Extract some keywords from the incident for basic categorization
    description_lower = incident_description.lower()
    
    # Default values
    criticality = "Significant"
    category = "IT Security"
    likelihood_score = 5
    impact_score = 5
    priority = "P1"
    
    # Basic categorization based on keywords and assign appropriate scores
    if any(word in description_lower for word in ["breach", "leak", "exposed", "data", "sensitive"]):
        category = "Data Breach"
        criticality = "Severe"
        likelihood_score = 7
        impact_score = 8
        priority = "P0"
        likelihood_justification = "Data breaches have high likelihood due to increasing cyber threats and the valuable nature of banking data. Score of 7 reflects significant threat landscape."
        impact_justification = "Data breaches can cause severe financial losses, regulatory penalties, and reputational damage. Score of 8 reflects major consequences for banking operations."
    elif any(word in description_lower for word in ["malware", "virus", "ransomware", "trojan"]):
        category = "Malware"
        criticality = "Severe"
        likelihood_score = 6
        impact_score = 8
        likelihood_justification = "Malware attacks are moderately likely given current threat environment and banking sector targeting. Score of 6 reflects ongoing risk."
        impact_justification = "Malware can disrupt critical banking systems, encrypt data, and halt operations. Score of 8 reflects severe operational impact."
    elif any(word in description_lower for word in ["phish", "social engineering", "impersonation"]):
        category = "Phishing"
        likelihood_score = 7
        impact_score = 6
        likelihood_justification = "Phishing attacks are highly likely as they target human vulnerabilities and are easy to execute. Score of 7 reflects frequent occurrence."
        impact_justification = "Phishing can lead to credential theft and unauthorized access but impact is more limited. Score of 6 reflects moderate consequences."
    elif any(word in description_lower for word in ["unauthorized", "access", "privilege", "credential"]):
        category = "Unauthorized Access"
        likelihood_score = 6
        impact_score = 7
        likelihood_justification = "Unauthorized access attempts are moderately likely given credential-based attacks. Score of 6 reflects consistent threat level."
        impact_justification = "Unauthorized access can compromise sensitive data and systems integrity. Score of 7 reflects significant potential damage."
    elif any(word in description_lower for word in ["ddos", "denial", "service", "availability"]):
        category = "Denial of Service"
        likelihood_score = 5
        impact_score = 6
        likelihood_justification = "DDoS attacks have moderate likelihood, often used for distraction or service disruption. Score of 5 reflects balanced risk."
        impact_justification = "Service denial can disrupt customer access and operations but recovery is usually possible. Score of 6 reflects moderate impact."
    elif any(word in description_lower for word in ["compliance", "regulatory", "regulation"]):
        category = "Compliance"
        likelihood_score = 4
        impact_score = 7
        likelihood_justification = "Compliance violations have lower likelihood with proper controls but regulatory changes increase risk. Score of 4 reflects controlled environment."
        impact_justification = "Compliance violations can result in significant fines and regulatory sanctions. Score of 7 reflects serious consequences."
    else:
        # Default case
        likelihood_justification = "General security incident with moderate likelihood based on current threat landscape. Score of 5 reflects balanced assessment."
        impact_justification = "Potential impact is moderate considering banking sector criticality and customer data sensitivity. Score of 5 reflects standard risk level."
    
    # Extract a title if possible
    title_match = None
    if "Title:" in incident_description:
        title_parts = incident_description.split("Title:", 1)[1].split("\n", 1)
        if title_parts:
            title_match = title_parts[0].strip()
    
    title = title_match or "Security Incident"
    
    return {
        "criticality": criticality,
        "possibleDamage": "Potential data exposure, system compromise, and reputational damage to the organization.",
        "category": category,
        "riskDescription": f"If this {category.lower()} incident is not properly addressed, it may lead to unauthorized access to sensitive data, financial loss, and regulatory penalties.",
        "riskLikelihood": likelihood_score,
        "riskLikelihoodJustification": likelihood_justification,
        "riskImpact": impact_score,
        "riskImpactJustification": impact_justification,
        "riskExposureRating": "High Exposure",
        "riskPriority": priority,
        "riskAppetite": "Exceeds Appetite",
        "riskMitigation": [
            "Step 1: Isolate affected systems to prevent further compromise",
            "Step 2: Initiate incident response procedures according to the security policy",
            "Step 3: Notify relevant stakeholders and regulatory bodies if required",
            "Step 4: Perform forensic analysis to determine the extent of the breach",
            "Step 5: Implement remediation actions to address the vulnerability",
            "Step 6: Update security controls to prevent similar incidents",
            "Step 7: Conduct post-incident review and update documentation"
        ]
    }


def generate_risk_fallback_analysis(risk_title, risk_description):
    """Generate a fallback risk analysis when the AI model is unavailable."""
    description_lower = f"{risk_title} {risk_description}".lower()
    
    # Default values for risk analysis
    criticality = "Medium"
    category = "Operational"
    likelihood_score = 5
    impact_score = 5
    
    # Risk-specific categorization based on keywords
    if any(word in description_lower for word in ["security", "cyber", "breach", "attack", "hack"]):
        category = "Information Security"
        criticality = "High"
        likelihood_score = 6
        impact_score = 7
        likelihood_justification = "Security risks have elevated likelihood due to increasing cyber threats and attack sophistication. Score reflects current threat landscape."
        impact_justification = "Security incidents can cause significant operational disruption, data exposure, and regulatory penalties. Score reflects banking sector security requirements."
    elif any(word in description_lower for word in ["financial", "credit", "market", "liquidity", "fraud"]):
        category = "Financial"
        criticality = "High"
        likelihood_score = 5
        impact_score = 8
        likelihood_justification = "Financial risks have moderate likelihood based on market conditions and control environment. Score reflects banking risk profile."
        impact_justification = "Financial risks can cause substantial losses and regulatory scrutiny. Score reflects materiality thresholds for banking operations."
    elif any(word in description_lower for word in ["compliance", "regulatory", "audit", "violation"]):
        category = "Compliance"
        criticality = "High"
        likelihood_score = 4
        impact_score = 7
        likelihood_justification = "Compliance risks have controlled likelihood with proper oversight but regulatory changes increase exposure. Score reflects control effectiveness."
        impact_justification = "Compliance violations result in regulatory penalties and reputational damage. Score reflects banking regulatory environment."
    elif any(word in description_lower for word in ["operational", "process", "system", "technology"]):
        category = "Operational"
        likelihood_score = 6
        impact_score = 6
        likelihood_justification = "Operational risks have elevated likelihood due to process complexity and system dependencies. Score reflects operational environment."
        impact_justification = "Operational failures can disrupt services and affect customer experience. Score reflects business continuity requirements."
    elif any(word in description_lower for word in ["strategic", "business", "market", "competition"]):
        category = "Strategic"
        likelihood_score = 5
        impact_score = 6
        likelihood_justification = "Strategic risks have moderate likelihood based on market dynamics and competitive position. Score reflects business environment."
        impact_justification = "Strategic risks affect long-term objectives and market position. Score reflects strategic importance to organization."
    else:
        # Default case
        likelihood_justification = "General risk with moderate likelihood based on standard risk assessment. Score reflects balanced risk profile."
        impact_justification = "Potential impact is moderate considering business operations and risk management controls. Score reflects typical risk exposure."
    
    return {
        "criticality": criticality,
        "criticalityJustification": f"Risk criticality assessed as {criticality} based on potential business impact, regulatory requirements, and operational significance. Follows enterprise risk management framework.",
        "riskLikelihood": likelihood_score,
        "riskLikelihoodJustification": likelihood_justification,
        "riskImpact": impact_score,
        "riskImpactJustification": impact_justification,
        "possibleDamage": f"Potential {category.lower()} impact including financial losses, operational disruption, regulatory penalties, and reputational damage depending on risk scenario.",
        "possibleDamageJustification": "Damage assessment considers direct and indirect costs, business interruption, regulatory exposure, and stakeholder impact based on risk materialization scenarios.",
        "category": category,
        "categoryJustification": f"Risk categorized as {category} based on primary impact domain and business function affected. Classification aligns with enterprise risk taxonomy.",
        "businessImpact": f"Moderate to significant impact on {category.lower()} functions and business continuity depending on risk materialization and control effectiveness.",
        "businessImpactJustification": "Business impact assessment covers revenue effects, operational continuity, customer relationships, and strategic objectives based on risk scenario analysis.",
        "riskMitigation": [
            f"Implement {category.lower()}-specific controls and monitoring systems",
            "Establish regular risk assessment and review processes",
            "Develop incident response and business continuity plans",
            "Ensure adequate training and awareness programs",
            "Maintain appropriate insurance coverage and risk transfer mechanisms"
        ],
        "riskMitigationJustification": "Mitigation strategies selected based on risk-control effectiveness analysis, regulatory requirements, and cost-benefit considerations. Implementation prioritized by risk exposure and business criticality."
    } 