"""
Step 2: Domain & Context Classification Service
Uses NVIDIA (OpenAI-compatible) with fallback to OpenAI
No character limits anywhere
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DomainClassificationResult:
    """Result of domain classification."""
    primary_domain: str
    industry_vertical: Optional[str]
    business_function: Optional[str]
    compliance_area: Optional[str]
    compliance_standards: Optional[list] = None  # Standards detected
    control_type: Optional[str] = None
    risk_category: Optional[str] = None
    confidence: float = 0.0
    classification_method: str = 'fallback'  # 'nvidia', 'openai', 'fallback'
    reasoning: str = ''
    context_used: Dict[str, Any] = None
    raw_response: Optional[Dict] = None


class DomainClassifier:
    """
    Hierarchical domain classifier using NVIDIA/OpenAI.
    Different prompts for each entity type.
    """
    
    def __init__(self):
        self.nvidia_api_key = os.environ.get('NVIDIA_API_KEY')
        self.nvidia_api_url = os.environ.get('NVIDIA_API_URL', 'https://integrate.api.nvidia.com/v1/chat/completions')
        self.nvidia_model = os.environ.get('NVIDIA_MODEL', 'meta/llama-3.1-70b-instruct')
        
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.openai_api_url = os.environ.get('OPENAI_API_URL', 'https://api.openai.com/v1/chat/completions')
        self.openai_model = os.environ.get('OPENAI_MODEL', 'gpt-4')
        
        self.provider = os.environ.get('RISK_AI_PROVIDER', 'nvidia').lower()
        self.timeout = int(os.environ.get('AI_TIMEOUT', '30'))
        self.temperature = float(os.environ.get('AI_TEMPERATURE', '0.3'))
    
    def classify_framework(self, framework_data: Dict[str, Any]) -> DomainClassificationResult:
        """
        Classify framework domain using its own fields only.
        No parent context needed for frameworks.
        """
        logger.info("[STEP 2] Classifying Framework domain")
        
        prompt = self._build_framework_prompt(framework_data)
        response = self._call_llm(prompt)
        
        return DomainClassificationResult(
            primary_domain=response.get('primary_domain', 'Unknown'),
            industry_vertical=response.get('industry_vertical'),
            business_function=None,
            compliance_area=response.get('compliance_standards'),
            control_type=None,
            risk_category=None,
            confidence=response.get('confidence', 0.0),
            classification_method=response.get('method', 'unknown'),
            reasoning=response.get('reasoning', ''),
            context_used={'framework_fields': list(framework_data.keys())},
            raw_response=response
        )
    
    def classify_policy(self, policy_data: Dict[str, Any], framework_context: Dict[str, Any]) -> DomainClassificationResult:
        """
        Classify policy using parent framework context + policy fields.
        """
        logger.info("[STEP 2] Classifying Policy domain with Framework context")
        
        prompt = self._build_policy_prompt(policy_data, framework_context)
        response = self._call_llm(prompt)
        
        return DomainClassificationResult(
            primary_domain=response.get('primary_domain', framework_context.get('domain', 'Unknown')),
            industry_vertical=None,
            business_function=response.get('business_function'),
            compliance_area=response.get('compliance_area'),
            control_type=None,
            risk_category=None,
            confidence=response.get('confidence', 0.0),
            classification_method=response.get('method', 'unknown'),
            reasoning=response.get('reasoning', ''),
            context_used={
                'framework_context': framework_context,
                'policy_fields': list(policy_data.keys())
            },
            raw_response=response
        )
    
    def classify_subpolicy(self, subpolicy_data: Dict[str, Any], 
                          framework_context: Dict[str, Any],
                          policy_context: Dict[str, Any]) -> DomainClassificationResult:
        """
        Classify subpolicy using Framework + Policy context.
        """
        logger.info("[STEP 2] Classifying SubPolicy with full parent context")
        
        prompt = self._build_subpolicy_prompt(subpolicy_data, framework_context, policy_context)
        response = self._call_llm(prompt)
        
        return DomainClassificationResult(
            primary_domain=response.get('primary_domain', framework_context.get('domain', 'Unknown')),
            industry_vertical=None,
            business_function=response.get('business_function', policy_context.get('business_function')),
            compliance_area=response.get('compliance_area', policy_context.get('compliance_area')),
            control_type=response.get('control_type'),
            risk_category=None,
            confidence=response.get('confidence', 0.0),
            classification_method=response.get('method', 'unknown'),
            reasoning=response.get('reasoning', ''),
            context_used={
                'framework_context': framework_context,
                'policy_context': policy_context,
                'subpolicy_fields': list(subpolicy_data.keys())
            },
            raw_response=response
        )
    
    def classify_compliance(self, compliance_data: Dict[str, Any],
                           framework_context: Dict[str, Any],
                           policy_context: Dict[str, Any],
                           subpolicy_context: Dict[str, Any]) -> DomainClassificationResult:
        """
        Classify compliance using complete hierarchy context.
        """
        logger.info("[STEP 2] Classifying Compliance with full GRC hierarchy")
        
        prompt = self._build_compliance_prompt(compliance_data, framework_context, policy_context, subpolicy_context)
        response = self._call_llm(prompt)
        
        return DomainClassificationResult(
            primary_domain=response.get('primary_domain', framework_context.get('domain', 'Unknown')),
            industry_vertical=None,
            business_function=response.get('business_function', policy_context.get('business_function')),
            compliance_area=response.get('compliance_area', policy_context.get('compliance_area')),
            control_type=response.get('control_type', subpolicy_context.get('control_type')),
            risk_category=response.get('risk_category'),
            confidence=response.get('confidence', 0.0),
            classification_method=response.get('method', 'unknown'),
            reasoning=response.get('reasoning', ''),
            context_used={
                'framework_context': framework_context,
                'policy_context': policy_context,
                'subpolicy_context': subpolicy_context,
                'compliance_fields': list(compliance_data.keys())
            },
            raw_response=response
        )
    
    def _build_framework_prompt(self, data: Dict[str, Any]) -> str:
        """Build prompt for framework classification. Generic, no examples."""
        return f"""You are a GRC domain classifier. Analyze the following framework and classify its industry domain.

