#!/usr/bin/env python3
"""
Example Usage Scripts for AI Analysis Pipeline

This file demonstrates various ways to use the AI analysis pipeline
for processing framework PDFs.
"""

import sys,os
from pathlib import Path
from ai_analysis import process_framework_pdf, FrameworkProcessor

# GROK configuration (user-provided)
# Set these in your environment or .env before running examples
GROK_API_KEY =  "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"
GROK_MODEL = os.getenv("GROK_MODEL", "llama-3.1-8b-instant")
def example1_simple_processing():
    """
    Example 1: Simple one-line processing
    Most straightforward way to process a PDF.
    """
    print("=" * 80)
    print("Example 1: Simple Processing")
    print("=" * 80)
    
    pdf_path = "data/PCI_DSS_1.pdf"
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found at {pdf_path}")
        print("Please place your PDF in the data/ folder")
        return
    
    # Process the PDF
    result = process_framework_pdf(pdf_path)
    
    if result['success']:
        print(f"\n✓ Success!")
        print(f"Output file: {result['output_file']}")
        print(f"Processing time: {result['duration']}")
    else:
        print(f"\n✗ Failed: {result.get('error')}")


def example2_custom_output_directory():
    """
    Example 2: Processing with custom output directory
    Useful when you want to organize outputs differently.
    """
    print("\n" + "=" * 80)
    print("Example 2: Custom Output Directory")
    print("=" * 80)
    
    pdf_path = "data/SP800-53_20251105_112130.pdf"
    output_dir = "my_custom_output"
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    result = process_framework_pdf(
        pdf_path=pdf_path,
        output_dir=output_dir,
        verbose=True
    )
    
    if result['success']:
        print(f"\n✓ Output saved to: {result['run_dir']}")


def example3_step_by_step_processing():
    """
    Example 3: Step-by-step processing with manual control
    Useful when you need to inspect or modify intermediate results.
    """
    print("\n" + "=" * 80)
    print("Example 3: Step-by-Step Processing")
    print("=" * 80)
    
    pdf_path = "data/SP800-53_20251105_112130.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    # Initialize processor
    processor = FrameworkProcessor(
        pdf_path=pdf_path,
        base_output_dir="changeManagement/output",
        verbose=True
    )
    
    try:
        # Step 1: Extract index
        print("\nRunning Step 1: Index Extraction...")
        step1_result = processor.step1_extract_index()
        print(f"Index file: {step1_result['index_file']}")
        print(f"Items found: {len(step1_result['index_data']['items'])}")
        
        # You can inspect or modify the index here if needed
        
        # Step 2: Extract sections
        print("\nRunning Step 2: Section Extraction...")
        step2_result = processor.step2_extract_sections(step1_result['index_file'])
        print(f"Sections extracted: {len(step2_result['manifest']['sections_written'])}")
        
        # You can inspect sections here
        
        # Step 3: Extract policies
        print("\nRunning Step 3: Policy Extraction...")
        step3_result = processor.step3_extract_policies(step2_result['sections_dir'])
        
        if step3_result['success']:
            summary = step3_result['result']['summary']['extraction_summary']
            print(f"Policies: {summary['total_policies']}")
            print(f"Subpolicies: {summary['total_subpolicies']}")
        
        # Step 4: Generate compliance
        print("\nRunning Step 4: Compliance Generation...")
        step4_result = processor.step4_generate_compliance(step3_result)
        print(f"Compliance records: {len(step4_result['all_compliances'])}")
        
        # Step 5: Generate hierarchical output
        print("\nRunning Step 5: Hierarchical JSON...")
        step5_result = processor.step5_generate_hierarchical_json(
            step3_result,
            step4_result
        )
        
        print(f"\n✓ Complete! Final output: {step5_result['output_file']}")
        
    except Exception as e:
        print(f"\n✗ Error during processing: {e}")
        import traceback
        traceback.print_exc()


