"""
Few-Shot Prompt Templates
- 25-35% accuracy improvement with examples
- Provides context and format guidance to LLM
"""
from typing import Dict, Any

# Risk Extraction Examples
RISK_EXTRACTION_EXAMPLES = """
Example 1:
Document: "Risk 1: Data Breach - Unauthorized access to customer database could result in exposure of 50,000 customer records."
Extracted:
{
  "RiskTitle": "Data Breach",
  "Criticality": "High",
  "PossibleDamage": "Exposure of 50,000 customer records, potential regulatory fines, reputation damage",
  "Category": "Information Security",
  "RiskType": "Current",
  "BusinessImpact": "Regulatory compliance violations, customer trust loss, potential GDPR fines up to 4% of revenue",
  "RiskDescription": "Unauthorized access to customer database could result in data exposure",
  "RiskLikelihood": 6,
  "RiskImpact": 9,
  "RiskExposureRating": 54.0,
  "RiskPriority": "High",
  "RiskMitigation": "1. Implement multi-factor authentication 2. Encrypt database at rest 3. Regular security audits 4. Access control reviews"
}

Example 2:
Document: "Risk 2: Vendor Dependency - Over-reliance on single cloud provider for critical infrastructure."
Extracted:
{
  "RiskTitle": "Vendor Dependency",
  "Criticality": "Medium",
  "PossibleDamage": "Service disruption if vendor fails, limited negotiation power, vendor lock-in",
  "Category": "Third-Party",
  "RiskType": "Current",
  "BusinessImpact": "Potential service outages affecting 80% of operations, increased costs due to lack of alternatives",
  "RiskDescription": "Over-reliance on single cloud provider creates dependency risk",
  "RiskLikelihood": 4,
  "RiskImpact": 7,
  "RiskExposureRating": 28.0,
  "RiskPriority": "Medium",
  "RiskMitigation": "1. Identify backup providers 2. Develop migration plan 3. Negotiate SLA terms 4. Regular vendor assessments"
}

Example 3:
Document: "Risk 3: Compliance Gap - Missing SOC 2 Type II certification for cloud services."
Extracted:
{
  "RiskTitle": "Compliance Gap - SOC 2",
  "Criticality": "High",
  "PossibleDamage": "Regulatory penalties, loss of customer contracts, audit findings",
  "Category": "Compliance",
  "RiskType": "Current",
  "BusinessImpact": "Inability to serve enterprise clients requiring SOC 2, potential revenue loss of $2M annually",
  "RiskDescription": "Cloud services lack required SOC 2 Type II certification",
  "RiskLikelihood": 5,
  "RiskImpact": 8,
  "RiskExposureRating": 40.0,
  "RiskPriority": "High",
  "RiskMitigation": "1. Initiate SOC 2 audit process 2. Implement required controls 3. Engage certified auditor 4. Target completion within 12 months"
}
"""

# Field-specific extraction examples
FIELD_EXTRACTION_EXAMPLES = {
    "Criticality": """
Example: "High-risk vulnerability" → Criticality: "High"
Example: "Moderate impact" → Criticality: "Medium"
Example: "Low priority issue" → Criticality: "Low"
Example: "Critical system failure" → Criticality: "Critical"
""",
    
    "RiskLikelihood": """
Example: "Occurs frequently" → RiskLikelihood: 8
Example: "Rare occurrence" → RiskLikelihood: 2
Example: "50% chance" → RiskLikelihood: 5
Example: "Almost certain" → RiskLikelihood: 9
""",
    
    "RiskImpact": """
Example: "Catastrophic consequences" → RiskImpact: 10
Example: "Minor inconvenience" → RiskImpact: 2
Example: "Significant business disruption" → RiskImpact: 7
Example: "Negligible effect" → RiskImpact: 1
""",
    
    "Category": """
Example: "Security breach" → Category: "Information Security"
Example: "Vendor issue" → Category: "Third-Party"
Example: "Regulatory violation" → Category: "Compliance"
Example: "Financial loss" → Category: "Financial"
Example: "Process failure" → Category: "Operational"
""",
    
    "RiskMitigation": """
Example: "Implement encryption, conduct regular audits, establish access controls"
→ RiskMitigation: "1. Implement encryption at rest and in transit 2. Conduct quarterly security audits 3. Establish role-based access controls 4. Monitor access logs"
"""
}

