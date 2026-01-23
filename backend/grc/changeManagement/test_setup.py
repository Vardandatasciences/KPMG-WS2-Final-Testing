#!/usr/bin/env python3
"""
Setup Validation Script

This script checks if all requirements are met before running the AI analysis pipeline.
Run this before processing your first PDF to ensure everything is configured correctly.
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8+"""
    print("Checking Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (need 3.8+)")
        return False


def check_dependencies():
    """Check if all required packages are installed"""
    print("\nChecking dependencies...")
    
    required_packages = {
        'django': 'Django',
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'dotenv': 'python-dotenv',
        'langchain_openai': 'langchain-openai',
        'fitz': 'PyMuPDF',
        'pdfminer': 'pdfminer.six',
        'openai': 'openai'
    }
    
    missing = []
    installed = []
    
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
            installed.append(package)
        except ImportError:
            print(f"  ✗ {package}")
            missing.append(package)
    
    return len(missing) == 0, missing


def check_django_setup():
    """Check if Django is properly configured"""
    print("\nChecking Django setup...", end=" ")
    
    try:
        # Add backend to path
        backend_path = Path(__file__).parent.parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
        
        import django
        django.setup()
        
        from django.conf import settings
        print("✓ Django configured")
        return True, settings
    except Exception as e:
        print(f"✗ Error: {e}")
        return False, None


def check_openai_key(settings):
    """Check if OpenAI API key is configured"""
    print("\nChecking OpenAI API key...", end=" ")
    
    try:
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if api_key and len(api_key) > 20:
            masked_key = api_key[:8] + "..." + api_key[-4:]
            print(f"✓ Key found: {masked_key}")
            return True
        else:
            print("✗ Not configured")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def check_modules():
    """Check if the pipeline modules are accessible"""
    print("\nChecking pipeline modules...")
    
    modules_dir = Path(__file__).parent.parent / "backend" / "grc" / "routes" / "uploadNist"
    
    required_modules = [
        'pdf_index_extractor.py',
        'index_content_extractor.py',
        'policy_extractor_enhanced.py',
        'compliance_generator.py'
    ]
    
    all_present = True
    for module in required_modules:
        module_path = modules_dir / module
        if module_path.exists():
            print(f"  ✓ {module}")
        else:
            print(f"  ✗ {module} (not found at {module_path})")
            all_present = False
    
    return all_present


def check_data_folder():
    """Check if data folder exists and has PDFs"""
    print("\nChecking data folder...", end=" ")
    
    data_dir = Path(__file__).parent / "data"
    
    if not data_dir.exists():
        print("✗ data/ folder not found")
        print("  Creating data/ folder...")
        data_dir.mkdir(parents=True, exist_ok=True)
        print("  ✓ Created")
        return False
    
    # Check for PDF files
    pdf_files = list(data_dir.glob("*.pdf"))
    if pdf_files:
        print(f"✓ Found {len(pdf_files)} PDF file(s)")
        for pdf in pdf_files:
            print(f"    - {pdf.name}")
        return True
    else:
        print("⚠ No PDF files found")
        print("  Place your PDF files in the data/ folder")
        return False


def check_output_folder():
    """Check if output folder exists"""
    print("\nChecking output folder...", end=" ")
    
    output_dir = Path(__file__).parent / "output"
    
    if not output_dir.exists():
        print("✗ output/ folder not found")
        print("  Creating output/ folder...")
        output_dir.mkdir(parents=True, exist_ok=True)
        print("  ✓ Created")
    else:
        print("✓ Exists")
    
    return True


def test_openai_connection(settings):
    """Test OpenAI API connection"""
    print("\nTesting OpenAI API connection...", end=" ")
    
    try:
        from openai import OpenAI
        
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            print("✗ No API key")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Simple test
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        
        print("✓ Connection successful")
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)[:50]}")
        return False


def main():
    """Run all checks"""
    print("=" * 80)
    print("AI Analysis Pipeline - Setup Validation")
    print("=" * 80)
    
    checks = []
    
    # Check Python version
    checks.append(("Python Version", check_python_version()))
    
    # Check dependencies
    deps_ok, missing = check_dependencies()
    checks.append(("Dependencies", deps_ok))
    
    if not deps_ok:
        print("\n⚠ Missing packages. Install with:")
        print(f"  pip install {' '.join(missing)}")
    
    # Check Django setup
    django_ok, settings = check_django_setup()
    checks.append(("Django Setup", django_ok))
    
    # Check OpenAI key
    if django_ok and settings:
        key_ok = check_openai_key(settings)
        checks.append(("OpenAI API Key", key_ok))
        
        if key_ok:
            # Test connection
            conn_ok = test_openai_connection(settings)
            checks.append(("OpenAI Connection", conn_ok))
    else:
        checks.append(("OpenAI API Key", False))
        checks.append(("OpenAI Connection", False))
    
    # Check modules
    modules_ok = check_modules()
    checks.append(("Pipeline Modules", modules_ok))
    
    # Check folders
    data_ok = check_data_folder()
    checks.append(("Data Folder", data_ok))
    
    output_ok = check_output_folder()
    checks.append(("Output Folder", output_ok))
    
    # Summary
    print("\n" + "=" * 80)
    print("Validation Summary")
    print("=" * 80)
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for check_name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {check_name}")
    
    print(f"\nResults: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✓ All checks passed! You're ready to run the pipeline.")
        print("\nRun the pipeline with:")
        print("  python ai_analysis.py --pdf-path data/your_file.pdf")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above before running the pipeline.")
        print("\nCommon fixes:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Set OpenAI API key in Django settings or .env file")
        print("3. Place PDF files in the data/ folder")
        return 1


if __name__ == "__main__":
    exit(main())