FRAMEWORK INFORMATION:
- Name: {data.get('name', '')}
- Description: {data.get('description', '')}
- Category: {data.get('category', '')}
- Type: {data.get('type', '')}
- Identifier: {data.get('identifier', '')}

CLASSIFICATION TASK:
1. Identify the primary industry domain based on content analysis
2. Identify the specific industry vertical if applicable
3. Detect any compliance standards or regulatory frameworks referenced
4. List key domain indicator keywords found in the text
5. Provide confidence score (0.0 to 1.0)
6. Explain your reasoning based on the actual content provided

Respond with JSON only in this exact format:
{{
  "primary_domain": "Extracted primary industry/domain",
  "industry_vertical": "Specific industry vertical if applicable",
  "compliance_standards": ["List", "of", "detected", "standards"],
  "keywords": ["key", "domain", "indicators"],
  "confidence": 0.95,
  "reasoning": "Explanation based on actual content analysis"
}}"""
    
    def _build_policy_prompt(self, policy_data: Dict[str, Any], framework_context: Dict[str, Any]) -> str:
        """Build prompt for policy classification with parent framework context."""
        return f"""You are a GRC policy classifier. Analyze this policy within its parent framework context.

PARENT FRAMEWORK CONTEXT:
- Framework Domain: {framework_context.get('domain', 'Unknown')}
- Framework Industry: {framework_context.get('industry_vertical', 'Unknown')}
- Framework Name: {framework_context.get('name', '')}

POLICY INFORMATION:
- Name: {policy_data.get('name', '')}
- Description: {policy_data.get('description', '')}
- Type: {policy_data.get('policy_type', '')}
- Category: {policy_data.get('category', '')}
- SubCategory: {policy_data.get('sub_category', '')}
- Scope: {policy_data.get('scope', '')}
- Objective: {policy_data.get('objective', '')}

