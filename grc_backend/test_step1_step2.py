"""
Test script for Step 1 (Text Cleaning) and Step 2 (Domain Classification)
Run: python test_step1_step2.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import json
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

from grc.services.similarity_service import SimilarityService
from grc.dataclasses.similarity_dataclasses import SimilarityCheckRequest


def test_framework_step1_step2():
    """Test Step 1 and Step 2 with PCI DSS framework."""
    
    print("\n" + "="*80)
    print("TESTING STEP 1 & STEP 2: PCI DSS FRAMEWORK")
    print("="*80 + "\n")
    
    # Sample framework data (similar to what you provided)
    framework_data = {
        'FrameworkName': 'Payment Card Industry Data Security Standard',
        'FrameworkDescription': '''The Payment Card Industry Data Security Standard (PCI DSS) is an information 
        security standard for organizations that handle branded credit cards from the major card schemes. 
        The PCI Standard is mandated by the card brands and administered by the Payment Card Industry 
        Security Standards Council. The standard was created to increase controls around cardholder data 
        to reduce credit card fraud.''',
        'Category': 'Financial Security and Compliance',
        'Domain': {'DomainName': 'Financial Services'},
        'InternalExternal': 'External',
        'Identifier': 'PCI-DSS-v4.0'
    }
    
    print("INPUT DATA:")
    print(f"  Name: {framework_data['FrameworkName']}")
    print(f"  Category: {framework_data['Category']}")
    print(f"  Type: {framework_data['InternalExternal']}")
    print(f"  Identifier: {framework_data['Identifier']}")
    print(f"  Description length: {len(framework_data['FrameworkDescription'])} chars")
    print()
    
    # Create service and request
    service = SimilarityService()
    request = SimilarityCheckRequest(
        item_type='Framework',
        item_data=framework_data
    )
    
    print("-"*80)
    print("STEP 1: TEXT CLEANING")
    print("-"*80)
    
    # Step 1: Text Cleaning
    try:
        cleaning_result, audit = service.step1_clean_text(request)
        
        print("\n✓ Step 1 Complete!")
        print(f"\nStructured JSON Output:")
        print(json.dumps(cleaning_result.structured_json, indent=2))
        
        print(f"\nEmbedding Text (first 200 chars):")
        print(f"'{cleaning_result.embedding_text[:200]}...'")
        print(f"Total embedding text length: {len(cleaning_result.embedding_text)} chars")
        
        print(f"\nChanges Made: {cleaning_result.changes_made}")
        
    except Exception as e:
        print(f"✗ Step 1 Failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "-"*80)
    print("STEP 2: DOMAIN CLASSIFICATION (NVIDIA/OpenAI)")
    print("-"*80)
    
    # Step 2: Domain Classification
    try:
        classification = service.step2_classify_domain(request, cleaning_result, audit)
        
        print("\n✓ Step 2 Complete!")
        print(f"\nClassification Results:")
        print(f"  Primary Domain: {classification.primary_domain}")
        print(f"  Industry Vertical: {classification.industry_vertical}")
        print(f"  Business Function: {classification.business_function}")
        print(f"  Compliance Area: {classification.compliance_area}")
        print(f"  Control Type: {classification.control_type}")
        print(f"  Risk Category: {classification.risk_category}")
        print(f"  Confidence: {classification.confidence:.2f}")
        print(f"  Method: {classification.classification_method}")
        
        print(f"\nReasoning:")
        print(f"  {classification.reasoning}")
        
        print(f"\nContext Used:")
        print(json.dumps(classification.context_used, indent=2))
        
        if classification.raw_response:
            print(f"\nRaw LLM Response (first 500 chars):")
            print(json.dumps(classification.raw_response, indent=2)[:500])
        
    except Exception as e:
        print(f"✗ Step 2 Failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "-"*80)
    print("AUDIT RECORD SAVED")
    print("-"*80)
    print(f"\nAudit ID: {audit.id}")
    print(f"Check ID in database: {audit.id}")
    print(f"You can query this in MySQL:")
    print(f"  SELECT * FROM similarity_check_audit WHERE id = {audit.id};")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    return audit.id


def test_policy_step1_step2():
    """Test with a Policy example."""
    
    print("\n\n" + "="*80)
    print("TESTING STEP 1 & STEP 2: POLICY UNDER FRAMEWORK")
    print("="*80 + "\n")
    
    # Note: For policy testing, we'd need a framework_id
    # This is a simplified test
    policy_data = {
        'PolicyName': 'Access Control Policy',
        'PolicyDescription': '''This policy defines the requirements for access control to ensure 
        that only authorized personnel can access sensitive cardholder data systems. 
        It covers user authentication, authorization, and accountability.''',
        'PolicyType': 'Security',
        'PolicyCategory': 'Access Control',
        'PolicySubCategory': 'User Authentication',
        'Scope': 'All systems handling payment card data',
        'Objective': 'Protect cardholder data through proper access controls'
    }
    
    print("POLICY INPUT:")
    print(f"  Name: {policy_data['PolicyName']}")
    print(f"  Type: {policy_data['PolicyType']}")
    print(f"  Category: {policy_data['PolicyCategory']}")
    print()
    
    # For actual policy test, we'd need to create a framework first
    # or use an existing framework_id
    print("Note: For Policy/SubPolicy/Compliance tests, parent entities must exist.")
    print("Use Django shell or API to create framework first, then test.")
    
    print("\n" + "="*80)


def check_env_variables():
    """Check if required environment variables are set."""
    
    print("\n" + "="*80)
    print("ENVIRONMENT CHECK")
    print("="*80 + "\n")
    
    nvidia_key = os.environ.get('NVIDIA_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')
    provider = os.environ.get('RISK_AI_PROVIDER', 'nvidia')
    
    print(f"RISK_AI_PROVIDER: {provider}")
    print(f"NVIDIA_API_KEY: {'✓ Set' if nvidia_key else '✗ Not Set'}")
    print(f"OPENAI_API_KEY: {'✓ Set' if openai_key else '✗ Not Set'}")
    
    if not nvidia_key and not openai_key:
        print("\n⚠ WARNING: No API keys configured!")
        print("   Step 2 will use fallback classification.")
        print("\n   To configure:")
        print("   export NVIDIA_API_KEY='your_key_here'")
        print("   or")
        print("   export OPENAI_API_KEY='your_key_here'")
    
    print("\n" + "="*80)


if __name__ == '__main__':
    # Check environment first
    check_env_variables()
    
    # Run tests
    try:
        audit_id = test_framework_step1_step2()
        test_policy_step1_step2()
        
        print("\n\n" + "="*80)
        print("NEXT STEPS")
        print("="*80)
        print(f"\n1. Check database for audit record:")
        print(f"   SELECT * FROM similarity_check_audit WHERE id = {audit_id};\n")
        
        print("2. To test with actual API call:")
        print("   curl -X POST http://localhost:8000/api/similarity-check/ \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{...framework data...}'\n")
        
        print("3. Check Django logs for detailed output.")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