def build_few_shot_prompt(task_type: str, document_text: str, field_name: str = None, 
                         field_prompts: dict = None) -> str:
    """
    Build prompt with few-shot examples.
    
    Args:
        task_type: 'risk_extraction', 'field_extraction'
        document_text: Document to analyze
        field_name: Optional specific field to extract
        field_prompts: Optional field-specific prompts dict
    
    Returns:
        Formatted prompt with examples
    """
    examples = {
        'risk_extraction': RISK_EXTRACTION_EXAMPLES,
    }
    
    example_text = examples.get(task_type, "")
    
    if field_name and field_prompts:
        # Single field extraction with field-specific examples
        field_example = FIELD_EXTRACTION_EXAMPLES.get(field_name, "")
        field_guidance = field_prompts.get(field_name, "Extract this field from the document.")
        
        prompt = f"""
You are a GRC analyst. Extract the field "{field_name}" from this document.

{field_example}

Guidance: {field_guidance}

Document to analyze:
\"\"\"{document_text[:3000]}\"\"\"

Extract ONLY the "{field_name}" field. Return JSON: {{"value": "...", "confidence": 0.0-1.0, "rationale": "brief explanation"}}
"""
    elif field_name:
        # Single field extraction without examples
        prompt = f"""
You are a GRC analyst. Extract the field "{field_name}" from this document.

Document to analyze:
\"\"\"{document_text[:3000]}\"\"\"

Extract ONLY the "{field_name}" field. Return JSON: {{"value": "...", "confidence": 0.0-1.0, "rationale": "brief explanation"}}
"""
    else:
        # Full risk extraction with examples
        prompt = f"""
You are a GRC analyst. Extract ALL risk information from this document.

{example_text}

Document to analyze:
\"\"\"{document_text[:8000]}\"\"\"

Extract all risks following the examples above. Return a JSON array of risks, each with all required fields.
Follow the exact structure and format shown in the examples.
"""
    
    return prompt

def get_field_extraction_prompt(field_name: str, document_text: str, field_prompts: dict) -> str:
    """
    Get optimized prompt for single field extraction with few-shot examples.
    
    Args:
        field_name: Field to extract
        document_text: Document context
        field_prompts: Field-specific prompts dict
    
    Returns:
        Optimized prompt
    """
    return build_few_shot_prompt(
        task_type='field_extraction',
        document_text=document_text,
        field_name=field_name,
        field_prompts=field_prompts
    )

def get_risk_extraction_prompt(document_text: str) -> str:
    """
    Get optimized prompt for full risk extraction with few-shot examples.
    
    Args:
        document_text: Document to analyze
    
    Returns:
        Optimized prompt
    """
    return build_few_shot_prompt(
        task_type='risk_extraction',
        document_text=document_text,
        field_name=None
    )