CLASSIFICATION TASK:
1. Confirm or refine the domain based on framework context provided
2. Identify the business function from the policy scope and objective
3. Identify the compliance area addressed by this policy
4. Assess policy maturity level based on comprehensiveness
5. Provide confidence score (0.0 to 1.0)
6. Explain your reasoning based on actual policy content

Respond with JSON only in this exact format:
{{
  "primary_domain": "Confirmed or refined domain",
  "business_function": "Identified business function",
  "compliance_area": "Specific compliance area",
  "maturity_level": "Basic/Standard/Advanced",
  "confidence": 0.88,
  "reasoning": "Explanation based on policy content analysis"
}}"""
    
    def _build_subpolicy_prompt(self, subpolicy_data: Dict[str, Any], 
                             framework_context: Dict[str, Any],
                             policy_context: Dict[str, Any]) -> str:
        """Build prompt for subpolicy with full parent context."""
        return f"""You are a GRC subpolicy classifier. Analyze this subpolicy within its full hierarchy.

GRANDPARENT FRAMEWORK:
- Domain: {framework_context.get('domain', 'Unknown')}
- Industry: {framework_context.get('industry_vertical', 'Unknown')}
- Name: {framework_context.get('name', '')}

PARENT POLICY:
- Business Function: {policy_context.get('business_function', 'Unknown')}
- Compliance Area: {policy_context.get('compliance_area', 'Unknown')}
- Name: {policy_context.get('name', '')}

SUBPOLICY INFORMATION:
- Name: {subpolicy_data.get('name', '')}
- Description: {subpolicy_data.get('description', '')}
- Control: {subpolicy_data.get('control', '')}
- Identifier: {subpolicy_data.get('identifier', '')}

CLASSIFICATION TASK:
1. Confirm domain from parent hierarchy context
2. Confirm business function from parent policy context
3. Classify control type based on control description
4. Identify specific control category
5. Provide confidence score (0.0 to 1.0)
6. Explain your reasoning based on actual control content

Respond with JSON only in this exact format:
{{
  "primary_domain": "Confirmed domain",
  "business_function": "Confirmed business function",
  "control_type": "Preventive/Detective/Corrective/Administrative/Technical/Physical",
  "control_category": "Specific control category",
  "confidence": 0.91,
  "reasoning": "Explanation based on control content analysis"
}}"""
    
    def _build_compliance_prompt(self, compliance_data: Dict[str, Any],
                                framework_context: Dict[str, Any],
                                policy_context: Dict[str, Any],
                                subpolicy_context: Dict[str, Any]) -> str:
        """Build prompt for compliance with complete hierarchy."""
        return f"""You are a GRC compliance classifier. Analyze this compliance item within the complete GRC hierarchy.

FULL HIERARCHY CONTEXT:

Level 1 - Framework:
- Domain: {framework_context.get('domain', 'Unknown')}
- Industry: {framework_context.get('industry_vertical', 'Unknown')}
- Name: {framework_context.get('name', '')}

Level 2 - Policy:
- Business Function: {policy_context.get('business_function', 'Unknown')}
- Compliance Area: {policy_context.get('compliance_area', 'Unknown')}
- Name: {policy_context.get('name', '')}

Level 3 - SubPolicy:
- Control Type: {subpolicy_context.get('control_type', 'Unknown')}
- Control Category: {subpolicy_context.get('control_category', 'Unknown')}
- Name: {subpolicy_context.get('name', '')}

Level 4 - Compliance (This Item):
- Title: {compliance_data.get('title', '')}
- Description: {compliance_data.get('description', '')}
- Compliance Type: {compliance_data.get('compliance_type', '')}
- Criticality: {compliance_data.get('criticality', '')}
- Risk Category: {compliance_data.get('risk_category', '')}
- Scope: {compliance_data.get('scope', '')}
- Objective: {compliance_data.get('objective', '')}

