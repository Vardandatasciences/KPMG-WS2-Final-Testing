#!/usr/bin/env python
"""
Comprehensive Test: All Entity Types - Correct vs Misleading Categories
Tests Framework, Policy, SubPolicy, Compliance with:
- Correct categories (AI should match)
- Misleading categories (AI should analyze content, not copy category)
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from grc.dataclasses.similarity_dataclasses import SimilarityCheckRequest
from grc.services.similarity_service import SimilarityService

def test_framework_correct():
    """Test 1: Framework with CORRECT category"""
    print("\n" + "=" * 80)
    print("TEST 1: FRAMEWORK - CORRECT CATEGORY")
    print("=" * 80)
    print("Input: PCI DSS framework with category 'Financial Security'")
    print("Expected: AI should identify 'Financial Services' domain")
    print("-" * 80)
    
    framework_data = {
        "FrameworkName": "Payment Card Industry Data Security Standard",
        "FrameworkDescription": "Security standard for organizations handling credit cards to reduce fraud.",
        "Category": "Financial Security",
        "Type": "External",
        "Identifier": "PCI-DSS-v4.0"
    }
    
    request = SimilarityCheckRequest(
        item_type='Framework',
        item_data=framework_data,
        tenant_id=None,
        user_id=None
    )
    
    service = SimilarityService()
    cleaning_result, audit = service.step1_clean_text(request)
    
    try:
        result = service.step2_classify_domain(request, cleaning_result, audit)
        print(f"✓ Primary Domain: {result.primary_domain}")
        print(f"✓ Industry Vertical: {result.industry_vertical}")
        print(f"✓ Compliance Standards: {result.compliance_standards}")
        print(f"✓ Confidence: {result.confidence}")
        print(f"✓ Reasoning: {result.reasoning[:100]}...")
        
        if 'financial' in result.primary_domain.lower():
            print("✓ PASS: AI correctly identified FINANCIAL domain")
        else:
            print(f"✗ FAIL: AI said '{result.primary_domain}' instead of Financial")
            
    except Exception as e:
        print(f"✗ Error: {e}")

def test_framework_misleading():
    """Test 2: Framework with MISLEADING category"""
    print("\n" + "=" * 80)
    print("TEST 2: FRAMEWORK - MISLEADING CATEGORY")
    print("=" * 80)
    print("Input: Food Safety framework but category is 'Banking' (WRONG!)")
    print("Expected: AI should detect FOOD domain, ignore 'Banking'")
    print("-" * 80)
    
    framework_data = {
        "FrameworkName": "Food Safety and Standards Act",
        "FrameworkDescription": "Regulations for food processing, hygiene standards, quality control in food manufacturing and distribution.",
        "Category": "Banking",  # DELIBERATELY WRONG!
        "Type": "External",
        "Identifier": "FSSAI-2024"
    }
    
    request = SimilarityCheckRequest(
        item_type='Framework',
        item_data=framework_data,
        tenant_id=None,
        user_id=None
    )
    
    service = SimilarityService()
    cleaning_result, audit = service.step1_clean_text(request)
    
    try:
        result = service.step2_classify_domain(request, cleaning_result, audit)
        print(f"✓ Primary Domain: {result.primary_domain}")
        print(f"✓ Industry Vertical: {result.industry_vertical}")
        print(f"✓ Compliance Standards: {result.compliance_standards}")
        print(f"✓ Confidence: {result.confidence}")
        print(f"✓ Reasoning: {result.reasoning[:100]}...")
        
        if 'food' in result.primary_domain.lower() or 'food' in result.industry_vertical.lower():
            print("✓ PASS: AI correctly identified FOOD domain despite 'Banking' category!")
        elif 'bank' in result.primary_domain.lower():
            print("✗ FAIL: AI was fooled by wrong 'Banking' category")
        else:
            print(f"? UNEXPECTED: {result.primary_domain}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

def test_policy_correct():
    """Test 3: Policy under Framework with correct parent context"""
    print("\n" + "=" * 80)
    print("TEST 3: POLICY - CORRECT PARENT CONTEXT")
    print("=" * 80)
    print("Input: Access Control Policy under PCI DSS (Financial)")
    print("Expected: AI should identify as Financial/Security domain")
    print("-" * 80)
    
    # First create framework context
    framework_context = {
        "domain": "Financial Services",
        "industry_vertical": "Payment Card Industry",
        "name": "PCI DSS Framework"
    }
    
    policy_data = {
        "PolicyName": "Access Control Policy",
        "PolicyDescription": "Controls for user authentication and authorization in payment processing systems.",
        "PolicyType": "Security",
        "PolicyCategory": "Access Management",
        "PolicySubCategory": "User Authentication",
        "Scope": "All payment card handling systems",
        "Objective": "Ensure only authorized users access cardholder data"
    }
    
    request = SimilarityCheckRequest(
        item_type='Policy',
        item_data=policy_data,
        tenant_id=None,
        user_id=None
    )
    request.framework_context = framework_context
    
    service = SimilarityService()
    cleaning_result, audit = service.step1_clean_text(request)
    
    try:
        result = service.step2_classify_domain(request, cleaning_result, audit)
        print(f"✓ Primary Domain: {result.primary_domain}")
        print(f"✓ Business Function: {result.business_function}")
        print(f"✓ Confidence: {result.confidence}")
        print(f"✓ Reasoning: {result.reasoning[:100]}...")
        
        if 'financial' in result.primary_domain.lower() or 'security' in result.business_function.lower():
            print("✓ PASS: Policy classified within Financial/Security context")
        else:
            print(f"? Result: {result.primary_domain}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

def test_policy_misleading():
    """Test 4: Policy with misleading parent context"""
    print("\n" + "=" * 80)
    print("TEST 4: POLICY - MISLEADING CONTEXT TEST")
    print("=" * 80)
    print("Input: Healthcare Data Policy but parent marked as 'Manufacturing'")
    print("Expected: AI should detect Healthcare, not Manufacturing")
    print("-" * 80)
    
    # Misleading parent context
    framework_context = {
        "domain": "Manufacturing",  # WRONG!
        "industry_vertical": "Automotive",  # WRONG!
        "name": "Auto Manufacturing Framework"
    }
    
    policy_data = {
        "PolicyName": "Patient Data Privacy Policy",
        "PolicyDescription": "HIPAA compliance policy for protecting electronic health records and patient personal information in healthcare facilities.",
        "PolicyType": "Privacy",
        "PolicyCategory": "Data Protection",
        "PolicySubCategory": "Health Records",
        "Scope": "All healthcare providers and medical staff",
        "Objective": "Ensure patient data privacy and HIPAA compliance"
    }
    
    request = SimilarityCheckRequest(
        item_type='Policy',
        item_data=policy_data,
        tenant_id=None,
        user_id=None
    )
    request.framework_context = framework_context
    
    service = SimilarityService()
    cleaning_result, audit = service.step1_clean_text(request)
    
    try:
        result = service.step2_classify_domain(request, cleaning_result, audit)
        print(f"✓ Primary Domain: {result.primary_domain}")
        print(f"✓ Business Function: {result.business_function}")
        print(f"✓ Compliance Area: {result.compliance_area}")
        print(f"✓ Confidence: {result.confidence}")
        print(f"✓ Reasoning: {result.reasoning[:100]}...")
        
        if 'health' in result.primary_domain.lower() or 'healthcare' in result.business_function.lower():
            print("✓ PASS: AI detected Healthcare despite wrong 'Manufacturing' context!")
        elif 'manufacturing' in result.primary_domain.lower():
            print("✗ FAIL: AI blindly followed wrong parent context")
        else:
            print(f"? Result: {result.primary_domain}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

def test_subpolicy_hierarchical():
    """Test 5: SubPolicy with full hierarchical context"""
    print("\n" + "=" * 80)
    print("TEST 5: SUBPOLICY - FULL HIERARCHICAL CONTEXT")
    print("=" * 80)
    print("Input: Password Policy under Access Control under PCI DSS")
    print("Expected: AI should classify as Financial/Security/Authentication")
    print("-" * 80)
    
    framework_context = {
        "domain": "Financial Services",
        "industry_vertical": "Payment Card Industry",
        "name": "PCI DSS Framework"
    }
    
    policy_context = {
        "primary_domain": "Financial Services",
        "business_function": "Access Management",
        "compliance_area": "PCI-DSS",
        "name": "Access Control Policy"
    }
    
    subpolicy_data = {
        "SubPolicyName": "Password Complexity Requirements",
        "Description": "Minimum password length, complexity rules, and rotation requirements for all payment system users.",
        "Control": "Strong authentication controls per PCI-DSS Requirement 8"
    }
    
    request = SimilarityCheckRequest(
        item_type='SubPolicy',
        item_data=subpolicy_data,
        tenant_id=None,
        user_id=None
    )
    request.framework_context = framework_context
    request.policy_context = policy_context
    
    service = SimilarityService()
    cleaning_result, audit = service.step1_clean_text(request)
    
    try:
        result = service.step2_classify_domain(request, cleaning_result, audit)
        print(f"✓ Primary Domain: {result.primary_domain}")
        print(f"✓ Business Function: {result.business_function}")
        print(f"✓ Control Type: {result.control_type}")
        print(f"✓ Confidence: {result.confidence}")
        
        if 'financial' in result.primary_domain.lower() or 'security' in str(result.control_type).lower():
            print("✓ PASS: SubPolicy correctly classified within hierarchy")
        else:
            print(f"? Result: {result.primary_domain}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

def test_compliance_deep_hierarchy():
    """Test 6: Compliance with deepest hierarchical context"""
    print("\n" + "=" * 80)
    print("TEST 6: COMPLIANCE - DEEPEST HIERARCHICAL CONTEXT")
    print("=" * 80)
    print("Input: Encryption Control under Password Policy under Access Control")
    print("Expected: AI should understand Financial/Security/Encryption context")
    print("-" * 80)
    
    framework_context = {
        "domain": "Financial Services",
        "industry_vertical": "Banking",
        "name": "Banking Security Framework"
    }
    
    policy_context = {
        "primary_domain": "Financial Services",
        "business_function": "Data Protection",
        "compliance_area": "Encryption Standards",
        "name": "Data Encryption Policy"
    }
    
    subpolicy_context = {
        "primary_domain": "Financial Services",
        "business_function": "Cryptographic Controls",
        "control_type": "Technical Control",
        "name": "Encryption Key Management"
    }
    
    compliance_data = {
        "ComplianceTitle": "AES-256 Encryption for Data at Rest",
        "ComplianceItemDescription": "All stored customer financial data must be encrypted using AES-256 algorithm with proper key rotation every 90 days.",
        "ComplianceType": "Technical",
        "Criticality": "High",
        "RiskCategory": "Data Breach Prevention"
    }
    
    request = SimilarityCheckRequest(
        item_type='Compliance',
        item_data=compliance_data,
        tenant_id=None,
        user_id=None
    )
    request.framework_context = framework_context
    request.policy_context = policy_context
    request.subpolicy_context = subpolicy_context
    
    service = SimilarityService()
    cleaning_result, audit = service.step1_clean_text(request)
    
    try:
        result = service.step2_classify_domain(request, cleaning_result, audit)
        print(f"✓ Primary Domain: {result.primary_domain}")
        print(f"✓ Business Function: {result.business_function}")
        print(f"✓ Compliance Area: {result.compliance_area}")
        print(f"✓ Risk Category: {result.risk_category}")
        print(f"✓ Confidence: {result.confidence}")
        
        if 'financial' in result.primary_domain.lower() or 'encryption' in str(result.compliance_area).lower():
            print("✓ PASS: Compliance correctly classified with deep hierarchy")
        else:
            print(f"? Result: {result.primary_domain}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("COMPREHENSIVE ENTITY CLASSIFICATION TEST SUITE")
    print("Testing: Correct vs Misleading Categories")
    print("=" * 80)
    
    # Run all tests
    test_framework_correct()
    test_framework_misleading()
    test_policy_correct()
    test_policy_misleading()
    test_subpolicy_hierarchical()
    test_compliance_deep_hierarchy()
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
    print("\nSummary:")
    print("- Framework: 2 tests (correct vs misleading)")
    print("- Policy: 2 tests (correct vs misleading)")
    print("- SubPolicy: 1 test (hierarchical context)")
    print("- Compliance: 1 test (deep hierarchy)")
    print("\nAI should analyze CONTENT, not blindly copy CATEGORY!")
    print("=" * 80)
