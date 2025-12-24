"""
Risk AI Document Processing - Comparison Test
Tests both NORMAL (OpenAI) and OPTIMIZED (Ollama) versions
and compares performance, quality, and results.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add Django settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.conf import settings

# Import both versions
from grc.routes.Risk.risk_ai_doc import (
    parse_risks_from_text as parse_risks_normal,
    extract_text_from_file,
    call_openai_json
)
from grc.routes.Risk.risk_ai_doc_optimized import (
    parse_risks_from_text as parse_risks_optimized,
    call_ollama_json
)

# =========================
# CONFIGURATION
# =========================
OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://13.205.15.232:11434').rstrip('/')
OPENAI_API_KEY = getattr(settings, 'OPENAI_API_KEY', '')
OPENAI_MODEL = getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini')

# Test document path (user will provide)
TEST_DOCUMENT_PATH = None
TEST_DOCUMENT_URL = None

# =========================
# UTILITIES
# =========================
def download_file_from_url(url: str, save_path: str) -> bool:
    """Download a file from URL."""
    try:
        print(f"📥 Downloading document from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded {len(response.content)} bytes to {save_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download file: {e}")
        return False

def get_file_extension(file_path: str) -> str:
    """Get file extension."""
    return os.path.splitext(file_path)[1].lower()

def format_time(seconds: float) -> str:
    """Format time in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.1f}s"

def calculate_similarity(risk1: Dict, risk2: Dict) -> float:
    """Calculate similarity score between two risks (0-1)."""
    if not risk1 or not risk2:
        return 0.0
    
    # Compare key fields
    fields_to_compare = [
        'RiskTitle', 'Criticality', 'Category', 'RiskType',
        'RiskPriority', 'RiskLikelihood', 'RiskImpact'
    ]
    
    matches = 0
    total = 0
    
    for field in fields_to_compare:
        val1 = risk1.get(field)
        val2 = risk2.get(field)
        
        if val1 is not None or val2 is not None:
            total += 1
            if val1 == val2:
                matches += 1
            elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # For numeric fields, allow small differences
                if abs(float(val1) - float(val2)) <= 1:
                    matches += 1
    
    return matches / total if total > 0 else 0.0

def compare_risks(normal_risks: List[Dict], optimized_risks: List[Dict]) -> Dict:
    """Compare results from both versions."""
    comparison = {
        'count_match': len(normal_risks) == len(optimized_risks),
        'normal_count': len(normal_risks),
        'optimized_count': len(optimized_risks),
        'similarities': [],
        'average_similarity': 0.0,
        'field_comparisons': {}
    }
    
    # Compare each risk
    min_count = min(len(normal_risks), len(optimized_risks))
    similarities = []
    
    for i in range(min_count):
        sim = calculate_similarity(normal_risks[i], optimized_risks[i])
        similarities.append(sim)
        comparison['similarities'].append({
            'risk_index': i,
            'normal_title': normal_risks[i].get('RiskTitle', 'N/A'),
            'optimized_title': optimized_risks[i].get('RiskTitle', 'N/A'),
            'similarity': sim
        })
    
    if similarities:
        comparison['average_similarity'] = sum(similarities) / len(similarities)
    
    # Field-level comparison
    if normal_risks and optimized_risks:
        all_fields = set()
        for risk in normal_risks + optimized_risks:
            all_fields.update(risk.keys())
        
        for field in all_fields:
            if field.startswith('_'):
                continue
            
            normal_values = [r.get(field) for r in normal_risks if r.get(field) is not None]
            optimized_values = [r.get(field) for r in optimized_risks if r.get(field) is not None]
            
            comparison['field_comparisons'][field] = {
                'normal_filled': len(normal_values),
                'optimized_filled': len(optimized_values),
                'normal_sample': normal_values[:3] if normal_values else [],
                'optimized_sample': optimized_values[:3] if optimized_values else []
            }
    
    return comparison

# =========================
# TEST FUNCTIONS
# =========================
def test_normal_version(text: str) -> Dict[str, Any]:
    """Test the normal (OpenAI) version."""
    print("\n" + "="*80)
    print("🧪 TESTING NORMAL VERSION (OpenAI)")
    print("="*80)
    
    if not OPENAI_API_KEY:
        print("⚠️  WARNING: OPENAI_API_KEY not set. Skipping normal version test.")
        return {
            'success': False,
            'error': 'OPENAI_API_KEY not configured',
            'time_elapsed': 0,
            'risks': []
        }
    
    start_time = time.time()
    
    try:
        print(f"📝 Processing {len(text)} characters of text...")
        print(f"🤖 Using OpenAI model: {OPENAI_MODEL}")
        
        risks = parse_risks_normal(text)
        
        elapsed = time.time() - start_time
        
        print(f"✅ Normal version completed in {format_time(elapsed)}")
        print(f"📊 Extracted {len(risks)} risk(s)")
        
        return {
            'success': True,
            'time_elapsed': elapsed,
            'risks': risks,
            'model_used': OPENAI_MODEL,
            'text_length': len(text)
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Normal version failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'error': str(e),
            'time_elapsed': elapsed,
            'risks': []
        }

