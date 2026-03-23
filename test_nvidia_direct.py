#!/usr/bin/env python3
"""
Direct test of NVIDIA API using OpenAI format
"""

import requests
import json
import os
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
env_path = Path(__file__).parent / "grc_backend" / ".env"
load_dotenv(env_path, override=True)

def test_nvidia_direct():
    """Test NVIDIA API directly using requests"""
    
    api_key = os.getenv("NVIDIA_API_KEY")
    api_url = os.getenv("OPENAI_API_URL", "https://integrate.api.nvidia.com/v1/chat/completions")
    model = os.getenv("OPENAI_MODEL", "meta/llama-3.1-70b-instruct")
    
    print(f"Testing NVIDIA API directly...")
    print(f"API URL: {api_url}")
    print(f"Model: {model}")
    print(f"API Key: {'Set' if api_key else 'Missing'}")
    
    if not api_key:
        print("ERROR: NVIDIA_API_KEY not found in environment")
        return False
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Analyze this security incident: Database server experienced unauthorized access attempt. Return a JSON with criticality (High/Medium/Low) and risk level (1-10)."},
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        print("Sending request to NVIDIA...")
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print("SUCCESS! NVIDIA API response:")
            print(content)
            return True
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_nvidia_direct()
    if success:
        print("\nNVIDIA API is working correctly!")
    else:
        print("\nNVIDIA API test failed.")