# Compliance Generation Examples
COMPLIANCE_GENERATION_EXAMPLES = """
Example 1:
Subpolicy: "Access Control Policy"
Description: "All users must authenticate using multi-factor authentication before accessing sensitive systems."
Control: "Implement MFA for all privileged accounts and systems containing sensitive data."

Generated Compliance:
{
    "compliances": [
        {
            "Identifier": "COMP-001",
            "ComplianceTitle": "Multi-Factor Authentication for Privileged Access",
            "ComplianceItemDescription": "All privileged accounts and systems containing sensitive data must require multi-factor authentication (MFA) before access is granted. This includes administrator accounts, database access, and systems processing payment card information.",
            "ComplianceType": "Regulatory",
            "Scope": "All privileged user accounts, systems containing sensitive data, and administrative interfaces",
            "Objective": "Prevent unauthorized access through compromised credentials by requiring multiple authentication factors",
            "BusinessUnitsCovered": "IT, Security, Operations, Finance",
            "IsRisk": 1,
            "PossibleDamage": "Unauthorized access to sensitive systems, data breaches, regulatory violations, financial losses",
            "mitigation": {
                "1": "Implement MFA for all privileged accounts",
                "2": "Conduct quarterly access reviews",
                "3": "Monitor authentication failures and suspicious access patterns"
            },
            "Criticality": "High",
            "MandatoryOptional": "Mandatory",
            "ManualAutomatic": "Automatic",
            "Impact": 8.5,
            "Probability": 6.0,
            "MaturityLevel": "Defined",
            "ActiveInactive": "Active",
            "PermanentTemporary": "Permanent",
            "CreatedByName": "radha.sharma",
            "CreatedByDate": "2024-01-15",
            "ComplianceVersion": "1.0",
            "Status": "Approved",
            "Applicability": "Global",
            "PotentialRiskScenarios": "Credential theft leading to unauthorized system access, insider threats, external attackers gaining privileged access",
            "RiskType": "Current",
            "RiskCategory": "Information Security",
            "RiskBusinessImpact": "IT operations, customer data protection, regulatory compliance",
            "risk": {
                "RiskTitle": "Unauthorized Privileged Access",
                "Criticality": "High",
                "PossibleDamage": "Data breaches, system compromise, regulatory violations",
                "Category": "Information Security",
                "RiskType": "Current",
                "BusinessImpact": "Potential exposure of sensitive customer data, regulatory fines, reputation damage",
                "RiskDescription": "Without MFA, compromised credentials could allow unauthorized access to privileged systems and sensitive data",
                "RiskLikelihood": 6,
                "RiskImpact": 9,
                "RiskExposureRating": 54.0,
                "RiskPriority": "High",
                "RiskMitigation": {
                    "1": "Implement MFA for all privileged accounts",
                    "2": "Regular access reviews and credential rotation",
                    "3": "Monitor and alert on suspicious access patterns"
                },
                "CreatedAt": "2024-01-15",
                "RiskMultiplierX": 0.1,
                "RiskMultiplierY": 0.1
            }
        }
    ]
}

Example 2:
Subpolicy: "Data Encryption Standards"
Description: "All sensitive data must be encrypted at rest and in transit using industry-standard encryption algorithms."
Control: "Encrypt all databases containing PII using AES-256 encryption. Use TLS 1.3 for all data in transit."

Generated Compliance:
{
    "compliances": [
        {
            "Identifier": "COMP-002",
            "ComplianceTitle": "Data Encryption for PII",
            "ComplianceItemDescription": "All personally identifiable information (PII) stored in databases must be encrypted at rest using AES-256 encryption. All data transmission must use TLS 1.3 or higher to ensure data protection in transit.",
            "ComplianceType": "Regulatory",
            "Scope": "All databases, file systems, and network communications containing PII",
            "Objective": "Protect sensitive personal information from unauthorized access through encryption",
            "BusinessUnitsCovered": "IT, Data Management, Security, Customer Service",
            "IsRisk": 1,
            "PossibleDamage": "Data breaches, identity theft, regulatory fines (GDPR up to 4% revenue), reputation damage",
            "mitigation": {
                "1": "Implement AES-256 encryption for all PII databases",
                "2": "Enforce TLS 1.3 for all data transmission",
                "3": "Regular encryption key rotation and management"
            },
            "Criticality": "Critical",
            "MandatoryOptional": "Mandatory",
            "ManualAutomatic": "Automatic",
            "Impact": 9.5,
            "Probability": 5.0,
            "MaturityLevel": "Managed",
            "ActiveInactive": "Active",
            "PermanentTemporary": "Permanent",
            "CreatedByName": "radha.sharma",
            "CreatedByDate": "2024-01-15",
            "ComplianceVersion": "1.0",
            "Status": "Approved",
            "Applicability": "Global",
            "PotentialRiskScenarios": "Database breach exposing unencrypted PII, man-in-the-middle attacks on data transmission, key compromise",
            "RiskType": "Current",
            "RiskCategory": "Privacy",
            "RiskBusinessImpact": "Customer data protection, regulatory compliance, legal liability",
            "risk": {
                "RiskTitle": "PII Data Exposure",
                "Criticality": "Critical",
                "PossibleDamage": "Massive data breach, GDPR fines, identity theft, legal liability",
                "Category": "Privacy",
                "RiskType": "Current",
                "BusinessImpact": "Regulatory fines up to 4% of annual revenue, customer trust loss, potential class-action lawsuits",
                "RiskDescription": "Unencrypted PII could be exposed in case of database breach or network interception",
                "RiskLikelihood": 5,
                "RiskImpact": 10,
                "RiskExposureRating": 50.0,
                "RiskPriority": "Critical",
                "RiskMitigation": {
                    "1": "Implement AES-256 encryption at rest",
                    "2": "Enforce TLS 1.3 for all data transmission",
                    "3": "Regular security audits and penetration testing"
                },
                "CreatedAt": "2024-01-15",
                "RiskMultiplierX": 0.1,
                "RiskMultiplierY": 0.1
            }
        }
    ]
}

Example 3:
Subpolicy: "Incident Response Procedures"
Description: "All security incidents must be reported within 1 hour of detection and investigated according to established procedures."
Control: "Establish 24/7 security operations center (SOC) to monitor, detect, and respond to security incidents. Maintain incident response playbook with escalation procedures."

Generated Compliance:
{
    "compliances": [
        {
            "Identifier": "COMP-003",
            "ComplianceTitle": "Security Incident Response and Reporting",
            "ComplianceItemDescription": "All security incidents must be detected, reported within 1 hour, and investigated according to established incident response procedures. A 24/7 Security Operations Center (SOC) must monitor systems and maintain an incident response playbook with clear escalation procedures.",
            "ComplianceType": "Internal",
            "Scope": "All IT systems, networks, applications, and security events",
            "Objective": "Ensure rapid detection, containment, and remediation of security incidents to minimize impact",
            "BusinessUnitsCovered": "Security, IT Operations, Risk Management, Legal",
            "IsRisk": 1,
            "PossibleDamage": "Extended security breaches, data loss, service disruption, regulatory reporting delays",
            "mitigation": {
                "1": "Establish 24/7 SOC with monitoring capabilities",
                "2": "Maintain comprehensive incident response playbook",
                "3": "Conduct quarterly incident response drills"
            },
            "Criticality": "High",
            "MandatoryOptional": "Mandatory",
            "ManualAutomatic": "Semi-Automatic",
            "Impact": 8.0,
            "Probability": 7.0,
            "MaturityLevel": "Defined",
            "ActiveInactive": "Active",
            "PermanentTemporary": "Permanent",
            "CreatedByName": "radha.sharma",
            "CreatedByDate": "2024-01-15",
            "ComplianceVersion": "1.0",
            "Status": "Approved",
            "Applicability": "Global",
            "PotentialRiskScenarios": "Undetected security breaches, delayed incident response, incomplete incident documentation, regulatory reporting failures",
            "RiskType": "Current",
            "RiskCategory": "Operational",
            "RiskBusinessImpact": "Security operations, business continuity, regulatory compliance",
            "risk": {
                "RiskTitle": "Delayed Incident Response",
                "Criticality": "High",
                "PossibleDamage": "Extended breach duration, increased data loss, regulatory penalties for delayed reporting",
                "Category": "Operational",
                "RiskType": "Current",
                "BusinessImpact": "Increased breach impact, potential regulatory fines, reputation damage from delayed disclosure",
                "RiskDescription": "Without proper incident response procedures, security incidents may go undetected or unaddressed, leading to extended breaches",
                "RiskLikelihood": 7,
                "RiskImpact": 8,
                "RiskExposureRating": 56.0,
                "RiskPriority": "High",
                "RiskMitigation": {
                    "1": "Establish 24/7 SOC monitoring",
                    "2": "Maintain incident response playbook",
                    "3": "Regular training and drills"
                },
                "CreatedAt": "2024-01-15",
                "RiskMultiplierX": 0.1,
                "RiskMultiplierY": 0.1
            }
        }
    ]
}
"""

