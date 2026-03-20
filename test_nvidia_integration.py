#!/usr/bin/env python3
"""
Test NVIDIA Integration in GRC System
Verifies that the AI configuration properly uses NVIDIA models
"""

import os
import sys
import django
from pathlib import Path

# Load environment variables first
from dotenv import load_dotenv
env_path = Path(__file__).parent / "grc_backend" / ".env"
load_dotenv(env_path, override=True)

# Add the Django project to the path
project_root = Path(__file__).parent / "grc_backend"
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def test_ai_configuration():
    """Test that AI configuration properly recognizes NVIDIA"""
    try:
        from grc.ai.config import get_ai_settings, AI_SETTINGS
        
        print("Testing AI Configuration...")
        print(f"   Provider: {AI_SETTINGS.provider}")
        print(f"   OpenAI API Key: {'Set' if AI_SETTINGS.openai_api_key else 'Missing'}")
        print(f"   OpenAI Model: {AI_SETTINGS.openai_model}")
        print(f"   OpenAI API URL: {AI_SETTINGS.openai_api_url}")
        
        # Verify NVIDIA configuration
        if AI_SETTINGS.provider == "openai" and "nvidia.com" in AI_SETTINGS.openai_api_url:
            print("NVIDIA configuration detected correctly!")
            return True
        else:
            print("NVIDIA configuration not detected")
            return False
            
    except Exception as e:
        print(f"Error testing AI configuration: {e}")
        return False

def test_nvidia_api_call():
    """Test a simple API call to NVIDIA"""
    try:
        from grc.ai.service import get_ai_service
        
        print("\nTesting NVIDIA API Call...")
        
        ai_service = get_ai_service()
        
        print("   Sending test prompt to NVIDIA model...")
        
        # Use the risk analysis task
        response = ai_service.run_task(
            "risk.analyze_security_incident",
            payload={
                "incident_description": "Database server experienced unauthorized access attempt from external IP address. Login attempts failed but caused temporary service disruption.",
                "rag_context": ""
            }
        )
        
        print("NVIDIA API call successful!")
        print(f"   Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
        
        if isinstance(response, dict) and 'criticality' in response:
            print(f"   Criticality: {response.get('criticality')}")
            print(f"   Risk Likelihood: {response.get('riskLikelihood')}")
            print(f"   Risk Impact: {response.get('riskImpact')}")
        
        return True
        
    except Exception as e:
        print(f"Error testing NVIDIA API: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("   NVIDIA Integration Test for GRC System")
    print("=" * 60)
    
    # Test 1: Configuration
    config_ok = test_ai_configuration()
    
    if not config_ok:
        print("\nConfiguration test failed. Check your .env file.")
        return False
    
    # Test 2: API Call
    api_ok = test_nvidia_api_call()
    
    if api_ok:
        print("\nAll tests passed! NVIDIA integration is working correctly.")
        print("\nNext steps:")
        print("   1. Test risk creation in the frontend")
        print("   2. Verify AI suggestions appear with robot badges")
        print("   3. Check that justifications are populated")
        return True
    else:
        print("\nAPI test failed. Check your NVIDIA API key and network connection.")
        return False

if __name__ == "__main__":
    main()