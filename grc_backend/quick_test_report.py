#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Test - Verify all components work before running full report
"""

import os
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*80)
print("Quick Test - Verifying Components")
print("="*80)

# Check documents
print("\n1. Checking test documents...")
documents = {
    "risk": "risk_register3.pdf",
    "incident": "incident_report_1.pdf",
    "policy": "PCI_DSS_1.pdf"
}

all_exist = True
for doc_type, doc_path in documents.items():
    if os.path.exists(doc_path):
        size = os.path.getsize(doc_path) / 1024  # KB
        print(f"   [OK] {doc_type.upper()}: {doc_path} ({size:.1f} KB)")
    else:
        print(f"   [ERROR] {doc_type.upper()}: {doc_path} NOT FOUND")
        all_exist = False

if not all_exist:
    print("\n[ERROR] Some documents are missing. Please ensure all test documents exist.")
    sys.exit(1)

# Check Python packages
print("\n2. Checking Python packages...")
packages = {
    "django": "Django",
    "reportlab": "reportlab",
    "matplotlib": "matplotlib",
    "pdfplumber": "pdfplumber",
    "PyPDF2": "PyPDF2"
}

missing = []
for module, package in packages.items():
    try:
        __import__(module)
        print(f"   [OK] {package}")
    except ImportError:
        print(f"   [MISSING] {package} - Install with: pip install {package}")
        missing.append(package)

if missing:
    print(f"\n[WARNING] Missing packages: {', '.join(missing)}")
    print("The report may not generate charts/PDF without these packages.")

# Check Django setup
print("\n3. Testing Django setup...")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    import django
    django.setup()
    print("   [OK] Django setup successful")
    
    # Test imports
    from grc.routes.Risk.risk_ai_doc import AI_PROVIDER, call_ollama_json, call_openai_json
    print(f"   [OK] AI modules imported (Current provider: {AI_PROVIDER})")
    
    from grc.utils.ai_cache import get_cache_stats
    from grc.utils.rag_system import is_rag_available
    from grc.utils.model_router import get_current_system_load
    print("   [OK] Phase 2 & 3 utilities imported")
    
except Exception as e:
    print(f"   [ERROR] Django setup failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check AI providers
print("\n4. Checking AI providers...")
from django.conf import settings

openai_key = getattr(settings, 'OPENAI_API_KEY', None)
if openai_key and openai_key != 'your-openai-api-key-here':
    print("   [OK] OpenAI API key configured")
else:
    print("   [WARNING] OpenAI API key not configured - OpenAI tests will fail")

ollama_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://13.205.15.232:11434')
print(f"   [INFO] Ollama URL: {ollama_url}")

# Check RAG
print("\n5. Checking Phase 3 components...")
if is_rag_available():
    from grc.utils.rag_system import get_rag_stats
    rag_stats = get_rag_stats()
    print(f"   [OK] RAG (ChromaDB) available: {rag_stats}")
else:
    print("   [WARNING] RAG not available - Phase 3 RAG features will be disabled")

cache_stats = get_cache_stats()
print(f"   [OK] Cache system: {cache_stats}")

system_load = get_current_system_load()
print(f"   [OK] System load tracking: {system_load:.2f}")

print("\n" + "="*80)
print("[OK] All checks passed! Ready to run full report.")
print("="*80)
print("\nTo generate the full report, run:")
print("  python generate_performance_report.py")
print("\nThis will:")
print("  1. Test all 3 documents with OpenAI")
print("  2. Test all 3 documents with Ollama (Phase 1, 2, 3 optimized)")
print("  3. Generate comparison charts")
print("  4. Create comprehensive PDF report")
print("  5. Save all results to performance_report_output/")
print("\nNote: This may take 10-30 minutes depending on document sizes.")
print("="*80)