def test_optimized_version(text: str) -> Dict[str, Any]:
    """Test the optimized (Ollama) version."""
    print("\n" + "="*80)
    print("🚀 TESTING OPTIMIZED VERSION (Ollama)")
    print("="*80)
    
    start_time = time.time()
    
    try:
        print(f"📝 Processing {len(text)} characters of text...")
        print(f"🤖 Using Ollama server: {OLLAMA_BASE_URL}")
        
        risks = parse_risks_optimized(text)
        
        elapsed = time.time() - start_time
        
        print(f"✅ Optimized version completed in {format_time(elapsed)}")
        print(f"📊 Extracted {len(risks)} risk(s)")
        
        return {
            'success': True,
            'time_elapsed': elapsed,
            'risks': risks,
            'model_used': 'Ollama (auto-selected)',
            'text_length': len(text)
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Optimized version failed: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'error': str(e),
            'time_elapsed': elapsed,
            'risks': []
        }

def check_connections() -> Dict[str, bool]:
    """Check connections to both services."""
    print("\n" + "="*80)
    print("🔌 CHECKING CONNECTIONS")
    print("="*80)
    
    results = {
        'openai': False,
        'ollama': False
    }
    
    # Check OpenAI
    if OPENAI_API_KEY:
        try:
            print("🔍 Testing OpenAI connection...")
            test_result = call_openai_json('Return JSON: {"test": true}', timeout=10)
            if test_result:
                results['openai'] = True
                print("✅ OpenAI connection: OK")
            else:
                print("⚠️  OpenAI connection: Failed (no response)")
        except Exception as e:
            print(f"❌ OpenAI connection: Failed - {e}")
    else:
        print("⚠️  OpenAI: API key not configured")
    
    # Check Ollama
    try:
        print("🔍 Testing Ollama connection...")
        url = f"{OLLAMA_BASE_URL}/api/tags"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        models = response.json().get('models', [])
        results['ollama'] = True
        print(f"✅ Ollama connection: OK ({len(models)} models available)")
        print(f"   Available models: {', '.join([m.get('name', 'unknown') for m in models[:5]])}")
    except Exception as e:
        print(f"❌ Ollama connection: Failed - {e}")
    
    return results