CLASSIFICATION TASK:
1. Confirm domain from hierarchy context
2. Confirm business function from hierarchy context
3. Confirm control type from hierarchy context
4. Assess risk level based on criticality and context
5. Recommend audit frequency based on risk assessment
6. Identify specific risk domain based on full context
7. Provide confidence score (0.0 to 1.0)
8. Explain your reasoning based on actual content analysis

Respond with JSON only in this exact format:
{{
  "primary_domain": "Confirmed primary domain",
  "business_function": "Confirmed business function",
  "control_type": "Confirmed control type",
  "risk_level": "Low/Medium/High/Critical",
  "audit_frequency": "Recommended frequency",
  "risk_domain": "Specific risk domain identified",
  "confidence": 0.93,
  "reasoning": "Explanation based on compliance content analysis"
}}"""
    
    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Call LLM with NVIDIA primary, fallback to OpenAI.
        No character limits on input.
        """
        # Try NVIDIA first if configured
        if self.provider == 'nvidia' and self.nvidia_api_key:
            try:
                logger.info("[STEP 2] Calling NVIDIA for classification")
                result = self._call_nvidia(prompt)
                result['method'] = 'nvidia'
                return result
            except Exception as e:
                logger.warning(f"[STEP 2] NVIDIA failed, falling back to OpenAI: {e}")
        
        # Fallback to OpenAI
        if self.openai_api_key:
            try:
                logger.info("[STEP 2] Calling OpenAI for classification")
                result = self._call_openai(prompt)
                result['method'] = 'openai'
                return result
            except Exception as e:
                logger.error(f"[STEP 2] OpenAI also failed: {e}")
        
        # Ultimate fallback - return unknown
        logger.error("[STEP 2] All LLM providers failed")
        return {
            'primary_domain': 'Unknown',
            'confidence': 0.0,
            'reasoning': 'All AI providers failed',
            'method': 'fallback'
        }
    
    def _call_nvidia(self, prompt: str) -> Dict[str, Any]:
        """Call NVIDIA API (OpenAI-compatible endpoint)."""
        import requests
        
        headers = {
            'Authorization': f'Bearer {self.nvidia_api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.nvidia_model,
            'messages': [
                {'role': 'system', 'content': 'You are a GRC domain classifier. Return only valid JSON.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': self.temperature,
            'max_tokens': 2000  # No hard limit, but reasonable cap for response
        }
        
        response = requests.post(
            self.nvidia_api_url,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Parse JSON from content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            raise
    
    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Call OpenAI API (or NVIDIA OpenAI-compatible API)."""
        import requests
        
        headers = {
            'Authorization': f'Bearer {self.openai_api_key}',
            'Content-Type': 'application/json'
        }
        
        # Detect if using NVIDIA API
        is_nvidia = 'nvidia.com' in self.openai_api_url or 'integrate.api.nvidia' in self.openai_api_url
        
        if is_nvidia:
            # NVIDIA uses model-specific endpoints
            # Extract base URL and construct model endpoint
            base_url = self.openai_api_url.replace('/v1/chat/completions', '').replace('/chat/completions', '')
            # Use model from payload or default
            model_name = self.openai_model if self.openai_model else 'meta/llama-3.1-70b-instruct'
            # Remove 'nvidia/' prefix if present for some models
            if model_name.startswith('nvidia/'):
                model_name = model_name[7:]  # Remove 'nvidia/' prefix
            url = f"{base_url}/v1/{model_name}"
            payload = {
                'model': model_name,
                'messages': [
                    {'role': 'system', 'content': 'You are a GRC domain classifier. Return only valid JSON.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': self.temperature,
                'max_tokens': 2000
            }
        else:
            # Standard OpenAI
            url = self.openai_api_url
            payload = {
                'model': self.openai_model,
                'messages': [
                    {'role': 'system', 'content': 'You are a GRC domain classifier. Return only valid JSON.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': self.temperature,
                'max_tokens': 2000
            }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            raise


# Convenience function
classify_domain = DomainClassifier()
