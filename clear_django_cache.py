#!/usr/bin/env python3
"""
Clear Django cache and reload AI configuration
"""

import os
import sys
import django
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables first
env_path = Path(__file__).parent / "grc_backend" / ".env"
load_dotenv(env_path, override=True)

# Add the Django project to the path
project_root = Path(__file__).parent / "grc_backend"
sys.path.insert(0, str(project_root))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def clear_ai_cache():
    """Clear AI configuration cache"""
    try:
        # Clear the LRU cache for AI settings
        from grc.ai.config import get_ai_settings
        get_ai_settings.cache_clear()
        print("Cleared AI settings cache")
        
        # Get fresh settings
        fresh_settings = get_ai_settings()
        print(f"Fresh AI Provider: {fresh_settings.provider}")
        print(f"Fresh OpenAI Model: {fresh_settings.openai_model}")
        print(f"Fresh OpenAI API URL: {fresh_settings.openai_api_url}")
        print(f"Fresh OpenAI API Key: {'Set' if fresh_settings.openai_api_key else 'Missing'}")
        
        return True
        
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return False

def test_fresh_config():
    """Test with fresh configuration"""
    try:
        from grc.ai.service import get_ai_service
        from grc.ai.config import AI_SETTINGS
        
        print(f"\nTesting Fresh Configuration:")
        print(f"   AI_PROVIDER: {AI_SETTINGS.provider}")
        print(f"   OPENAI_MODEL: {AI_SETTINGS.openai_model}")
        print(f"   OPENAI_API_URL: {AI_SETTINGS.openai_api_url}")
        
        # Test model selection
        ai_service = get_ai_service()
        from grc.ai.types import AIRequestOptions
        
        options = AIRequestOptions(
            task_name="risk.analyze_security_incident",
            preferred_provider=None,
            preferred_model=None
        )
        
        decision = ai_service.router.select_model(options, "test prompt")
        print(f"\nModel Selection Result:")
        print(f"   Provider: {decision.provider}")
        print(f"   Model: {decision.model}")
        print(f"   Reason: {decision.reason}")
        
        if decision.provider == "openai" and "meta/llama" in decision.model:
            print("NVIDIA model selection is working!")
            return True
        else:
            print("Still selecting wrong model")
            return False
            
    except Exception as e:
        print(f"Error testing config: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("   Django Cache Clear & NVIDIA Config Test")
    print("=" * 60)
    
    # Clear cache
    cache_cleared = clear_ai_cache()
    
    if cache_cleared:
        # Test fresh config
        config_ok = test_fresh_config()
        
        if config_ok:
            print("\nSUCCESS! NVIDIA configuration is now working correctly.")
            print("\nNext steps:")
            print("   1. Restart your Django server: python manage.py runserver")
            print("   2. Test risk creation in the frontend")
        else:
            print("\nConfiguration still has issues.")
    else:
        print("\nFailed to clear cache.")