#!/usr/bin/env python
"""
Test AI Analysis for a Specific PDF
This script tests the improved AI prompt on a PDF file
"""

import os
import sys
import json
from pathlib import Path

# Add Django project to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django
django.setup()

from grc.changeManagement.changemanagement import (
    get_change_management_service,
    process_specific_file
)


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")


def test_ai_analysis_on_pdf(pdf_filename):
    """Test AI analysis on a specific PDF"""
    print_header(f"Testing AI Analysis on: {pdf_filename}")
    
    service = get_change_management_service()
    pdf_path = service.data_dir / pdf_filename
    
    if not pdf_path.exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        print(f"📁 Available PDFs in data directory:")
        pdf_files = list(service.data_dir.glob("*.pdf")) + list(service.data_dir.glob("*.PDF"))
        for pdf_file in pdf_files:
            print(f"   - {pdf_file.name}")
        return None
    
    print(f"✅ Found PDF: {pdf_path}")
    print(f"📊 File size: {pdf_path.stat().st_size / (1024*1024):.2f} MB")
    
    # Test text extraction
    print_header("Step 1: Text Extraction")
    snippet = service._extract_pdf_text_snippet(pdf_path)
    if snippet:
        print(f"✅ Extracted {len(snippet)} characters")
        print(f"📝 Preview (first 500 chars):")
        print(f"   {snippet[:500]}...")
    else:
        print(f"❌ Failed to extract text from PDF")
        return None
    
    # Test AI analysis
    print_header("Step 2: AI Analysis")
    print(f"🤖 AI Enabled: {service.ai_enabled}")
    print(f"🤖 OpenAI Model: {service.openai_model}")
    
    if not service.ai_enabled:
        print("⚠️ AI analysis is disabled. Check OpenAI API key configuration.")
        return None
    
    ai_analysis = service.analyze_pdf_with_ai(pdf_path)
    
    if not ai_analysis:
        print("❌ AI analysis returned no results")
        return None
    
    print_header("Step 3: AI Analysis Results")
    
    # Print framework info
    print(f"Framework Name: {ai_analysis.get('framework_name', 'Unknown')}")
    print(f"Confidence: {ai_analysis.get('confidence', 0):.2f}")
    print(f"Aliases: {', '.join(ai_analysis.get('probable_aliases', []))}")
    print(f"\nSummary: {ai_analysis.get('summary', 'No summary')}")
    
    # Print modified controls
    modified_controls = ai_analysis.get('modified_controls', [])
    print(f"\n{'='*60}")
    print(f"Modified Controls: {len(modified_controls)}")
    print(f"{'='*60}")
    for i, control in enumerate(modified_controls[:5], 1):  # Show first 5
        print(f"\n{i}. {control.get('control_id', 'N/A')}: {control.get('control_name', 'N/A')}")
        print(f"   Type: {control.get('change_type', 'N/A')}")
        print(f"   Description: {control.get('change_description', 'N/A')[:100]}...")
        if control.get('sub_policies'):
            print(f"   Sub-policies: {len(control.get('sub_policies'))}")
    
    if len(modified_controls) > 5:
        print(f"\n... and {len(modified_controls) - 5} more modified controls")
    
    # Print new additions
    new_additions = ai_analysis.get('new_additions', [])
    print(f"\n{'='*60}")
    print(f"New Additions: {len(new_additions)}")
    print(f"{'='*60}")
    for i, addition in enumerate(new_additions[:5], 1):  # Show first 5
        print(f"\n{i}. {addition.get('control_id', 'N/A')}: {addition.get('control_name', 'N/A')}")
        print(f"   Scope: {addition.get('scope', 'N/A')[:100]}...")
        print(f"   Purpose: {addition.get('purpose', 'N/A')[:100]}...")
    
    if len(new_additions) > 5:
        print(f"\n... and {len(new_additions) - 5} more new additions")
    
    # Print framework references
    framework_refs = ai_analysis.get('framework_references', [])
    print(f"\n{'='*60}")
    print(f"Framework References: {len(framework_refs)}")
    print(f"{'='*60}")
    for i, ref in enumerate(framework_refs, 1):
        print(f"\n{i}. {ref.get('referenced_framework', 'N/A')}")
        print(f"   Type: {ref.get('reference_type', 'N/A')}")
        print(f"   Description: {ref.get('description', 'N/A')}")
    
    # Save full analysis to file
    output_file = service.data_dir / f"ai_analysis_{pdf_filename}.json"
    with open(output_file, 'w') as f:
        json.dump(ai_analysis, f, indent=2)
    print(f"\n✅ Full AI analysis saved to: {output_file}")
    
    return ai_analysis


def test_full_processing(pdf_filename):
    """Test full PDF processing including S3 upload and database update"""
    print_header(f"Full Processing Test: {pdf_filename}")
    
    print("⚠️ WARNING: This will process the PDF and update the database!")
    print("Press Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        return None
    
    result = process_specific_file(pdf_filename, "test_ai_system")
    
    print_header("Processing Results")
    print(f"Success: {result.get('success')}")
    print(f"Status: {result.get('status')}")
    
    if result.get('success'):
        print(f"✅ Framework: {result.get('framework_name')} (ID: {result.get('framework_id')})")
        print(f"✅ S3 URL: {result.get('s3_url')}")
        
        if result.get('ai_analysis'):
            ai = result['ai_analysis']
            print(f"\n📊 AI Analysis Stats:")
            print(f"   - Modified controls: {len(ai.get('modified_controls', []))}")
            print(f"   - New additions: {len(ai.get('new_additions', []))}")
            print(f"   - Framework references: {len(ai.get('framework_references', []))}")
        
        if result.get('amendment_info'):
            amend = result['amendment_info']
            print(f"\n📝 Amendment Info:")
            print(f"   - Modified sections: {len(amend.get('modified_sections', []))}")
            print(f"   - Content summary: {amend.get('content_summary', 'N/A')[:100]}...")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    return result


def main():
    """Main test function"""
    print("\n" + "🧪 " + "="*58)
    print("  AI ANALYSIS TEST TOOL")
    print("="*60 + "\n")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python {sys.argv[0]} <pdf_filename> [--full]")
        print("")
        print("Options:")
        print("  --full    Perform full processing (S3 upload + DB update)")
        print("")
        print("Examples:")
        print(f"  python {sys.argv[0]} PCI-DSS-v3-2-1-to-v4-0-Summary-of-Changes-r1.pdf")
        print(f"  python {sys.argv[0]} SP800-53-r5.2.0-changes.pdf --full")
        print("")
        
        # List available PDFs
        service = get_change_management_service()
        pdf_files = list(service.data_dir.glob("*.pdf")) + list(service.data_dir.glob("*.PDF"))
        if pdf_files:
            print("📁 Available PDFs in data directory:")
            for pdf_file in pdf_files:
                print(f"   - {pdf_file.name}")
        else:
            print("⚠️ No PDFs found in data directory")
        
        sys.exit(1)
    
    pdf_filename = sys.argv[1]
    full_processing = "--full" in sys.argv
    
    if full_processing:
        result = test_full_processing(pdf_filename)
    else:
        result = test_ai_analysis_on_pdf(pdf_filename)
    
    if result:
        print_header("✅ Test Completed Successfully")
        sys.exit(0)
    else:
        print_header("❌ Test Failed")
        sys.exit(1)


if __name__ == "__main__":
    main()