# Policy Extraction Examples
POLICY_EXTRACTION_EXAMPLES = """
Example 1:
Section: "Access Control Requirements"
Content: "All users must authenticate before accessing systems. Privileged accounts require multi-factor authentication. Access must be reviewed quarterly."

Extracted:
{
    "has_policies": true,
    "policies": [
        {
            "policy_id": "NIST-CSF-SEC-001",
            "policy_title": "Access Control Policy",
            "policy_description": "Establishes requirements for user authentication and access management to ensure only authorized personnel can access organizational systems and data.",
            "policy_text": "All users must authenticate before accessing systems. Privileged accounts require multi-factor authentication. Access must be reviewed quarterly.",
            "scope": "This policy applies to all organizational units, personnel, systems, and processes involved in access control. The scope encompasses all information systems, networks, applications, databases, and associated infrastructure components.",
            "objective": "The primary objective of this policy is to establish clear requirements and guidelines for access control, ensuring organizational compliance and operational effectiveness. Specific objectives include: (1) protecting organizational assets from unauthorized access; (2) ensuring the confidentiality, integrity, and availability of information systems; (3) establishing robust security controls and monitoring mechanisms.",
            "policy_type": "Security",
            "policy_category": "Access Control and Identity Management",
            "policy_subcategory": "Identity and Authentication",
            "subpolicies": [
                {
                    "subpolicy_id": "NIST-CSF-SEC-001.01",
                    "subpolicy_title": "User Authentication Requirements",
                    "subpolicy_description": "All users must authenticate before accessing any organizational system or application.",
                    "control": "WHAT: Implement user authentication for all system access. WHO: IT Security team and system administrators. WHEN: Before every system access attempt. HOW: Use username/password or SSO authentication. WHERE: All organizational systems, applications, and network resources."
                },
                {
                    "subpolicy_id": "NIST-CSF-SEC-001.02",
                    "subpolicy_title": "Privileged Account Multi-Factor Authentication",
                    "subpolicy_description": "All privileged accounts must use multi-factor authentication (MFA) to prevent unauthorized access.",
                    "control": "WHAT: Require MFA for all privileged accounts. WHO: IT Security team. WHEN: Before every privileged access attempt. HOW: Use MFA tokens, SMS, or authenticator apps. WHERE: All systems with administrative or elevated privileges."
                },
                {
                    "subpolicy_id": "NIST-CSF-SEC-001.03",
                    "subpolicy_title": "Quarterly Access Reviews",
                    "subpolicy_description": "All user access must be reviewed quarterly to ensure appropriate access levels.",
                    "control": "WHAT: Review and validate all user access permissions. WHO: Access management team and department managers. WHEN: Quarterly (every 3 months). HOW: Generate access reports, review with managers, remove unnecessary access. WHERE: All systems and applications with user access."
                }
            ]
        }
    ],
    "document_type": "regulation",
    "confidence": 0.95
}

Example 2:
Section: "Data Protection Standards"
Content: "Sensitive data must be encrypted at rest and in transit. Encryption keys must be managed securely. Data classification is required."

Extracted:
{
    "has_policies": true,
    "policies": [
        {
            "policy_id": "NIST-CSF-SEC-002",
            "policy_title": "Data Protection and Encryption Policy",
            "policy_description": "Defines requirements for protecting sensitive data through encryption and secure key management to prevent unauthorized access and data breaches.",
            "policy_text": "Sensitive data must be encrypted at rest and in transit. Encryption keys must be managed securely. Data classification is required.",
            "scope": "This policy applies to all organizational units, personnel, systems, and processes involved in data protection. The scope encompasses all information systems, networks, applications, databases, and associated infrastructure components. It includes all employees, contractors, vendors, and third-party service providers who have access to organizational systems or data.",
            "objective": "The primary objective of this policy is to establish clear requirements and guidelines for data protection, ensuring organizational compliance and operational effectiveness. Specific objectives include: (1) protecting organizational assets from unauthorized access, modification, or destruction; (2) ensuring the confidentiality, integrity, and availability of information systems and data; (3) establishing robust security controls and monitoring mechanisms.",
            "policy_type": "Security",
            "policy_category": "Data Protection",
            "policy_subcategory": "Information Security and Encryption",
            "subpolicies": [
                {
                    "subpolicy_id": "NIST-CSF-SEC-002.01",
                    "subpolicy_title": "Data Encryption Requirements",
                    "subpolicy_description": "All sensitive data must be encrypted both at rest and during transmission.",
                    "control": "WHAT: Encrypt sensitive data at rest and in transit using industry-standard algorithms (AES-256). WHO: IT Security and Data Management teams. WHEN: Continuously for all sensitive data. HOW: Use AES-256 for data at rest, TLS 1.3 for data in transit. WHERE: All databases, file systems, and network communications containing sensitive data."
                },
                {
                    "subpolicy_id": "NIST-CSF-SEC-002.02",
                    "subpolicy_title": "Encryption Key Management",
                    "subpolicy_description": "Encryption keys must be managed securely with proper access controls and rotation procedures.",
                    "control": "WHAT: Implement secure key management practices including key rotation and access controls. WHO: IT Security team and key custodians. WHEN: Key rotation every 90 days, access reviews monthly. HOW: Use hardware security modules (HSM) or cloud key management services. WHERE: All systems using encryption for sensitive data."
                },
                {
                    "subpolicy_id": "NIST-CSF-SEC-002.03",
                    "subpolicy_title": "Data Classification Requirements",
                    "subpolicy_description": "All data must be classified according to sensitivity levels to determine appropriate protection measures.",
                    "control": "WHAT: Classify all organizational data by sensitivity (Public, Internal, Confidential, Restricted). WHO: Data owners and classification team. WHEN: At data creation and during periodic reviews. HOW: Use data classification tools and manual review processes. WHERE: All data repositories, file systems, and data processing systems."
                }
            ]
        }
    ],
    "document_type": "standard",
    "confidence": 0.92
}
"""

