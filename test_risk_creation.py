#!/usr/bin/env python3
"""
Test Risk Creation with NVIDIA AI
Tests the actual endpoint that the frontend uses
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / "grc_backend" / ".env"
load_dotenv(env_path, override=True)

def test_risk_analysis_endpoint():
    """Test the /analyze-incident/ endpoint that the frontend uses"""
    
    # Assuming Django server is running on localhost:8000
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/analyze-incident/"
    
    # Test data - same as what the frontend would send
    test_data = {
        "title": "Database Security Breach",
        "description": "Unauthorized access attempt detected on production database server. Multiple failed login attempts from external IP address. System automatically blocked the IP but service was temporarily disrupted."
    }
    
    print("Testing Risk Analysis Endpoint...")
    print(f"URL: {endpoint}")
    print(f"Data: {test_data}")
    
    try:
        # Make request to Django endpoint
        response = requests.post(
            endpoint,
            json=test_data,
            headers={
                "Content-Type": "application/json",
                # Add any authentication headers if needed
            },
            timeout=60  # Give it time for AI processing
        )
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS! AI Analysis Response:")
            print(json.dumps(result, indent=2))
            
            # Check if we got the expected fields
            expected_fields = ['criticality', 'riskLikelihood', 'riskImpact', 'possibleDamage']
            missing_fields = [field for field in expected_fields if field not in result]
            
            if missing_fields:
                print(f"WARNING: Missing expected fields: {missing_fields}")
            else:
                print("All expected fields present!")
                
            return True
        else:
            print(f"ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to Django server.")
        print("Make sure the Django development server is running:")
        print("  cd grc_backend && python manage.py runserver")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def check_django_server():
    """Check if Django server is running"""
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        return True
    except:
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("   Risk Creation with NVIDIA AI Test")
    print("=" * 60)
    
    # Check if Django server is running
    if not check_django_server():
        print("Django server is not running.")
        print("Please start it with: cd grc_backend && python manage.py runserver")
        exit(1)
    
    success = test_risk_analysis_endpoint()
    
    if success:
        print("\nSUCCESS! NVIDIA AI integration is working in risk creation!")
        print("\nNext steps:")
        print("1. Test in the frontend UI")
        print("2. Create a risk using AI mode")
        print("3. Verify AI badges and justifications appear")
    else:
        print("\nTest failed. Check the Django server logs for more details.")