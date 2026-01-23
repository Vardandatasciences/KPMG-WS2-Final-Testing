#!/usr/bin/env python3
"""
AI Analysis Orchestration Script

This script orchestrates the entire process of extracting framework, policies, subpolicies, 
and compliance data from PDF documents.

Process Flow:
1. Extract index/TOC from PDF (pdf_index_extractor.py)
2. Extract content for each section (index_content_extractor.py)
3. Generate policies and subpolicies using AI (policy_extractor_enhanced.py)
4. Generate compliance records for each subpolicy (compliance_generator.py)
5. Combine everything into a hierarchical JSON structure

Usage:
    python ai_analysis.py --pdf-path "data/SP800-53_20251105_112130.pdf"
    
    Or from another script:
    from ai_analysis import process_framework_pdf
    result = process_framework_pdf("data/SP800-53_20251105_112130.pdf")
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd

# Django setup for settings access (must happen BEFORE importing modules that use settings)
import django
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.conf import settings

# Add uploadNist path and import processing modules AFTER Django is configured
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "grc" / "routes" / "uploadNist"))

from pdf_index_extractor import extract_and_save_index
from index_content_extractor import process_pdf_sections
from policy_extractor_enhanced import extract_policies
from compliance_generator import generate_compliance_for_single_subpolicy


OPENAI_API_KEY = "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"
OPENAI_MODEL = "gpt-4o-mini"





class FrameworkProcessor:
    """Main class to orchestrate the framework processing pipeline"""
    
    def __init__(self, pdf_path, base_output_dir="changeManagement/output", verbose=True):
        """
        Initialize the framework processor.
        
        Args:
            pdf_path (str): Path to the PDF file to process
            base_output_dir (str): Base directory for all outputs
            verbose (bool): Whether to print progress messages
        """
        self.pdf_path = Path(pdf_path)
        self.base_output_dir = Path(base_output_dir)
        self.verbose = verbose
        
        # Validate PDF exists
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        
        # Create base output directory
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup output paths
        self.pdf_name = self.pdf_path.stem
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.base_output_dir / f"{self.pdf_name}_{self.timestamp}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Save state
        self.state_file = self.base_output_dir / "state.json"
        self.state = self._load_state()
        
        self._log("=" * 80)
        self._log("Framework PDF Processing Pipeline")
        self._log("=" * 80)
        self._log(f"PDF: {self.pdf_path}")
        self._log(f"Output Directory: {self.run_dir}")
        self._log(f"Timestamp: {self.timestamp}")
        self._log("=" * 80)
    
    def _log(self, message):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(message)
    
    def _load_state(self):
        """Load processing state from state file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self._log(f"Warning: Could not load state file: {e}")
                return {}
        return {}
    
    def _save_state(self):
        """Save current processing state"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self._log(f"Warning: Could not save state file: {e}")
    
    def _update_state(self, step, status, data=None):
        """Update processing state"""
        self.state[step] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        self._save_state()
    
    def step1_extract_index(self):
        """Step 1: Extract index/TOC from PDF"""
        self._log("\n" + "=" * 80)
        self._log("STEP 1: Extracting Index/TOC from PDF")
        self._log("=" * 80)
        
        try:
            index_output_path = self.run_dir / f"{self.pdf_name}_index.json"
            
            self._log(f"Extracting index to: {index_output_path}")
            index_data = extract_and_save_index(
                pdf_path=str(self.pdf_path),
                output_path=str(index_output_path),
                prefer_toc=True
            )
            
            items_count = len(index_data.get('items', []))
            extraction_method = index_data.get('extraction_method', 'unknown')
            
            self._log(f"✓ Index extraction complete!")
            self._log(f"  - Items extracted: {items_count}")
            self._log(f"  - Extraction method: {extraction_method}")
            self._log(f"  - Saved to: {index_output_path}")
            
            self._update_state('step1_extract_index', 'completed', {
                'index_file': str(index_output_path),
                'items_count': items_count,
                'extraction_method': extraction_method
            })
            
            return {
                'success': True,
                'index_file': str(index_output_path),
                'index_data': index_data
            }
            
        except Exception as e:
            self._log(f"✗ Error in Step 1: {e}")
            self._update_state('step1_extract_index', 'failed', {'error': str(e)})
            raise
    
    def step2_extract_sections(self, index_file):
        """Step 2: Extract content for each section based on index"""
        self._log("\n" + "=" * 80)
        self._log("STEP 2: Extracting Section Content")
        self._log("=" * 80)
        
        try:
            sections_output_dir = self.run_dir / "sections"
            
            self._log(f"Extracting sections to: {sections_output_dir}")
            manifest = process_pdf_sections(
                pdf_path=str(self.pdf_path),
                index_json_path=index_file,
                output_dir=str(sections_output_dir),
                verbose=self.verbose
            )
            
            sections_written = len(manifest.get('sections_written', []))
            unresolved = len(manifest.get('unresolved_titles', []))
            
            self._log(f"✓ Section extraction complete!")
            self._log(f"  - Sections extracted: {sections_written}")
            self._log(f"  - Unresolved sections: {unresolved}")
            self._log(f"  - Saved to: {sections_output_dir}")
            
            self._update_state('step2_extract_sections', 'completed', {
                'sections_dir': str(sections_output_dir),
                'sections_count': sections_written,
                'unresolved_count': unresolved
            })
            
            return {
                'success': True,
                'sections_dir': str(sections_output_dir),
                'manifest': manifest
            }
            
        except Exception as e:
            self._log(f"✗ Error in Step 2: {e}")
            self._update_state('step2_extract_sections', 'failed', {'error': str(e)})
            raise
    
    def step3_extract_policies(self, sections_dir):
        """Step 3: Generate policies and subpolicies using AI"""
        self._log("\n" + "=" * 80)
        self._log("STEP 3: Extracting Policies and Subpolicies using AI")
        self._log("=" * 80)
        
        try:
            policies_output_dir = self.run_dir / "policies"
            
            self._log(f"Extracting policies to: {policies_output_dir}")
            self._log("Note: This step uses OpenAI API and may take a while...")
            
            result = extract_policies(
                sections_dir=sections_dir,
                output_dir=str(policies_output_dir),
                api_key=None,  # Will use Django settings
                verbose=self.verbose
            )
            
            if result['success']:
                summary = result['summary']['extraction_summary']
                policies_count = summary['total_policies']
                subpolicies_count = summary['total_subpolicies']
                
                self._log(f"✓ Policy extraction complete!")
                self._log(f"  - Policies extracted: {policies_count}")
                self._log(f"  - Subpolicies extracted: {subpolicies_count}")
                self._log(f"  - API calls made: {summary['api_calls_made']}")
                self._log(f"  - Saved to: {policies_output_dir}")
                
                self._update_state('step3_extract_policies', 'completed', {
                    'policies_dir': str(policies_output_dir),
                    'policies_count': policies_count,
                    'subpolicies_count': subpolicies_count
                })
                
                return {
                    'success': True,
                    'policies_dir': str(policies_output_dir),
                    'result': result
                }
            else:
                raise Exception(result.get('error', 'Policy extraction failed'))
                
        except Exception as e:
            self._log(f"✗ Error in Step 3: {e}")
            self._update_state('step3_extract_policies', 'failed', {'error': str(e)})
            raise
    
    def step4_generate_compliance(self, policies_data):
        """Step 4: Generate compliance records for each subpolicy"""
        self._log("\n" + "=" * 80)
        self._log("STEP 4: Generating Compliance Records")
        self._log("=" * 80)
        
        try:
            compliance_output_dir = self.run_dir / "compliance"
            compliance_output_dir.mkdir(parents=True, exist_ok=True)
            
            all_compliances = []
            total_subpolicies = 0
            processed_subpolicies = 0
            
            # Load policies from the all_policies.json file
            all_policies_file = Path(policies_data['policies_dir']) / "all_policies.json"
            with open(all_policies_file, 'r', encoding='utf-8') as f:
                policies_list = json.load(f)
            
            # Count total subpolicies
            for section_item in policies_list:
                for policy in section_item['analysis']['policies']:
                    total_subpolicies += len(policy.get('subpolicies', []))
            
            self._log(f"Total subpolicies to process: {total_subpolicies}")
            self._log("Note: This step uses OpenAI API and may take a while...")
            
            # Process each policy and subpolicy
            for section_idx, section_item in enumerate(policies_list):
                section_info = section_item['section_info']
                section_title = section_info['title']
                
                self._log(f"\n[Section {section_idx + 1}/{len(policies_list)}] {section_title}")
                
                for policy in section_item['analysis']['policies']:
                    policy_id = policy['policy_id']
                    policy_title = policy['policy_title']
                    
                    self._log(f"  [Policy] {policy_title} ({policy_id})")
                    
                    for subpolicy in policy.get('subpolicies', []):
                        subpolicy_id = subpolicy['subpolicy_id']
                        subpolicy_title = subpolicy['subpolicy_title']
                        subpolicy_description = subpolicy['subpolicy_description']
                        control = subpolicy.get('control', '')
                        
                        self._log(f"    [Subpolicy {processed_subpolicies + 1}/{total_subpolicies}] {subpolicy_title}")
                        
                        try:
                            # Generate compliance for this subpolicy
                            compliance_records = generate_compliance_for_single_subpolicy(
                                subpolicy_id=subpolicy_id,
                                subpolicy_name=subpolicy_title,
                                description=subpolicy_description,
                                control=control
                            )
                            
                            if compliance_records:
                                # Add context information to each compliance record
                                for comp_record in compliance_records:
                                    comp_record['section_info'] = section_info
                                    comp_record['policy_info'] = {
                                        'policy_id': policy_id,
                                        'policy_title': policy_title,
                                        'policy_type': policy.get('policy_type'),
                                        'policy_category': policy.get('policy_category'),
                                        'policy_subcategory': policy.get('policy_subcategory')
                                    }
                                    comp_record['subpolicy_info'] = {
                                        'subpolicy_id': subpolicy_id,
                                        'subpolicy_title': subpolicy_title,
                                        'subpolicy_description': subpolicy_description,
                                        'control': control
                                    }
                                
                                all_compliances.extend(compliance_records)
                                self._log(f"      ✓ Generated {len(compliance_records)} compliance record(s)")
                            else:
                                self._log(f"      ⚠ No compliance records generated")
                            
                        except Exception as e:
                            self._log(f"      ✗ Error generating compliance: {e}")
                        
                        processed_subpolicies += 1
                        
                        # Small delay to avoid rate limiting
                        import time
                        time.sleep(0.5)
            
            # Save all compliance records
            compliance_file = compliance_output_dir / "all_compliances.json"
            with open(compliance_file, 'w', encoding='utf-8') as f:
                json.dump(all_compliances, f, ensure_ascii=False, indent=2)
            
            self._log(f"\n✓ Compliance generation complete!")
            self._log(f"  - Total compliance records: {len(all_compliances)}")
            self._log(f"  - Saved to: {compliance_file}")
            
            self._update_state('step4_generate_compliance', 'completed', {
                'compliance_dir': str(compliance_output_dir),
                'compliance_count': len(all_compliances)
            })
            
            return {
                'success': True,
                'compliance_dir': str(compliance_output_dir),
                'all_compliances': all_compliances
            }
            
        except Exception as e:
            self._log(f"✗ Error in Step 4: {e}")
            self._update_state('step4_generate_compliance', 'failed', {'error': str(e)})
            raise
    
    def step5_generate_hierarchical_json(self, policies_data, compliance_data):
        """Step 5: Combine everything into a hierarchical JSON structure"""
        self._log("\n" + "=" * 80)
        self._log("STEP 5: Generating Hierarchical JSON Output")
        self._log("=" * 80)
        
        try:
            # Load policies
            all_policies_file = Path(policies_data['policies_dir']) / "all_policies.json"
            with open(all_policies_file, 'r', encoding='utf-8') as f:
                policies_list = json.load(f)
            
            # Load framework metadata from summary
            summary_file = Path(policies_data['policies_dir']) / "extraction_summary.json"
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            
            framework_metadata = summary_data.get('framework_metadata', {})
            
            # Get all compliances
            all_compliances = compliance_data['all_compliances']
            
            # Build hierarchical structure
            hierarchical_output = {
                "metadata": {
                    "source_pdf": str(self.pdf_path.resolve()),
                    "processing_timestamp": self.timestamp,
                    "processing_date": datetime.now().isoformat(),
                    "total_sections": len(policies_list),
                    "total_policies": sum(len(item['analysis']['policies']) for item in policies_list),
                    "total_subpolicies": sum(
                        sum(len(policy['subpolicies']) for policy in item['analysis']['policies'])
                        for item in policies_list
                    ),
                    "total_compliances": len(all_compliances)
                },
                "framework": framework_metadata,
                "sections": []
            }
            
            # Build hierarchy
            for section_item in policies_list:
                section_info = section_item['section_info']
                
                section_node = {
                    "section_title": section_info['title'],
                    "section_level": section_info.get('level'),
                    "section_pages": {
                        "start": section_info.get('start_page'),
                        "end": section_info.get('end_page')
                    },
                    "policies": []
                }
                
                for policy in section_item['analysis']['policies']:
                    policy_node = {
                        "policy_id": policy['policy_id'],
                        "policy_title": policy['policy_title'],
                        "policy_description": policy['policy_description'],
                        "policy_text": policy['policy_text'],
                        "scope": policy['scope'],
                        "objective": policy['objective'],
                        "policy_type": policy['policy_type'],
                        "policy_category": policy['policy_category'],
                        "policy_subcategory": policy['policy_subcategory'],
                        "subpolicies": []
                    }
                    
                    for subpolicy in policy.get('subpolicies', []):
                        subpolicy_id = subpolicy['subpolicy_id']
                        
                        # Find all compliance records for this subpolicy
                        subpolicy_compliances = [
                            comp for comp in all_compliances
                            if comp.get('SubPolicyId') == subpolicy_id
                        ]
                        
                        subpolicy_node = {
                            "subpolicy_id": subpolicy_id,
                            "subpolicy_title": subpolicy['subpolicy_title'],
                            "subpolicy_description": subpolicy['subpolicy_description'],
                            "subpolicy_text": subpolicy.get('subpolicy_text', ''),
                            "control": subpolicy.get('control', ''),
                            "compliances": subpolicy_compliances
                        }
                        
                        policy_node['subpolicies'].append(subpolicy_node)
                    
                    section_node['policies'].append(policy_node)
                
                hierarchical_output['sections'].append(section_node)
            
            # Save hierarchical JSON
            output_file = self.run_dir / f"{self.pdf_name}_complete_hierarchy.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(hierarchical_output, f, ensure_ascii=False, indent=2)
            
            self._log(f"✓ Hierarchical JSON generated!")
            self._log(f"  - Saved to: {output_file}")
            self._log(f"\nHierarchy Summary:")
            self._log(f"  - Sections: {hierarchical_output['metadata']['total_sections']}")
            self._log(f"  - Policies: {hierarchical_output['metadata']['total_policies']}")
            self._log(f"  - Subpolicies: {hierarchical_output['metadata']['total_subpolicies']}")
            self._log(f"  - Compliances: {hierarchical_output['metadata']['total_compliances']}")
            
            self._update_state('step5_generate_hierarchical_json', 'completed', {
                'output_file': str(output_file)
            })
            
            return {
                'success': True,
                'output_file': str(output_file),
                'hierarchical_output': hierarchical_output
            }
            
        except Exception as e:
            self._log(f"✗ Error in Step 5: {e}")
            self._update_state('step5_generate_hierarchical_json', 'failed', {'error': str(e)})
            raise
    
    def process(self):
        """Run the complete processing pipeline"""
        try:
            start_time = datetime.now()
            
            # Step 1: Extract Index
            step1_result = self.step1_extract_index()
            
            # Step 2: Extract Sections
            step2_result = self.step2_extract_sections(step1_result['index_file'])
            
            # Step 3: Extract Policies
            step3_result = self.step3_extract_policies(step2_result['sections_dir'])
            
            # Step 4: Generate Compliance
            step4_result = self.step4_generate_compliance(step3_result)
            
            # Step 5: Generate Hierarchical JSON
            step5_result = self.step5_generate_hierarchical_json(step3_result, step4_result)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            self._log("\n" + "=" * 80)
            self._log("PROCESSING COMPLETE!")
            self._log("=" * 80)
            self._log(f"Total processing time: {duration}")
            self._log(f"Final output: {step5_result['output_file']}")
            self._log("=" * 80)
            
            return {
                'success': True,
                'output_file': step5_result['output_file'],
                'run_dir': str(self.run_dir),
                'duration': str(duration),
                'results': {
                    'step1': step1_result,
                    'step2': step2_result,
                    'step3': step3_result,
                    'step4': step4_result,
                    'step5': step5_result
                }
            }
            
        except Exception as e:
            self._log(f"\n✗ Processing failed: {e}")
            import traceback
            self._log(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }


def process_framework_pdf(pdf_path, output_dir="changeManagement/output", verbose=True):
    """
    Convenience function to process a framework PDF through the entire pipeline.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_dir (str): Base output directory
        verbose (bool): Whether to print progress messages
    
    Returns:
        dict: Processing results with success status and output file path
    
    Example:
        >>> result = process_framework_pdf("data/SP800-53.pdf")
        >>> if result['success']:
        ...     print(f"Output saved to: {result['output_file']}")
    """
    processor = FrameworkProcessor(pdf_path, output_dir, verbose)
    return processor.process()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI Analysis Pipeline - Process Framework PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Process a PDF from the data folder:
    python ai_analysis.py --pdf-path data/SP800-53_20251105_112130.pdf
  
  Process with custom output directory:
    python ai_analysis.py --pdf-path data/framework.pdf --output-dir custom_output
  
  Process in quiet mode:
    python ai_analysis.py --pdf-path data/framework.pdf --quiet
        """
    )
    
    parser.add_argument(
        '--pdf-path',
        required=True,
        help='Path to the PDF file to process'
    )
    parser.add_argument(
        '--output-dir',
        default='changeManagement/output',
        help='Base output directory (default: changeManagement/output)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress messages'
    )
    
    args = parser.parse_args()
    
    result = process_framework_pdf(
        pdf_path=args.pdf_path,
        output_dir=args.output_dir,
        verbose=not args.quiet
    )
    
    if result['success']:
        print(f"\n✓ Success! Output saved to: {result['output_file']}")
        return 0
    else:
        print(f"\n✗ Failed: {result.get('error', 'Unknown error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