def example4_batch_processing():
    """
    Example 4: Batch processing multiple PDFs
    Useful when you have multiple framework documents to process.
    """
    print("\n" + "=" * 80)
    print("Example 4: Batch Processing")
    print("=" * 80)
    
    # List of PDFs to process
    pdf_files = [
        "data/SP800-53_20251105_112130.pdf",
        # Add more PDFs here
        # "data/another_framework.pdf",
        # "data/yet_another.pdf",
    ]
    
    results = []
    
    for pdf_path in pdf_files:
        if not Path(pdf_path).exists():
            print(f"\n⚠ Skipping {pdf_path} (not found)")
            continue
        
        print(f"\n{'=' * 80}")
        print(f"Processing: {pdf_path}")
        print(f"{'=' * 80}")
        
        result = process_framework_pdf(pdf_path, verbose=True)
        results.append({
            'pdf': pdf_path,
            'result': result
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("Batch Processing Summary")
    print("=" * 80)
    
    successful = sum(1 for r in results if r['result']['success'])
    failed = len(results) - successful
    
    print(f"Total processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nFailed files:")
        for r in results:
            if not r['result']['success']:
                print(f"  - {r['pdf']}: {r['result'].get('error')}")


def example5_accessing_results():
    """
    Example 5: Accessing and using the results
    Shows how to read and use the generated JSON files.
    """
    print("\n" + "=" * 80)
    print("Example 5: Accessing Results")
    print("=" * 80)
    
    pdf_path = "data/SP800-53_20251105_112130.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    result = process_framework_pdf(pdf_path, verbose=False)
    
    if not result['success']:
        print(f"Processing failed: {result.get('error')}")
        return
    
    # Load the final hierarchical JSON
    import json
    output_file = result['output_file']
    
    with open(output_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Access framework information
    framework = data['framework']
    print(f"\nFramework: {framework['framework_name']}")
    print(f"Version: {framework['current_version']}")
    print(f"Category: {framework['category']}")
    
    # Access statistics
    metadata = data['metadata']
    print(f"\nStatistics:")
    print(f"  Sections: {metadata['total_sections']}")
    print(f"  Policies: {metadata['total_policies']}")
    print(f"  Subpolicies: {metadata['total_subpolicies']}")
    print(f"  Compliances: {metadata['total_compliances']}")
    
    # Access sections
    sections = data['sections']
    print(f"\nFirst 3 sections:")
    for i, section in enumerate(sections[:3], 1):
        print(f"  {i}. {section['section_title']}")
        print(f"     Policies: {len(section['policies'])}")
    
    # Access a specific policy
    if sections and sections[0]['policies']:
        first_policy = sections[0]['policies'][0]
        print(f"\nExample Policy:")
        print(f"  ID: {first_policy['policy_id']}")
        print(f"  Title: {first_policy['policy_title']}")
        print(f"  Type: {first_policy['policy_type']}")
        print(f"  Subpolicies: {len(first_policy['subpolicies'])}")
        
        # Access subpolicy and compliance
        if first_policy['subpolicies']:
            first_subpolicy = first_policy['subpolicies'][0]
            print(f"\n  Example Subpolicy:")
            print(f"    ID: {first_subpolicy['subpolicy_id']}")
            print(f"    Title: {first_subpolicy['subpolicy_title']}")
            print(f"    Compliances: {len(first_subpolicy['compliances'])}")
            
            if first_subpolicy['compliances']:
                first_compliance = first_subpolicy['compliances'][0]
                print(f"\n    Example Compliance:")
                print(f"      Identifier: {first_compliance['Identifier']}")
                print(f"      Title: {first_compliance['ComplianceTitle']}")
                print(f"      Type: {first_compliance['ComplianceType']}")
                print(f"      Criticality: {first_compliance['Criticality']}")


def example6_quiet_mode():
    """
    Example 6: Processing in quiet mode
    Useful for automated scripts or background processing.
    """
    print("\n" + "=" * 80)
    print("Example 6: Quiet Mode Processing")
    print("=" * 80)
    
    pdf_path = "data/SP800-53_20251105_112130.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    print("Processing (this may take a while)...")
    
    result = process_framework_pdf(
        pdf_path=pdf_path,
        verbose=False  # Suppress all progress messages
    )
    
    if result['success']:
        print(f"✓ Done! Output: {result['output_file']}")
    else:
        print(f"✗ Failed: {result.get('error')}")


def main():
    """Run selected example"""
    print("AI Analysis Pipeline - Example Usage")
    print("=" * 80)
    print("\nAvailable examples:")
    print("1. Simple processing")
    print("2. Custom output directory")
    print("3. Step-by-step processing")
    print("4. Batch processing")
    print("5. Accessing results")
    print("6. Quiet mode")
    print("0. Run all examples")
    
    choice = input("\nSelect example (0-6): ").strip()
    
    examples = {
        '1': example1_simple_processing,
        '2': example2_custom_output_directory,
        '3': example3_step_by_step_processing,
        '4': example4_batch_processing,
        '5': example5_accessing_results,
        '6': example6_quiet_mode,
    }
    
    if choice == '0':
        for example in examples.values():
            example()
    elif choice in examples:
        examples[choice]()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()