def get_compliance_generation_prompt(subpolicy_name: str, description: str, control: str, current_date: str) -> str:
    """
    Get optimized prompt for compliance generation with few-shot examples.
    
    Args:
        subpolicy_name: Name of the subpolicy
        description: Description of the subpolicy
        control: Control information
        current_date: Current date string
    
    Returns:
        Optimized prompt with examples
    """
    return f"""You are a compliance expert that generates detailed compliance and risk records for policies.

{COMPLIANCE_GENERATION_EXAMPLES}

Based on the following subpolicy information:
- Subpolicy Name: {subpolicy_name}
- Description: {description}
- Control: {control}

Generate 1-2 different compliance records that would be relevant for this subpolicy. Each compliance should cover different aspects or requirements of the subpolicy. Focus on the most critical compliance requirements to reduce processing time.
For each compliance record, also generate associated risk information.

Follow the examples above for structure and format. Ensure all fields are comprehensive and realistic.

Provide the following information in valid JSON format:

{{
    "compliances": [
        {{
            "Identifier": "Unique identifier code for this compliance (e.g., COMP-001)",
            "ComplianceTitle": "Clear, specific title for the compliance requirement",
            "ComplianceItemDescription": "Detailed description of what needs to be complied with",
            "ComplianceType": "One of: Regulatory, Internal, Industry Standard, Legal, Operational",
            "Scope": "Description of what/who this compliance applies to",
            "Objective": "What this compliance aims to achieve",
            "BusinessUnitsCovered": "Which business units this applies to",
            "IsRisk": 1,
            "PossibleDamage": "Description of potential damage if not complied with",
            "mitigation": {{"1": "first mitigation strategy", "2": "second mitigation strategy", "3": "third mitigation strategy"}},
            "Criticality": "One of: Low, Medium, High, Critical",
            "MandatoryOptional": "One of: Mandatory, Optional",
            "ManualAutomatic": "One of: Manual, Automatic, Semi-Automatic",
            "Impact": float between 1.0-10.0 (Risk impact severity),
            "Probability": float between 1.0-10.0 (probability of occurrence),
            "MaturityLevel": "One of: Initial, Developing, Defined, Managed, Optimizing",
            "ActiveInactive": "Active",
            "PermanentTemporary": "Permanent",
            "CreatedByName": "radha.sharma",
            "CreatedByDate": "{current_date}",
            "ComplianceVersion": "1.0",
            "Status": "Approved",
            "Applicability": "One of: Global, Regional, Local, Specific",
            "PotentialRiskScenarios": "Description of potential risk scenarios",
            "RiskType": "One of: Current, Residual, Inherent, Emerging, Accepted",
            "RiskCategory": "One of: Operational, Financial, IT, Legal, Compliance, Strategic, Reputational, Environmental",
            "RiskBusinessImpact": "Description of which business units would be impacted by this risk",
            "risk": {{
                "RiskTitle": "Clear, descriptive title for the associated risk",
                "Criticality": "One of: Low, Medium, High, Critical (should match compliance Criticality)",
                "PossibleDamage": "Description of potential damage (should match compliance PossibleDamage)",
                "Category": "One of: Operational, Financial, IT, Legal, Compliance, Strategic, Reputational, Environmental",
                "RiskType": "One of: Current, Residual, Inherent, Emerging, Accepted",
                "BusinessImpact": "Description of business impact",
                "RiskDescription": "Detailed description of the risk and its potential consequences",
                "RiskLikelihood": integer between 1-10 (likelihood of risk occurrence),
                "RiskImpact": integer between 1-10 (impact severity),
                "RiskExposureRating": float (calculated as RiskImpact * RiskLikelihood),
                "RiskPriority": "One of: Low, Medium, High",
                "RiskMitigation": {{"1": "first mitigation strategy", "2": "second mitigation strategy", "3": "third mitigation strategy"}},
                "CreatedAt": "{current_date}",
                "RiskMultiplierX": 0.1,
                "RiskMultiplierY": 0.1
            }}
        }}
    ]
}}

Ensure the JSON is valid and each compliance record with its associated risk is comprehensive and realistic based on the subpolicy information provided.
Follow the structure and detail level shown in the examples above."""

