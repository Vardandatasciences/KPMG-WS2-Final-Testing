#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Report Generator V2
Directly tests OpenAI vs Ollama by calling AI functions directly
"""

import os
import sys
import django
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import traceback

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup Django
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

try:
    django.setup()
    print("[OK] Django setup successful")
except Exception as e:
    print(f"[ERROR] Django setup failed: {e}")
    sys.exit(1)

# Import AI functions directly
from grc.routes.Risk.risk_ai_doc import (
    call_ollama_json,
    call_openai_json,
    _select_ollama_model_by_complexity,
    OLLAMA_MODEL_DEFAULT,
    OPENAI_MODEL
)

from grc.routes.Incident.incident_ai_import import (
    parse_incidents_from_text as incident_parse
)

from grc.utils.ai_cache import get_cache_stats, clear_cache_pattern
from grc.utils.rag_system import get_rag_stats, is_rag_available, retrieve_relevant_context, build_rag_prompt
from grc.utils.model_router import get_current_system_load, track_system_load
from grc.utils.document_preprocessor import preprocess_document, calculate_document_hash
from grc.utils.few_shot_prompts import get_risk_extraction_prompt

# For PDF generation
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# For charts
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

TEST_DOCUMENTS = {
    "risk": "risk_register3.pdf",
    "incident": "incident_report_1.pdf",
    "policy": "PCI_DSS_1.pdf"
}

test_results = {}

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF."""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text
    except:
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
            return text
        except Exception as e:
            print(f"[ERROR] Failed to extract text: {e}")
            return ""

def test_risk_with_provider(text: str, provider: str, document_hash: str) -> Dict[str, Any]:
    """Test risk extraction with specific provider by directly calling AI functions."""
    start_time = time.time()
    
    # Build prompt using few-shot template
    prompt = get_risk_extraction_prompt(text[:8000])
    
    # Phase 3: RAG context
    rag_context = None
    if is_rag_available():
        try:
            rag_context = retrieve_relevant_context("Extract all risks from this document", n_results=3)
            if rag_context:
                prompt = build_rag_prompt(prompt, rag_context, None)
        except:
            pass
    
    # Call appropriate provider
    if provider == 'ollama':
        model = _select_ollama_model_by_complexity(len(text))
        result = call_ollama_json(prompt, model=model, document_hash=document_hash)
    else:
        result = call_openai_json(prompt, document_hash=document_hash)
    
    processing_time = time.time() - start_time
    track_system_load(processing_time, len(text))
    
    # Parse result
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except:
            result = {"risks": []}
    
    risks = result.get("risks", []) if isinstance(result, dict) else []
    
    return {
        "provider": provider,
        "processing_time": processing_time,
        "num_risks": len(risks),
        "risks": risks[:3],
        "cache_stats": get_cache_stats(),
        "rag_stats": get_rag_stats() if is_rag_available() else None,
        "system_load": get_current_system_load()
    }

def test_incident_with_provider(text: str, provider: str, document_hash: str) -> Dict[str, Any]:
    """Test incident extraction - uses shared parse function which respects current provider."""
    # For incidents, we need to temporarily set the provider
    # Since incident_ai_import uses risk_ai_doc's provider, we'll use env var
    original_env = os.environ.get('RISK_AI_PROVIDER')
    
    try:
        os.environ['RISK_AI_PROVIDER'] = provider
        # Reload to pick up new provider
        import importlib
        import grc.routes.Incident.incident_ai_import as incident_module
        importlib.reload(incident_module)
        
        start_time = time.time()
        incidents = incident_module.parse_incidents_from_text(text, document_hash=document_hash)
        processing_time = time.time() - start_time
        
        return {
            "provider": provider,
            "processing_time": processing_time,
            "num_incidents": len(incidents) if incidents else 0,
            "incidents": incidents[:3] if incidents else [],
            "cache_stats": get_cache_stats(),
            "rag_stats": get_rag_stats() if is_rag_available() else None,
            "system_load": get_current_system_load()
        }
    finally:
        if original_env:
            os.environ['RISK_AI_PROVIDER'] = original_env
        elif 'RISK_AI_PROVIDER' in os.environ:
            del os.environ['RISK_AI_PROVIDER']

def main():
    """Main execution."""
    print("="*80)
    print("Performance Report Generator V2")
    print("="*80)
    
    # Verify documents
    for doc_type, doc_path in TEST_DOCUMENTS.items():
        if not os.path.exists(doc_path):
            print(f"[ERROR] Document not found: {doc_path}")
            return
    
    output_dir = "performance_report_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Test Risk Document
    print("\n" + "="*80)
    print("TESTING RISK DOCUMENT")
    print("="*80)
    
    risk_text = extract_text_from_pdf(TEST_DOCUMENTS["risk"])
    risk_text, _ = preprocess_document(risk_text, max_length=8000)
    risk_hash = calculate_document_hash(risk_text)
    
    clear_cache_pattern("risk_*")
    print("\n[TEST] OpenAI...")
    test_results["risk"] = {"openai": test_risk_with_provider(risk_text, "openai", risk_hash)}
    
    time.sleep(2)
    clear_cache_pattern("risk_*")
    print("\n[TEST] Ollama...")
    test_results["risk"]["ollama"] = test_risk_with_provider(risk_text, "ollama", risk_hash)
    
    # Test Incident Document
    print("\n" + "="*80)
    print("TESTING INCIDENT DOCUMENT")
    print("="*80)
    
    incident_text = extract_text_from_pdf(TEST_DOCUMENTS["incident"])
    incident_text, _ = preprocess_document(incident_text, max_length=8000)
    incident_hash = calculate_document_hash(incident_text)
    
    clear_cache_pattern("incident_*")
    print("\n[TEST] OpenAI...")
    test_results["incident"] = {"openai": test_incident_with_provider(incident_text, "openai", incident_hash)}
    
    time.sleep(2)
    clear_cache_pattern("incident_*")
    print("\n[TEST] Ollama...")
    test_results["incident"]["ollama"] = test_incident_with_provider(incident_text, "ollama", incident_hash)
    
    # Save results
    results_file = os.path.join(output_dir, "test_results.json")
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"\n[OK] Results saved to: {results_file}")
    
    # Generate summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    for doc_type in ["risk", "incident"]:
        openai_result = test_results.get(doc_type, {}).get("openai", {})
        ollama_result = test_results.get(doc_type, {}).get("ollama", {})
        
        if "error" not in openai_result and "error" not in ollama_result:
            openai_time = openai_result.get("processing_time", 0)
            ollama_time = ollama_result.get("processing_time", 0)
            improvement = ((openai_time - ollama_time) / openai_time * 100) if openai_time > 0 else 0
            
            print(f"\n{doc_type.upper()}:")
            print(f"  OpenAI: {openai_time:.2f}s, Ollama: {ollama_time:.2f}s")
            print(f"  Improvement: {improvement:.1f}%")
    
    print("\n[OK] Test complete! Run generate_performance_report.py for full PDF report.")
    print("="*80)

if __name__ == "__main__":
    main()