# =========================
# MAIN TEST RUNNER
# =========================
def run_comparison_test(document_path: str = None, document_url: str = None) -> Dict[str, Any]:
    """Run the complete comparison test."""
    print("\n" + "="*80)
    print("📊 RISK AI DOCUMENT PROCESSING - COMPARISON TEST")
    print("="*80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check connections
    connections = check_connections()
    
    if not connections['ollama']:
        print("\n❌ ERROR: Cannot connect to Ollama server. Please check configuration.")
        return {'error': 'Ollama connection failed'}
    
    # Step 2: Get document
    if document_url:
        # Download from URL
        temp_file = f"/tmp/test_document_{int(time.time())}.pdf"
        if not download_file_from_url(document_url, temp_file):
            return {'error': 'Failed to download document'}
        document_path = temp_file
    
    if not document_path or not os.path.exists(document_path):
        print("\n❌ ERROR: Document path not provided or file does not exist")
        print("   Usage: python test_risk_ai_comparison.py <document_path>")
        print("   Or: python test_risk_ai_comparison.py --url <document_url>")
        return {'error': 'Document not found'}
    
    print(f"\n📄 Processing document: {document_path}")
    
    # Step 3: Extract text
    print("\n" + "="*80)
    print("📖 EXTRACTING TEXT FROM DOCUMENT")
    print("="*80)
    
    ext = get_file_extension(document_path)
    text = extract_text_from_file(document_path, ext)
    
    if not text or len(text.strip()) < 50:
        print(f"❌ ERROR: Could not extract meaningful text. Length: {len(text) if text else 0}")
        return {'error': 'Text extraction failed'}
    
    print(f"✅ Extracted {len(text)} characters from document")
    print(f"📝 First 200 chars: {text[:200]}...")
    
    # Step 4: Run tests
    normal_result = test_normal_version(text) if connections.get('openai') else None
    optimized_result = test_optimized_version(text)
    
    # Step 5: Compare results
    print("\n" + "="*80)
    print("📊 COMPARISON RESULTS")
    print("="*80)
    
    comparison = {
        'timestamp': datetime.now().isoformat(),
        'document_path': document_path,
        'document_length': len(text),
        'connections': connections,
        'normal_result': normal_result,
        'optimized_result': optimized_result,
        'performance_comparison': {},
        'quality_comparison': {}
    }
    
    # Performance comparison
    if normal_result and normal_result.get('success') and optimized_result.get('success'):
        normal_time = normal_result['time_elapsed']
        optimized_time = optimized_result['time_elapsed']
        speedup = normal_time / optimized_time if optimized_time > 0 else 0
        time_saved = normal_time - optimized_time
        
        comparison['performance_comparison'] = {
            'normal_time': normal_time,
            'optimized_time': optimized_time,
            'speedup': f"{speedup:.2f}x",
            'time_saved': time_saved,
            'time_saved_percent': f"{(time_saved/normal_time*100):.1f}%" if normal_time > 0 else "0%"
        }
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"   Normal (OpenAI):    {format_time(normal_time)}")
        print(f"   Optimized (Ollama): {format_time(optimized_time)}")
        print(f"   Speedup:            {speedup:.2f}x faster")
        print(f"   Time saved:         {format_time(time_saved)} ({(time_saved/normal_time*100):.1f}%)")
    
    # Quality comparison
    if normal_result and normal_result.get('success') and optimized_result.get('success'):
        normal_risks = normal_result.get('risks', [])
        optimized_risks = optimized_result.get('risks', [])
        
        quality_comp = compare_risks(normal_risks, optimized_risks)
        comparison['quality_comparison'] = quality_comp
        
        print(f"\n📊 QUALITY:")
        print(f"   Normal risks found:    {len(normal_risks)}")
        print(f"   Optimized risks found:  {len(optimized_risks)}")
        print(f"   Count match:           {'✅ Yes' if quality_comp['count_match'] else '❌ No'}")
        print(f"   Average similarity:    {quality_comp['average_similarity']:.2%}")
        
        if quality_comp['similarities']:
            print(f"\n   Risk-by-risk similarity:")
            for sim_data in quality_comp['similarities'][:5]:  # Show first 5
                print(f"      Risk {sim_data['risk_index']+1}: {sim_data['similarity']:.2%}")
                print(f"         Normal:    {sim_data['normal_title'][:50]}")
                print(f"         Optimized: {sim_data['optimized_title'][:50]}")
    
    # Summary
    print("\n" + "="*80)
    print("📋 SUMMARY")
    print("="*80)
    
    if optimized_result.get('success'):
        print(f"✅ Optimized version: SUCCESS")
        if comparison.get('performance_comparison'):
            print(f"   ⚡ {comparison['performance_comparison']['speedup']} faster")
    else:
        print(f"❌ Optimized version: FAILED - {optimized_result.get('error', 'Unknown error')}")
    
    if normal_result and normal_result.get('success'):
        print(f"✅ Normal version: SUCCESS")
    elif normal_result:
        print(f"❌ Normal version: FAILED - {normal_result.get('error', 'Unknown error')}")
    else:
        print(f"⚠️  Normal version: SKIPPED (OpenAI not configured)")
    
    # Save results
    results_file = f"risk_ai_comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(comparison, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return comparison

# =========================
# CLI INTERFACE
# =========================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare Normal vs Optimized Risk AI Processing')
    parser.add_argument('document', nargs='?', help='Path to document file (PDF/DOCX/TXT)')
    parser.add_argument('--url', help='URL to download document from')
    parser.add_argument('--output', help='Output file for results JSON')
    
    args = parser.parse_args()
    
    document_path = args.document
    document_url = args.url
    
    if not document_path and not document_url:
        print("❌ ERROR: Please provide either a document path or URL")
        print("\nUsage:")
        print("  python test_risk_ai_comparison.py <document_path>")
        print("  python test_risk_ai_comparison.py --url <document_url>")
        sys.exit(1)
    
    results = run_comparison_test(document_path=document_path, document_url=document_url)
    
    if 'error' in results:
        print(f"\n❌ Test failed: {results['error']}")
        sys.exit(1)
    else:
        print("\n✅ Comparison test completed successfully!")
        sys.exit(0)