def get_policy_extraction_prompt(section_title: str, content: str, framework_info: Dict[str, Any]) -> str:
    """
    Get optimized prompt for policy extraction with few-shot examples.
    
    Args:
        section_title: Title of the section
        content: Content to analyze
        framework_info: Framework metadata
    
    Returns:
        Optimized prompt with examples
    """
    return f"""You are an expert policy analyst specializing in {framework_info['framework_name']}. Your task is to analyze content and generate comprehensive policy and subpolicy information with detailed metadata.

FRAMEWORK CONTEXT:
- Framework: {framework_info['framework_name']}
- Version: {framework_info['current_version']}
- Category: {framework_info['category']}
- Description: {framework_info['framework_description']}

{POLICY_EXTRACTION_EXAMPLES}

CRITICAL REQUIREMENTS:
1. Every policy MUST have at least one subpolicy
2. Every subpolicy MUST have a detailed "control" field with WHO, WHAT, WHEN, HOW, WHERE
3. Generate comprehensive metadata for all policies and subpolicies
4. Create structured, implementable policies from the content
5. Extract ACTUAL policies from the content - do NOT return generic templates
6. The response MUST include "has_policies": true and a "policies" array

Section Title: {section_title}

Content to analyze:
{content[:8000]}

IMPORTANT: You MUST extract actual policies from the content above. Do NOT return generic templates or placeholder data.
- If the content describes requirements, controls, or procedures, extract them as policies
- Each policy must have: policy_title, policy_description, policy_text, scope, objective, policy_type, policy_category, policy_subcategory, and subpolicies array
- Each subpolicy must have: subpolicy_title, subpolicy_description, subpolicy_text, and control

Generate comprehensive policies with all required metadata fields. Follow the examples above EXACTLY for structure, detail level, and format.
Ensure all policies have comprehensive metadata including scope, objective, categorization, and structured identifiers.

Return ONLY valid JSON in this EXACT format:
{{
    "has_policies": true,
    "policies": [
        {{
            "policy_title": "...",
            "policy_description": "...",
            "policy_text": "...",
            "scope": "...",
            "objective": "...",
            "policy_type": "...",
            "policy_category": "...",
            "policy_subcategory": "...",
            "subpolicies": [...]
        }}
    ],
    "document_type": "...",
    "confidence": 0.95
}}

If no policies can be extracted, return:
{{
    "has_policies": false,
    "policies": [],
    "document_type": "other",
    "confidence": 0.0
}}"""

